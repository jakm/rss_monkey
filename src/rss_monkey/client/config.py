#! -*- coding: utf8 -*-

import os.path
from ConfigParser import RawConfigParser
from rss_monkey.common.utils import singleton

CONFIG_FILE = '/etc/rss_monkey_client.ini'


@singleton
class Config(object):
    def __init__(self):
        self.parser = RawConfigParser()
        self.parser.read(CONFIG_FILE)

    def get(self, section, option):
        return self.parser.get(section, option)


@singleton
class UserConfig(object):
    def __init__(self):
        self.path = os.path.expanduser('~/.rss_monkey.ini')
        self.parser = RawConfigParser()
        self.parser.read(self.path)

    def get(self, section, option):
        return self.parser.get(section, option)

    def set(self, section, option, value=None):
        if not self.parser.has_section(section):
            self.parser.add_section(section)

        self.parser.set(section, option, value)

    def write(self):
        with open(self.path, 'w') as f:
            self.parser.write(f)
