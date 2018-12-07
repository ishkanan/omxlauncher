#!/bin/bash

cd /home/pi/omxlauncher
apt-get install -y python3-venv
python3 -m venv .
source bin/activate
pip install --upgrade pip
cd /home/pi/omxlauncher/repo
pip install -r requirements.txt
python omxlauncher.py "/home/pi/omxlauncher/omxlauncher.log" "$1"
deactivate
cd /home/pi/omxlauncher
