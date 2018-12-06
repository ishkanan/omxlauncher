#!/usr/bin/python

import logging
import os
import pexpect
import signal
import sys
import time

OMX_CMD = "omxplayer -o hdmi --avdict rtsp_transport:tcp --threshold 0.2 {url}"
#OMX_CMD = "google-chrome {url}"
child = None
logger = None

def signal_handler(signum, frame):
    if child == None:
        logger.debug("omxplayer not launched, nothing to do.")
    else:
        logger.info("Force-closing omxplayer...")
        child.close(force=True)
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

def main(args):
    """Runs a loop to ensure omxplayer is always running, and keeps retrying
    in the event of a disconnect.
    """
    global child
    cmd_to_run = OMX_CMD.format(url=args[0])

    logger.debug("Entering loop to keep omxplayer running...")
    while True:
        logger.debug("Launching omxplayer...")
        child = pexpect.spawn(cmd_to_run)
        ret = child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        if ret == 0:
            logger.debug("omxplayer is running. Yay.")
            #child.send("2")               # send 2 to exploit bug that syncs stream   
            #child.interact()              # Give control of the child to the user.
        else:
            logger.debug("omxplayer failed to start, retrying in 10 seconds...")
            time.sleep(10)
            continue

        ret = child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
        while ret == 0:
            ret = child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
        logger.debug("omxplayer has exited, will restart...")

if __name__ == "__main__":    
    if len(sys.argv) < 3:
        print("USAGE: omxlauncher <log file> <feed URL>")
        sys.exit(-1)
    logger = make_logger("omxlauncher", sys.argv[1])
    signal.signal(signal.SIGINT, signal_handler)
    main(sys.argv[2:])
