#!/usr/bin/env python

import logging
import os
import pexpect
import signal
import sys
from threading import Thread
import time

from bottle import route, run

PLAYER_CMDS = {
    "omx": "omxplayer -b -o hdmi --avdict rtsp_transport:tcp --threshold 0.2 {url}",
    "vlc": "vlc {url}",
}

logger = None
player_proc = None
status = {
    "status": "booting",
    "stream": None,
}

##########################

def set_status(stage, stream):
    global status
    status = {
        "status": stage,
        "stream": stream,
    }

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

def make_logger(name, out_file):
    """Creates a logger with specified name that writes to console and
    specified output file.
    """
    l = logging.getLogger(name)
    l.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s  - %(levelname)s - %(message)s')
    ch = logging.FileHandler(out_file)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    l.addHandler(ch)
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    l.addHandler(ch)
    return l

def do_single_stream(player, stream):
    """Runs a best-effort loop to keep the player always watching a single stream.
    """
    global player_proc
    cmd = PLAYER_CMDS[player].format(url=stream)

    logger.debug("Starting single stream infinity loop...")
    while True:
        logger.info("Launching {} player...".format(player.upper()))
        set_status("launching", stream)
        try:
            player_proc = pexpect.spawn(cmd)
        except Exception as ex:
            logger.warning("Launch error, will retry in 10 secs - {}".format(ex))
            set_status("launch_fail", stream)
            time.sleep(10)
            continue

        ret = player_proc.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        if ret == 0:
            logger.info("The player is now running.")
            set_status("playing", stream)
        else:
            logger.warning("The player did not start, will retry in 10 secs.")
            set_status("launch_fail", stream)
            time.sleep(10)
            continue

        while ret == 0:
            ret = player_proc.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
        logger.warning("The player has stopped, will attempt to restart it.")
        set_status("stopped", stream)

def do_multi_stream(player, streams, cyclesecs):
    """Runs a best-effort loop to keep the player always watching a stream,
    cycling between the specified streams at the specified delay.
    """
    global player_proc
    cmd = PLAYER_CMDS[player]
    cycle = False
    s_index = 0

    def cycler():
        nonlocal cycle
        while True:
            time.sleep(cyclesecs)
            logger.debug("Setting stream cycle flag.")
            cycle = True

    logger.debug("Starting multi stream cycler thread...")
    t = Thread(target=cycler, daemon=True)
    t.start()

    logger.debug("Starting multi stream infinity loop...")
    while True:
        if cycle:
            logger.debug("Honouring stream cycle flag.")
            cycle = False
            s_index = s_index + 1 if s_index < len(streams) - 1 else 0
        stream = streams[s_index]

        logger.info("Launching {} player with stream '{}'...".format(
            player.upper(),
            stream,
        ))
        try:
            player_proc = pexpect.spawn(cmd.format(url=stream))
        except Exception as ex:
            logger.warning("Launch error, will retry in 10 secs - {}".format(ex))
            time.sleep(10)
            continue

        ret = player_proc.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        if ret == 0:
            logger.info("The player is now running.")
        else:
            logger.warn("The player did not start, will retry in 10 secs.")
            time.sleep(10)
            continue

        while ret == 0 and not cycle:
            ret = player_proc.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
        if ret != 0:
            logger.warn("The player has stopped, will attempt to restart it.")
        else:
            player_proc.close()
            logger.info("Stream has played for long enough, will cycle to next one.")

##########################

def run_server():
    run(host="0.0.0.0", port=7070)

@route("/status")
def status():
    global status
    return status

##########################

if __name__ == "__main__":
    """CLI entry point
    """
    if len(sys.argv) < 4:
        print("USAGE: streamwatcher <logfile> <player> <stream URL 1> [ <stream URL 2> ... cyclesecs ]")
        sys.exit(-1)

    logger = make_logger("streamwatcher", sys.argv[1])
    signal.signal(signal.SIGINT, signal_handler)
    bottle_thread = Thread(target=run_server, daemon=True)
    bottle_thread.start()

    player = sys.argv[2]
    streams = sys.argv[3:]
    if len(streams) == 1:
        do_single_stream(player, streams[0])
    else:
        cyclesecs = int(streams[-1])
        streams = streams[:-1]
        do_multi_stream(player, streams, cyclesecs)
