#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
auto_copy.py
Automatically copy stuff from the CDRom drive to disk.
This script will determine if it is a data disk or a
video DVD and act accordingly. It uses HandBrakeCLI
to rip video DVDs.

This is meant to be called via udev trigger but can also be
used manually.
"""

# 11-NOV-2015 - Isaac Hailperin <isaac.hailperin@gmail.com> - initial version
# 28-APR-2016 - Isaac Hailperin <isaac.hailperin@gmail.com> - Refactoring
# 30-AUG-2018 - Isaac Hailperin <isaac.hailperin@gmail.com> - Adding dvd title detection

import atexit
import datetime
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
import config_parser
import dvd_title

# ENVIRONMENT will be passed to subprocess.Popen()
ENVIRONMENT = {
    'PATH' : '/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin',
    'http_proxy' : '',
    'https_proxy' : '',
    'ftp_proxy' : '',
    }

# constants
KILO = 1024
MEGA = KILO * KILO

MY_PID = str(os.getpid())

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

LOGGER = logging.getLogger('auto_copy')
LOGGER.setLevel(LOG_LEVELS[DEFAULT_LOG_LEVEL])

class CouldNotMountException(Exception):
    pass


class CouldNotAcquireLockException(Exception):
    pass


class Lock(object):
    """
    Simple implementation of a lock. Should be cleaned up on almost any exit,
    with the notable exception of SIGKILL (cannot be cought by underlying C library).
    """

    def __init__(self):
        """
        Set a few attributes, and call needed methods
        """
        lock_dir = '/tmp'
        lock_name = os.path.basename(sys.argv[0])
        self.lock = os.path.join(lock_dir, lock_name)
        self.my_pid = os.getpid()
        self.pid_lock = os.path.join(self.lock, str(self.my_pid))
        self.make_singular()

    def aquire_lock(self):
        """
        Acquire a lock
        """
        try:
            os.mkdir(self.lock)
            os.mkdir(self.pid_lock)
            LOGGER.debug('Aqcuired lock')
        except OSError:
            LOGGER.info('Could not aquire lock, raising CouldNotAcquireLockException (PID ' + str(self.my_pid) + ')')
            raise CouldNotAcquireLockException()

    def release_lock(self, signal_num, stack_frame):
        """
        Release a lock - only if it belongs to this PID.
        This can be called from a signal handler and as such needs the unused
        arguments 'signal_num' and 'stack_frame'.

        Arguments are manadatory by signal.signal
        """
        if not os.path.isdir(self.lock): return
        pids = os.listdir(self.lock)
        if len(pids) > 1: raise Exception('ERROR: Found more then one lock - ' + ', '.join(pids))
        if len(pids) == 0: return #someone else is either aquirein or releasing the lock
        if int(pids[0]) != self.my_pid: return
        os.rmdir(self.pid_lock)
        os.rmdir(self.lock)
        LOGGER.debug('Lock released')
        return

    def make_singular(self):
        """
        handle lock management, to ensure there is only a singular instance running
        """
        atexit.register(self.release_lock, None, None)
        for sig in (signal.SIGABRT, signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self.release_lock)
        self.aquire_lock()


def determine_media_type(config):
    """
    Determine the media type of inserted media

    config: a configParser object

    returns one of ['VIDEO_DVD', 'DATA', 'AUDIO']
    """
    LOGGER.debug('Determining media type. PID ' + MY_PID)
    media_type = ''
    time.sleep(5)
    # check for audio first
    audio_check = config.cdparanoia + ' -Q'
    result = subprocess.call(audio_check.split(), stdout=DEV_ZERO, stderr=DEV_ZERO)
    if result == 0:
        LOGGER.debug('Media type found was AUDIO PID ' + MY_PID)
        return 'AUDIO'
    mount(config.cdrom_device, config.cdrom_mnt)
    time.sleep(5)
    if os.path.exists(config.cdrom_mnt + '/VIDEO_TS') or os.path.exists(config.cdrom_mnt + '/video_ts'):
        media_type = 'VIDEO_DVD'
    else:
        media_type = 'DATA'
    LOGGER.debug(config.cdrom_mnt + ' contains ' + '\n'.join(os.listdir(config.cdrom_mnt)))
    LOGGER.debug('Media type found was ' + media_type + ' PID ' + MY_PID)
    umount(config.cdrom_device)
    return media_type


def mount(cdrom_device, cdrom_mnt):
    """
    Mount cdrom drive
    """
    mount_command = 'mount ' + cdrom_device + ' ' + cdrom_mnt
    LOGGER.debug('Executing: ' + mount_command)
    result = subprocess.call(mount_command.split(), stdout=DEV_ZERO, stderr=DEV_ZERO)
    if result != 0:
        LOGGER.info('Could not mount optical drive - probably empty.')
        raise CouldNotMountException()


def umount(cdrom_device):
    """
    uMount cdrom drive
    """
    umount_command = 'umount ' + cdrom_device
    LOGGER.debug('Executing: ' + umount_command)
    subprocess.call(umount_command.split(), stdout=DEV_ZERO, stderr=DEV_ZERO)


def rip_large_tracks(config):
    """
    Call HandbrakeCLI to rip large tracks

    config: a configParser object

    """
    LOGGER.info('Starting to rip large tracks')
    handbrake_base_cmd = config.handbrakecli + ' -i ' + config.cdrom_device + ' -o ' \
        + config.data_dir + '/OUTFILE -e x264 -q 20.0 -a 1,2,3,4,5,6 -s 1,2,3,4,5,6 ' \
        + '-E ffaac -B 160 -6 dpl2 -R Auto -D 0.0 ' \
        + '--audio-copy-mask aac,ac3,dtshd,dts,mp3 --audio-fallback ffac3 ' \
        + '-f mp4 --loose-anamorphic --modulus 2 -m --x264-preset ' \
        + config.rip_speed + ' --h264-profile main --h264-level 4.0 --optimize'
    LOGGER.debug('Trying to determine dvd title ...')
    LOGGER.debug('cdrom_device: ' + config.cdrom_device + '; handbrakecli: ' + config.handbrakecli)
    dvd_title_with_year = dvd_title.title_with_year(
            device=config.cdrom_device, handbrakecli=config.handbrakecli)
    LOGGER.debug('dvd title determined as: "' + str(dvd_title_with_year) + '"')
    for track_num in xrange(1, config.max_tracks + 1):
        if not dvd_title_with_year:
            # set a default that at least hints to when the file was ripped
            outfile_name = 'new_video_' + str(track_num) + '_' \
                + str(datetime.datetime.now()).replace(' ', '_').replace(':', '-') \
                + '.mp4'
        else:
            appendix = '.mp4'
            if track_num > 1:
                appendix = '_' + str(track_num) + '.mp4'
            # add double quotes around name because the title will contain whitespace
            outfile_name = '"' + dvd_title_with_year + appendix + '"'
        handbrake_cmd = handbrake_base_cmd.replace('OUTFILE', outfile_name) \
            + ' -t ' + str(track_num)
        LOGGER.debug('Executing: ' + handbrake_cmd)
        with open('/dev/zero', 'w') as dev_zero:
            subprocess.call(handbrake_cmd, stdout=dev_zero, stderr=dev_zero, shell=True)


def rip_audio_cd(config):
    """
    rip an audio cd

    config: a configParser object

    """
    LOGGER.info('Starting to rip audio CD')
    rip_command = config.abcde + ' -N'
    with open('/dev/zero', 'w') as dev_zero:
        result = subprocess.call(rip_command.split(), stdout=dev_zero, stderr=dev_zero)
        if result != 0:
            LOGGER.warn('Something went wrong ripping the audio CD.')


def copy_large_files(config):
    """
    Copy large files from cdrom

    config: a configParser object

    """
    LOGGER.info('Starting to copy large files')
    mount(config.cdrom_device, config.cdrom_mnt)
    file_list = get_recursive_file_list(config.cdrom_mnt)
    LOGGER.debug('File list: ' + '\n'.join(file_list))
    for file_path in file_list:
        size_in_bytes = os.path.getsize(file_path)
        LOGGER.debug('Considering for copy: ' + str(size_in_bytes) + 'B ' + file_path)
        if size_in_bytes / MEGA > config.min_file_size:
            LOGGER.debug('Copying ' + file_path + ' to ' + config.data_dir)
            shutil.copy(file_path, config.data_dir)
    umount(config.cdrom_device)


def get_recursive_file_list(root_dir):
    """
    Get a recursive listing of files in
    root_dir: string, the root dir to start the file listing

    """
    LOGGER.debug("Getting recursive file list for " + root_dir)
    file_list = []
    for root, sub_folders, files in os.walk(root_dir):
        for my_file in files:
            file_list.append(os.path.join(root, my_file))
    return file_list


def setup_logging(config):
    """
    Do some setup for logging

    config: a configParser object

    """
    # create file handler
    fh = logging.FileHandler(config.log_file)
    fh.setLevel(LOG_LEVELS[DEFAULT_LOG_LEVEL])
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVELS[DEFAULT_LOG_LEVEL])
    # create formatter and add it to the handlers
    ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh_formatter = ch_formatter
    ch.setFormatter(ch_formatter)
    fh.setFormatter(fh_formatter)
    # add the handlers to LOGGER
    LOGGER.addHandler(ch)
    LOGGER.addHandler(fh)


def read_config(config_file):
    """
    Read the configuration from

    config_file: path to a yaml file containing the configuration

    """
    return config_parser.configParser(config_file,
        defaults={
            'rip_speed': 'slow',
            'cdrom_mnt': '/mnt/cdrom',
            'min_file_size': 10,
            'max_tracks': 10,
            'no_exec_file': '/var/tmp/no_auto_copy',
            'config.log_file': '/tmp/auto_copy.log',
            'trayopen': '/usr/local/bin/trayopen',
            'handbrakecli': '/bin/HandBrakeCLI',
            'cdparanoia': '/bin/cdparanoia',
            'abcde': '/bin/abcde',
        },
        allowed_values={
            'rip_speed': ['veryfast', 'fast', 'slow', 'veryslow', 'placebo'],
        },
        required_keys=[
            'cdrom_device',
            'data_dir',
        ],
    )


def sanity_checks_pass(config, my_lock):
    """
    Do some sanity checking bevor the real action

    config: a configParser object
    my_lock: a Lock object

    """
    # do not exit if no_exec_file exists
    if os.path.exists(config.no_exec_file):
        LOGGER.info('Exiting, found no exec file ' + config.no_exec_file)
        LOGGER.debug('Explicitly releasing lock since no exec file found')
        my_lock.release_lock(None, None)
        return False
    LOGGER.debug('Sleeping 10 secs to allow drive to settle')
    time.sleep(10)
    LOGGER.debug('Slept 10 secs')
    # check if we have custom binary trayopen
    if not os.path.exists(config.trayopen):
        LOGGER.debug('ERROR: Could not find ' + config.trayopen)
        LOGGER.debug('Explicitly releasing lock as trayopen was not found')
        my_lock.release_lock(None, None)
        sys.exit(1)
    # check if the tray is open or closed
    tray_open = subprocess.call([config.trayopen, config.cdrom_device])
    if tray_open == 0:
        LOGGER.debug('Exiting as tray is currently open')
        LOGGER.debug('Explicitly releasing lock as tray is currently open')
        my_lock.release_lock(None, None)
        return False
    return True


def auto_copy(config):
    """
    do the auto copy of stuff from optical disc

    config: a configParser object

    """
    # only one instance running at a time
    try:
        my_lock = Lock()
    except CouldNotAcquireLockException:
        return
    if not sanity_checks_pass(config, my_lock):
        return
    ###
    # Action
    ###
    try:
        media_type = determine_media_type(config)
        if media_type == 'VIDEO_DVD':
            rip_large_tracks(config)
        elif media_type == 'DATA':
            copy_large_files(config)
        elif media_type == 'AUDIO':
            rip_audio_cd(config)
        else:
            LOGGER.warn('Could not determine media type')
        # eject when done
        LOGGER.info('All tasks finished, ejecting')
        subprocess.call(['eject'], stdout=DEV_ZERO, stderr=DEV_ZERO)
    except Exception:
        LOGGER.warn('Something went wrong, ejecting anyway')
        subprocess.call(['eject'], stdout=DEV_ZERO, stderr=DEV_ZERO)
    finally:
        LOGGER.debug('Explicitly releasing lock in finally block')
        my_lock.release_lock(None, None)
        subprocess.call(['eject'], stdout=DEV_ZERO, stderr=DEV_ZERO)


if __name__ == '__main__':
    main_config = read_config('/etc/auto_copy.yml')
    setup_logging(main_config)
    auto_copy(main_config)

