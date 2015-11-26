#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal, time
import auto_copy

SIGNAL_RECEIVED = False

def run_daemon():
    signal.signal(signal.SIGUSR1, signal_handler)
    while True:
        time.sleep(1)
        global SIGNAL_RECEIVED
        if SIGNAL_RECEIVED:
            auto_copy.auto_copy()
            SIGNAL_RECEIVED = False

def signal_handler(dump1, dump2):
    global SIGNAL_RECEIVED
    SIGNAL_RECEIVED = True

if __name__ == "__main__":
    auto_copy.setup_logging()
    run_daemon()
