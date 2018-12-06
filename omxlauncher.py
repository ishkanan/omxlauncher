#!/usr/bin/python
import logging
import pexpect
import time
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

#stream datasources

#ZAC TEST GP2018
STAGE = 'rtsp://wowza.mmf:1935/live/foh.stream'

# create logger
logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.FileHandler('omxlauncher.log')
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s  - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


#logging.basicConfig(filename='omxlauncher.log',level=logging.DEBUG)
logger.debug('launcher boot')
while (1 > 0):
        #build command
        omx_cmd = "omxplayer -o hdmi {} ".format(STAGE)
        running = 0
        #omx_cmd = "omxplayer  {} ".format(STAGE)
        child = pexpect.spawn (omx_cmd)
        a = child.expect([pexpect.TIMEOUT,pexpect.EOF], timeout=10) # wait 10 sec for process to end
        #logging.debug(a.before)
        if (a ==0):
                logger.debug('player start')
                time.sleep(10)
                child.send('2')               # send 2 to exploit bug that syncs stream   
                #child.interact()              # Give control of the child to the user.
                #logging.debug('launcher running')
                a=0
                running = 1
        while (a == 0):
                a = child.expect([pexpect.TIMEOUT,pexpect.EOF], timeout=300) # wait 5min for process to end
                if (a ==0):
                        running = 1

        if (running == 1):
                logger.debug('player exit')
