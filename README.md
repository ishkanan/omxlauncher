# README #

Launcher and monitor script for omxplayer and VLC. Auto-restarts the player if it shuts down due to a disconnect or reboot.

## Setup ##

* Checkout this repository with:

```bash
dest=/home/pi/streamwatcher/repo
rm -Rf $dest && mkdir -p $dest
git clone https://github.com/ishkanan/streamwatcher $dest
```

* Determine which WOWZA/media stream(s) the player is going to connect to

* Run the desired Ansible playbook to add the launcher script to system startup

* Enjoy the view after the Pi has rebooted

## Who do I talk to? ##

Anthony Ishkan (anthony.ishkan@gmail.com)
