# README #

Launcher and monitor script for omxplayer and VLC. Auto-restarts the player if it shuts down due to a disconnect or reboot.

## Setup ##

* Checkout this repository with:

```bash
dest=/home/pi/streamwatcher/repo
rm -Rf $dest && mkdir -p $dest
git clone https://github.com/ishkanan/streamwatcher $dest
```

* Determine the URL of the WOWZA/media stream the player is going to connect to

* Add the launcher script to system startup by running the correct Ansible playbook

* Reboot the Pi

## Who do I talk to? ##

Anthony Ishkan (anthony.ishkan@gmail.com)
