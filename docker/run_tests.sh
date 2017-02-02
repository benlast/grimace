#!/usr/bin/env bash
cd /grimace
. /venv/bin/activate
pip install -r test-requirements.txt
nosetests grimace
