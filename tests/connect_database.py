#!/usr/bin/bpython -i
# -*- coding: utf8 -*-
'''
Allows connect database as used in rss_monkey.

Prepares sys.path to import rss_monkey module.
Imports frequently used classes - User, Feed, FeedEntry.
'''

import sys
import os.path

def get_project_root():
    executable = sys.argv[0]
    test_dir = os.path.split(executable)[0]
    project_root = os.path.join(test_dir, '..')
    return os.path.realpath(project_root)

def prepare_import():
    src_dir = os.path.join(get_project_root(), 'src')
    sys.path.insert(0, src_dir)

prepare_import()
del get_project_root
del prepare_import

from rss_monkey.common.context import install_context, AppContext
from rss_monkey.server.config import AppConfig
install_context(AppConfig())
db = AppContext.get_object('db')
from rss_monkey.common.model import User, Feed, FeedEntry
