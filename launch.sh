#!/bin/bash

if [ ! -f bin/activate ]; then
  # slight speed up
  python3 -m venv .
fi

source bin/activate
cd repo
pip install -r requirements.txt

# launch
python streamwatcher.py $@
deactivate
cd ..
