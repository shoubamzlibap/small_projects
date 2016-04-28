#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The daemon that calls auto_copy.py uppon optical disc insertion
"""

import signal
import sys
import time

sys.path.append('/usr/local/bin')

import auto_copy

SIGNAL_RECEIVED = False

def run_daemon(config):
    """
    Run the damon

    config: configParser object
    """
    signal.signal(signal.SIGUSR1, signal_handler)
    while True:
        time.sleep(1)
        global SIGNAL_RECEIVED
        if SIGNAL_RECEIVED:
            auto_copy.auto_copy(config)
            SIGNAL_RECEIVED = False

def signal_handler(dump1, dump2):
    global SIGNAL_RECEIVED
    SIGNAL_RECEIVED = True

if __name__ == "__main__":
    main_config = auto_copy.read_config('/etc/auto_copy.yml')
    auto_copy.setup_logging(main_config)
    run_daemon(main_config)
