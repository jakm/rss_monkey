# -*- coding: utf8 -*-

from zope.interface import Interface


class IService(Interface):
    """
    Base interface of services.
    """


class ILoginService(IService):
    """
    Interface of login service.
    """

    def login(self, login, passwd):
        """
        Login user with passed login name and password hash.

        @param login str, Login name
        @param passwd str, SHA256 hash of password
        @return string, Session token
        """


class IRegistrationService(IService):
    """
    Interface of registration service.
    """

    def register_user(self, login, passwd):
        """
        Register user with passed login name and password hash.

        @param login str, Login name
        @param passwd str, SHA256 hash of password
        TODO: @throw ...
        """


class IRssService(IService):
    """
    Interface of essential service to control user's channels and entries.
    """

    def get_channels(self, user_id):
        """
        Retrieve channels registered by user. Records are in format:
        {'id': int, 'title': str, 'url': str}

        @param user_id int, User ID
        @return tuple, Tuple of records
        """

    def reorder_channels(self, user_id, new_order):
        """
        Change ordering of user's channels.

        @param user_id int, User ID
        @param new_order sequence, Sequence of ordered channel IDs
        """

    def add_channel(self, user_id, url):
        """
        Bind user with channel. If channel doesn't exist create new record.

        @param user_id int, User ID
        @param url str, URL of channel
        """

    def remove_channel(self, user_id, channel_id):
        """
        Unbind user with channel. If channel is not bound with any user remove it.

        @param user_id int, User ID
        @param channel_id int, Channel ID
        """

    def has_unread_entries(self, user_id, channel_id):
        """
        True if channel has unread entries or False.

        @param user_id int, User ID
        @param channel_id int, Channel ID
        @return bool
        """

    def get_entries(self, user_id, channel_id, limit=None, offset=None):
        """
        Return entries with any read status. Records are in format:
        {'id', int, 'title': str, 'summary': str, 'link': str, 'date':
         datetime.datetime, 'read': bool}

        @param user_id int, User ID
        @param channel_id int, Channel ID
        @param limit int, Maximal number of returned records or None for unlimited
        @param offset int, Number of records to skip
        @return tuple, Tuple of records
        """

    def set_entry_read(self, user_id, entry_id, read):
        """
        Set read status of entry.

        @param user_id int, User ID
        @param entry_id int, Entry ID
        @param read bool, Read status of entry
        """
