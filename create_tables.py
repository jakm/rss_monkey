#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
import os.path
from optparse import OptionParser


def main():
    parser = OptionParser()
    parser.add_option('-f', '--force', dest='force',
        action='store_true', default=False,
        help='Force CREATE TABLE execution - removes existing data!!!')
    parser.add_option('-y', '--answer-yes', dest='answer_yes',
        action='store_true', default=False,
        help='Answer YES to confirm execute.')

    (options, args) = parser.parse_args()

    if args:
        parser.print_usage()
        exit(1)

    if not options.answer_yes:
        print 'Continue with creation of tables? [yes/NO]:'
        answer = raw_input()
        if answer != 'yes':
            exit()

    prepare_import()
    engine = connect()
    create_tables(engine, options.force)


def prepare_import():
    src_dir = os.path.join(get_project_root(), 'src')
    sys.path.insert(0, src_dir)


def connect():
    from rss_monkey.common import app_context
    app_context.install_context(app_context.AppConfig())
    return app_context.AppContext.get_object('db_engine')


def create_tables(engine, force=False):
    from rss_monkey.common.model import Base

    if force:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)


def get_project_root():
    executable = sys.argv[0]
    directory = os.path.split(executable)[0]
    project_root = os.path.realpath(directory)
    return project_root

if __name__ == '__main__':
    main()
