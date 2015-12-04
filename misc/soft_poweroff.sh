#!/bin/bash
# soft_poweroff.sh
# Do a poweroff after checking several conditions
# 03-DEC-2015 Isaac Hailperin <isaac.hailperin@gmail.com>

# The following values server as defaults and are overwritten
# in LOCAL_CONFIG, see below

# Minimum load that will prevent script from not powering off.
# It will be scaled with the number of available processors.
# Should be a float, like "0.3"
# This might need tuning
MIN_LOAD=0.3

# List of commands that if present in ps output should
# prevent the machine from powering off. Should be 
# a "|" seperated list, e.g. "dnf|vim"
COMMAND_LIST="dnf|vim"

# List of users that should be ignored if logged in.
# e.g. "joe|cathy"
IGNORE_USERS=""

# Minimum uptime in seconds since boot to be elegible for shutdown
MIN_UPTIME=3600

# Load local config file if it exists
LOCAL_CONFIG=/usr/local/etc/soft_poweroff.cfg
[ -f ${LOCAL_CONFIG} ] && source ${LOCAL_CONFIG}
# Create local config file if it does not exist
[ -f ${LOCAL_CONFIG} ] || cat >>${LOCAL_CONFIG}<<EOF
# Config file for $(basename $0)

# Minimum load that will prevent script from not powering off.
# It will be scaled with the number of available processors.
# Should be a float, like "0.3"
# This might need tuning
MIN_LOAD=$MIN_LOAD

# List of commands that if present in ps output should
# prevent the machine from powering off. Should be 
# a "|" seperated list, e.g. "dnf|vim"
COMMAND_LIST=$COMMAND_LIST

# List of users that should be ignored if logged in.
# e.g. "joe|cathy"
IGNORE_USERS=$IGNORE_USERS

# Minimum uptime in seconds since boot to be elegible for shutdown
MIN_UPTIME=$MIN_UPTIME
EOF

# exit if load exeeds a certain level
# load is defined to be the average over the last 5 minutes
check_load(){
    load=$(uptime |awk '{print $10}' |sed 's/,//')
    num_processors=$(grep processor /proc/cpuinfo |wc -l)
    rel_load=$(echo "scale=3; $load / $num_processors" |bc)
    min_exceedet=$(echo "$rel_load > $MIN_LOAD" |bc)
    if [ $min_exceedet == "1" ]; then
        echo "relative load is too high (${rel_load}), not shutting down"
        exit 0
    fi
    echo "Load not high enough to prevent shutdown"
}

# exit if certain processes exist
check_processes(){
    ps -elf |grep -v grep |grep -E "${COMMAND_LIST}" >/dev/null
    if [ $? == "0" ]; then
        echo "Found at least one of ${COMMAND_LIST}, not shutting down"
        exit 0
    fi
    echo "No processes found that would prevent shutdown"
}

# check if someone is logged in
check_logins() {
    num_logged_in=$(who |grep -v -E ${IGNORE_USERS} |wc -l)
    if [ $num_logged_in != "0" ]; then 
        echo "Found $num_logged_in sessions, not shutting down"
        exit 0
    fi
    echo "Found no logins that would prevent shutdown"
}

# check if machine is up for a while
check_uptime() {
    seconds_since_boot=$(awk '{print $1}' /proc/uptime |awk -F. '{print $1}') 
    if [ $seconds_since_boot -lt $MIN_UPTIME ]; then
        echo "System uptime is shorter then $MIN_UPTIME seconds, not shutting down"
        exit 0
    fi
    echo "System uptime is not short enough to prevent shutdown"
}

check_uptime
check_logins
check_load
check_processes
echo "System will be automatically powered off in 60 seconds" |wall
sleep 60
poweroff

