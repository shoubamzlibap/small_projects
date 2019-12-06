#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dvd_title.py
Get the title of a dvd.
Can be used as a standalone tool or as library.
"""

# 30-AUG-2018 - Isaac Hailperin <isaac.hailperin@gmail.com> - initial version

from subprocess import PIPE, Popen
import subprocess
from imdb import IMDb
import logging

TMP_FILE = '/tmp/dvd_title.tmp'

###
# logging setup
###
LOG_LEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL, }

# default log level
DEFAULT_LOG_LEVEL = 'debug'

# should shell command output be printed to stdout?
DEBUG = True 

# used for subprocess calls - print stdout and stderr if log level is debug
if DEBUG:
    DEV_ZERO = None
else:
    DEV_ZERO = open('/dev/zero', 'w')

LOGGER = logging.getLogger('dvd_title')
LOGGER.setLevel(LOG_LEVELS[DEFAULT_LOG_LEVEL])


def read_title(device='/dev/sr0', handbrakecli='/bin/HandBrakeCLI'):
    "Read the title of the dvd, as printed by libdvdnav"
    # invoking awk is a dirty hack, however there were strange characters in the handbrake
    # output, which I could not get rid of. piping the output through awk did the trick
    hb_command = [handbrakecli, ' --scan', '-i ', device]
    LOGGER.debug('hb_command: ' + ' '.join(hb_command))
    with open(TMP_FILE, 'w+') as tmp_file_fh:
        subprocess.call(hb_command, stdout=tmp_file_fh, stderr=subprocess.STDOUT)
    LOGGER.debug('Done with scanning')

def read_title_old(device='/dev/sr0', handbrakecli='/bin/HandBrakeCLI'):
    "Read the title of the dvd, as printed by libdvdnav"
    # invoking awk is a dirty hack, however there were strange characters in the handbrake
    # output, which I could not get rid of. piping the output through awk did the trick
    hb_command = handbrakecli + ' --scan -i ' + device + " | awk -F: '/DVD Title/ {print $3}' "
    LOGGER.debug('deterime title, hb_command: ' + hb_command)
    process = Popen(hb_command, stdout=PIPE, shell=True)
    while True:
        line = process.stdout.readline()
        if line == '' and process.poll() is not None:
            break
        if line:
            dvd_title = line.title().replace('_', ' ').strip()
            return dvd_title
    return None

def get_year(movie_title):
    "Get the year a movie title was published"
    myimdb = IMDb()
    # This search will most likely return multiple results.
    # I have currently no other method to identify a dvd,
    # so I am just using the first result in the hope that it
    # has the highest likelyhood of being correct
    movies = myimdb.search_movie(movie_title)
    if movies:
        return movies[0].get('year')
    else:
        return None


def title_with_year(device='/dev/sr0', handbrakecli='/bin/HandBrakeCLI'):
    "get dvd title with year"
    LOGGER.debug('device: ' + device + '; handbrakecli: ' + handbrakecli)
    dvd_title = read_title(device=device, handbrakecli=handbrakecli)
    if dvd_title:
        year = get_year(dvd_title)
    else:
        return None
    if year:
        return dvd_title + ' (' + str(year) + ')' 
    else:
        return dvd_title

def setup_logging():
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVELS[DEFAULT_LOG_LEVEL])
    # create formatter and add it to the handlers
    ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(ch_formatter)
    # add the handlers to LOGGER
    LOGGER.addHandler(ch)

def main():
    setup_logging()
    print(title_with_year())

if __name__ == '__main__':
    main()
