# -*- coding: utf8 -*-

import collections

from twisted.cred import error
from twisted.cred.credentials import IUsernamePassword
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.portal import IRealm
from twisted.internet import defer
from twisted.web.resource import IResource
from zope.interface import implements

from rss_monkey.common.db import NoResultError


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

    @defer.inlineCallbacks
    def checkCredentials(self, credentials):

        user = yield self.db.get_user(credentials.username)

        try:
            uid, passwd = user['id'], user['passwd']

            if passwd.lower() != credentials.password.lower():
                raise error.UnauthorizedLogin('Password mismatch')

            defer.returnValue(uid)

        except NoResultError:
            raise error.UnauthorizedLogin('Username unknown')
