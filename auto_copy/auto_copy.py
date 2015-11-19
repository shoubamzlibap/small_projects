#!/usr/bin/env python
# auto_copy.py
# Automatically copy stuff from the CDRom drive to disk.
# This is meant to be called via udev trigger. Details shall follow.
# example for udev rule:
#SUBSYSTEM=="block", ENV{ID_CDROM}=="?*", ENV{ID_PATH}=="pci-0000:00:1f.2-scsi-1:0:0:0", ACTION=="change", RUN+="/home/isaac/bin/auto_copy.sh"

# 11-NOV-2015 - Isaac Hailperin <isaac.hailperin@gmail.com> - initial version

import atexit
import datetime
import logging
import os
import shutil
import signal
import subprocess
import sys
import time

# quality for dvd rips
# one of 
# 'veryfast', 'fast', 'slow', 'veryslow', 'placebo'
# and probably a few more. Check HandBrake for details.
rip_speed = 'veryslow'
# mount point for cdrom device
cdrom_mnt = '/mnt/cdrom'
# your cdrom device
cdrom_device = '/dev/sr0'
# place where data should be put
data_dir = '/mnt/video/new'
# print information about what is going on
# also print output of shell commands
verbose = True
# minimum size of files to be copied, in MB
min_file_size = 10
# maximum number of tracks attempted to be ripped from DVD
max_tracks = 10
# file that prevents execution if present
no_exec_file = '/var/tmp/no_auto_copy' 
# log file
log_file = '/tmp/auto_copy.log'
# default log level
default_log_level = 'debug'
# location of the trayopen binary
trayopen = '/usr/local/bin/trayopen'

# ENVIRONMENT will be passed to subprocess.Popen()
ENVIRONMENT = {
    'PATH' : '/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/isaac/bin',
    'http_proxy' : '',
    'https_proxy' : '',
    'ftp_proxy' : '',
    }


# constants
kilo = 1024
mega = kilo * kilo


logger = logging.getLogger('auto_copy')
logger.setLevel(logging.DEBUG)

my_pid = str(os.getpid())

LOG_LEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL, }

if verbose:
    dev_zero = None
else:
    dev_zero = open('/dev/zero','w')



def determine_media_type():
    """
    Determine the media type of inserted media

    returns one of ['VIDEO_DVD', 'DATA']
    """
    logger.debug('Determining media type. PID ' + my_pid)
    media_type = ''
    time.sleep(5)
    mount(cdrom_device, cdrom_mnt)
    time.sleep(5)
    if os.path.exists(cdrom_mnt + '/VIDEO_TS') or os.path.exists(cdrom_mnt + '/video_ts'):
        media_type = 'VIDEO_DVD'
    else:
        media_type = 'DATA'
    logger.debug(cdrom_mnt + ' contains ' + '\n'.join(os.listdir(cdrom_mnt)))
    logger.debug('Media type found was ' + media_type + ' PID ' + my_pid)
    umount(cdrom_device)
    return media_type

def mount(cdrom_device, cdrom_mnt):
    """
    Mount cdrom drive
    """
    mount_command = 'mount ' + cdrom_device + ' ' + cdrom_mnt
    logger.debug('Executing: ' + mount_command)
    result = subprocess.call(mount_command.split(), stdout=dev_zero, stderr=dev_zero)
    if result != 0:
        logger.info('Could not mount optical drive - probably empty. Exiting')
        sys.exit(0)

def umount(cdrom_device):
    """
    uMount cdrom drive
    """
    umount_command = 'umount ' + cdrom_device 
    logger.debug('Executing: ' + umount_command)
    subprocess.call(umount_command.split(), stdout=dev_zero, stderr=dev_zero)
    
def rip_large_tracks():
    """
    Call HandbrakeCLI to rip large tracks
    """
    logger.debug('Starting to rip large tracks')
    handbrake_base_cmd = '/bin/HandBrakeCLI -i /dev/sr0 -o /home/isaac/video/new/OUTFILE -e x264 -q 20.0 -a 1,2,3 -s 1,2,3 -E ffaac -B 160 -6 dpl2 -R Auto -D 0.0 --audio-copy-mask aac,ac3,dtshd,dts,mp3 --audio-fallback ffac3 -f mp4 --loose-anamorphic --modulus 2 -m --x264-preset ' + rip_speed + ' --h264-profile main --h264-level 4.0 --optimize'
    track_num = 1
    while track_num <= max_tracks:
        outfile_name = 'new_video_' + str(datetime.datetime.now()).replace(' ', '_').replace(':', '-') + '.mp4'
        handbrake_cmd = handbrake_base_cmd.replace('OUTFILE', outfile_name) + ' -t ' + str(track_num)
        track_num += 1
        logger.debug('Executing: ' + handbrake_cmd)
        process = subprocess.Popen(handbrake_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENVIRONMENT)
        (stdoutdata, stderrdata) = process.communicate() # commuicate() also waits for the process to finish
        if stderrdata: logger.debug(stderrdata)

def copy_large_files():
    """ 
    Copy large files from cdrom
    """
    logger.debug('Starting to copy large files')
    mount(cdrom_device, cdrom_mnt)
    file_list = get_recursive_file_list(cdrom_mnt)
    logger.debug('File list: ' + '\n'.join(file_list))
    for file_path in file_list:
        size_in_bytes = os.path.getsize(file_path)
        logger.debug('Considering for copy: ' + str(size_in_bytes) + 'B ' + file_path)
        if size_in_bytes / mega > min_file_size:
            logger.debug('Copying ' + file_path + ' to ' + data_dir)
            shutil.copy(file_path, data_dir)        
    umount(cdrom_device)

def get_recursive_file_list(root_dir):
    """
    Get a recursive listing of files in
    root_dir: string, the root dir to start the file listing
    """
    logger.debug("Getting recursive file list for " + root_dir)
    file_list = []
    for root, sub_folders, files in os.walk(root_dir):
        for file in files:
            file_list.append(os.path.join(root,file))
    return file_list


class Lock:
    """
    Simple implementation of a lock. Should be cleaned up on almost any exit,
    with the notable exception of SIGKILL (cannot be cought by underlying C library).
    """

    def __init__(self, catch_signals=None):
        """
        Set a few attributes, and call needed methods
        """
        self.catch_signals = catch_signals
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
        except OSError:
            logger.info('Could not aquire lock, exiting (PID ' + str(self.my_pid) + ')')
            sys.exit(0)

    def release_lock(self, signal_num, stack_frame ):
        """
        Release a lock - only if it belongs to this PID

        Arguments are manadatory by signal.signal
        """
        if not os.path.isdir(self.lock): return
        pids = os.listdir(self.lock)
        if len(pids) > 1: raise Exception('ERROR: Found more then one lock - ' + ', '.join(pids))
        if int(pids[0]) != self.my_pid: return
        os.rmdir(self.pid_lock)
        os.rmdir(self.lock)

    def make_singular(self):
        """
        handle lock management, to insure there is only a singualr instance running
        """
        atexit.register(self.release_lock, None, None)
        for sig in (signal.SIGABRT, signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self.release_lock)
        self.aquire_lock()


if __name__ == '__main__':
    ###
    # Logging
    ###
    # create file handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(LOG_LEVELS[default_log_level])
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVELS[default_log_level])
    # create formatter and add it to the handlers
    ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh_formatter = ch_formatter
    ch.setFormatter(ch_formatter)
    fh.setFormatter(fh_formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    ###
    # some checks bevor we start
    ###
    Lock()
    if os.path.exists(no_exec_file):
        logger.info('Exiting, found no exec file ' + no_exec_file)
        sys.exit(0)
    time.sleep(5)
    if not os.path.exists(trayopen):
        logger.debug('ERROR: Could not find ' + trayopen)
        sys.exit(1)
    tray_open = subprocess.call([trayopen, cdrom_device])
    if tray_open == 0: 
        logger.debug('Exiting as tray is currently open')
        sys.exit(0)
       
    ###
    # Action
    ###
    media_type = determine_media_type()
    if media_type == 'VIDEO_DVD':
        rip_large_tracks()
    elif media_type == 'DATA':
        copy_large_files()
    else:
        logger.warn('Could not determine media type')
    # eject when done
    logger.info('All tasks finished, ejecting')
    subprocess.call(['eject'], stdout=dev_zero, stderr=dev_zero)
