#!/bin/sh
/bin/HandBrakeCLI  --scan -i  /dev/sr0 | awk -F: '/DVD Title/ {print $3}' |head -1 >/tmp/dvd_title.tmp
