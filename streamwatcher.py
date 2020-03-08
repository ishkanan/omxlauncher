#!/usr/bin/env python

import logging
import os
import pexpect
import re
import signal
import subprocess
import sys
from threading import Thread
import time

from bottle import route, run

PLAYER_CMDS = {
    "omx": "omxplayer -b -o hdmi --avdict rtsp_transport:tcp --live --threshold 0.2 {url}",
    "vlc": "vlc {url}",
}

OMX_STATUS_CMD = [
    "./dbus-omx.sh",
    "status",
]

last_omx_duration = 0
logger = None
player_proc = None
status = {
    "mode": "single",
    "status": "booting",
    "stream": "",
}

##########################

def intTryParse(value):
    try:
        return int(value), True
    except ValueError:
        return value, False

def set_status(stage, stream):
    """Quick helper function to set the global status for the web server.
    """
    global status
    status.update({
        "status": stage,
        "stream": stream,
    })

def signal_handler(signum, frame):
    """Handles a SIGHUP or SIGKILL from the OS.
    """
    if player_proc == None:
        logger.debug("SIGHANDLER: Player is not running, nothing to do.")
    else:
        logger.debug("SIGHANDLER: Player is running, will force close it.")
        player_proc.close(force=True)
    logger.info("Gracefully stopped. Bye.")
    sys.exit(0)

def make_logger(name):
    """Creates a logger with specified name that writes to console and
    specified output file.
    """
    l = logging.getLogger(name)
    l.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s  - %(levelname)s - %(message)s')
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    l.addHandler(ch)
    return l

def do_check_omx_healthy():
    """Checks if omxplayer is playing the stream by querying it over its DBus
    link. If OMX reports a good duration, then we assume it's healthy, otherwise
    we assume something is wrong.
    """
    global last_omx_duration
    ret = subprocess.run(OMX_STATUS_CMD, capture_output=True, encoding="utf8")
    if ret.returncode != 0:
        return False
    ret = re.search("Duration: (\\d+)", ret.stdout)
    if len(ret.groups()) < 1:
        return False
    dur, ok = intTryParse(ret.groups()[0])
    if not ok or dur <= last_omx_duration:
        return False
    last_omx_duration = dur
    return True

def do_single_stream(player, stream):
    """Runs a best-effort loop to keep the player always watching a single stream.
    """
    global last_omx_duration
    global player_proc
    cmd = PLAYER_CMDS[player].format(url=stream)

    logger.debug("Starting single stream infinity loop...")
    while True:
        healthy = False
        last_omx_duration = 0

        # try to launch omxplayer
        logger.info("Launching {} player...".format(player.upper()))
        set_status("launching", stream)
        try:
            player_proc = pexpect.spawn(cmd)
        except Exception as ex:
            logger.warning("Launch error, will retry in 10 secs - {}".format(ex))
            set_status("launch_fail", stream)
            time.sleep(10)
            continue

        # check if the player launched
        ret = player_proc.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        if ret == 0:
            logger.info("The player is now running.")
            set_status("playing", stream)
            time.sleep(10) # must wait until the stream is up (hacky but meh)
            healthy = do_check_omx_healthy()
        else:
            logger.warning("The player did not start, will retry in 10 secs.")
            set_status("launch_fail", stream)
            time.sleep(10)
            continue

        # keep checking the player is running/healthy
        while ret == 0 and healthy:
            time.sleep(5)
            ret = player_proc.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
            healthy = do_check_omx_healthy()

        # player needs re-launching
        logger.warning("The player has stopped, will attempt to restart it.")
        set_status("stopped", stream)

def do_multi_stream(player, streams, cyclesecs):
    """Runs a best-effort loop to keep the player always watching a stream,
    cycling between the specified streams at the specified delay.
    """
    global last_omx_duration
    global player_proc
    cmd = PLAYER_CMDS[player]
    cycle = False
    s_index = 0

    def cycler():
        """Forces a stream cycle at regular intervals.
        """
        nonlocal cycle
        while True:
            time.sleep(cyclesecs)
            logger.debug("Setting stream cycle flag.")
            cycle = True

    # start the stream cycler
    logger.debug("Starting multi stream cycler thread...")
    t = Thread(target=cycler, daemon=True)
    t.start()

    logger.debug("Starting multi stream infinity loop...")
    while True:
        healthy = False
        last_omx_duration = 0

        # cycle stream if time is up
        if cycle:
            logger.debug("Honouring stream cycle flag.")
            cycle = False
            s_index = s_index + 1 if s_index < len(streams) - 1 else 0
        stream = streams[s_index]

        # try to launch omxplayer
        logger.info("Launching {} player with stream '{}'...".format(
            player.upper(),
            stream,
        ))
        set_status("launching", stream)
        try:
            player_proc = pexpect.spawn(cmd.format(url=stream))
        except Exception as ex:
            logger.warning("Launch error, will retry in 10 secs - {}".format(ex))
            set_status("launch_fail", stream)
            time.sleep(10)
            continue

        # check if the player launched
        ret = player_proc.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        if ret == 0:
            logger.info("The player is now running.")
            set_status("playing", stream)
            time.sleep(10) # must wait until the stream is up (hacky but meh)
            healthy = do_check_omx_healthy()
        else:
            logger.warning("The player did not start, will retry in 10 secs.")
            set_status("launch_fail", stream)
            time.sleep(10)
            continue

        # keep checking the player is running/healthy AND doesn't need a stream cycle
        while ret == 0 and healthy and not cycle:
            time.sleep(5)
            ret = player_proc.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
            healthy = do_check_omx_healthy()

        # player needs re-launching
        if ret != 0 or not healthy:
            logger.warn("The player has stopped, will attempt to restart it.")
        else:
            player_proc.close()
            logger.info("Stream has played for long enough, will cycle to next one.")
        set_status("stopped", stream)

##########################

def run_server():
    run(host="0.0.0.0", port=7070)

@route("/status")
def get_status():
    global status
    return status

@route("/reboot")
def do_reboot():
    os.system("reboot")
    return ""

##########################

if __name__ == "__main__":
    """CLI entry point
    """
    if len(sys.argv) < 3:
        print("USAGE: streamwatcher <player> <stream URL 1> [ <stream URL 2> ... cyclesecs ]")
        sys.exit(-1)

    logger = make_logger("streamwatcher")
    signal.signal(signal.SIGINT, signal_handler)
    bottle_thread = Thread(target=run_server, daemon=True)
    bottle_thread.start()

    player = sys.argv[1]
    streams = sys.argv[2:]
    if len(streams) == 1:
        status["mode"] = "single"
        do_single_stream(player, streams[0])
    else:
        cyclesecs = int(streams[-1])
        streams = streams[:-1]
        status["mode"] = "cycle"
        do_multi_stream(player, streams, cyclesecs)
