# README #

Launcher script and monitor for omxplayer. Auto-restarts omxplayer if it ever shuts down due to a disconnect or reboot.

## Setup ##

* Checkout the repository with `mkdir -p /home/pi/omxlauncher/repo && git clone https://github.com/ishkanan/omxlauncher /home/pi/omxlauncher/repo`.
* Decide which WOWZA stream the Pi is going to play and get its URL.
* Add launcher script to system startup by adding `/home/pi/omxlauncher/repo/omxlauncher.sh "<URL>"` to `/etc/rc.local`.
* Reboot the Pi

## Who do I talk to? ##

Anthony Ishkan (anthony.ishkan@gmail.com)
