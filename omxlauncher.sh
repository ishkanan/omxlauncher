#!/bin/bash

# die apt die!
systemctl stop apt-daily.timer
systemctl disable apt-daily.timer
systemctl stop apt-daily.service
systemctl disable apt-daily.service
systemctl kill --kill-who=all apt-daily.service
while ! (systemctl list-units --all apt-daily.service | fgrep -q dead)
do
  sleep 1;
done

# go go
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

