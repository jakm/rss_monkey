#!/usr/bin/env python
# -*- coding: utf8 -*-

from optparse import OptionParser

from rss_monkey.common import app_context
from rss_monkey.common.model import Base


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

    app_context.install_default()

    engine = app_context.AppContext.get_object('db_engine')

    Base.metadata.create_all(bind=engine, checkfirst=(not options.force))

if __name__ == '__main__':
    main()
