#!/bin/bash

workdir=$(dirname $(which $0))
cd $workdir

export PYTHONPATH="`pwd`/src"

twistd -n -y src/RssMonkeyServer.tac
