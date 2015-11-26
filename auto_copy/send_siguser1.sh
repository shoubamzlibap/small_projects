#!/bin/bash
kill -SIGUSR1 $(ps -elf |grep auto_copy_daemon.py |awk '/python/ {print $4}')
sleep 1
