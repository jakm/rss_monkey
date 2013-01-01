# -*- coding: utf8 -*-

import collections

from sqlalchemy.orm.exc import NoResultFound
from twisted.cred import error
from twisted.cred.credentials import IUsernamePassword
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.portal import IRealm
from twisted.web.resource import IResource
from zope.interface import implements

from rss_monkey.common.model import User
from rss_monkey.common.utils import defer_to_thread


class PrivateServiceRealm(object):
    implements(IRealm)

    def __init__(self, resource_factory):
        if not isinstance(resource_factory, collections.Callable):
            raise ValueError('Factory must be a callable.')

        self.factory = resource_factory

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, self.factory(avatarId), lambda: None)

        raise NotImplementedError()


class DbCredentialsChecker(object):
    implements(ICredentialsChecker)

    credentialInterfaces = (IUsernamePassword,)

    def __init__(self, db):
        self.db = db

    def requestAvatarId(self, credentials):
        for interface in self.credentialInterfaces:
            if interface.providedBy(credentials):
                break
        else:
            raise error.UnhandledCredentials()

        return self.checkCredentials(credentials)

    @defer_to_thread
    def checkCredentials(self, credentials):
        query = self.db.query(User.id, User.passwd).filter(User.login == credentials.username)

        try:
            uid, passwd = query.one()

            if passwd.lower() != credentials.password.lower():
                raise error.UnauthorizedLogin('Password mismatch')

            return uid

        except NoResultFound:
            raise error.UnauthorizedLogin('Username unknown')
