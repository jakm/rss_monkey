# -*- coding: utf8 -*-

from zope.interface import Interface


class IService(Interface):
    """
    Base interface of services.
    """


class ITestService(IService):
    """
    Interface of test service.
    """

    def test(self):
        """
        Return 'OK' when server is alive.
        @return string
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

    def get_channels(self):
        """
        Retrieve channels registered by user. Records are in format:
        {'id': int, 'title': str, 'url': str}

        @return tuple, Tuple of records
        """

    def reorder_channels(self, new_order):
        """
        Change ordering of user's channels.

        @param new_order sequence, Sequence of ordered channel IDs
        """

    def add_channel(self, url):
        """
        Bind user with channel. If channel doesn't exist create new record.

        @param url str, URL of channel
        @return int, Channel ID
        """

    def reload_channel(self, channel_id):
        """
        Instruct 'feed processor' to reload data of channel.

        @param channel_id int, Channel ID
        """

    def remove_channel(self, channel_id):
        """
        Unbind user with channel. If channel is not bound with any user remove it.

        @param channel_id int, Channel ID
        """

    def has_unread_entries(self, channel_id):
        """
        True if channel has unread entries or False.

        @param channel_id int, Channel ID
        @return bool
        """

    def get_entries(self, channel_id, limit=None, offset=None):
        """
        Return entries with any read status. Records are in format:
        {'id', int, 'title': str, 'summary': str, 'link': str, 'date':
         datetime.datetime, 'read': bool}

        @param channel_id int, Channel ID
        @param limit int, Maximal number of returned records or None for unlimited
        @param offset int, Number of records to skip
        @return tuple, Tuple of records
        """

    def set_entry_read(self, entry_id, read):
        """
        Set read status of entry.

        @param entry_id int, Entry ID
        @param read bool, Read status of entry
        """
