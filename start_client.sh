#!/bin/bash

workdir=$(dirname $(which $0))
cd $workdir

export PYTHONPATH="${workdir}/src:${workdir}/lib"

src/RssMonkeyClient
