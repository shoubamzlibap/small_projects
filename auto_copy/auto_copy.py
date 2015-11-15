#!/usr/bin/env python
# auto_copy.py
# Automatically copy stuff from the CDRom drive to disk.
# This is meant to be called via udev trigger. Details shall follow.
# example for udev rule:
#SUBSYSTEM=="block", ENV{ID_CDROM}=="?*", ENV{ID_PATH}=="pci-0000:00:1f.2-scsi-1:0:0:0", ACTION=="change", RUN+="/home/isaac/bin/auto_copy.sh"

# 11-NOV-2015 - Isaac Hailperin <isaac.hailperin@gmail.com> - initial version

import datetime
import os
import shutil
import subprocess
import sys

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
# constants
kilo = 1024
mega = kilo * kilo

if verbose:
    dev_zero = None
else:
    dev_zero = open('/dev/zero','w')

def determine_media_type():
    """
    Determine the media type of inserted media

    returns one of ['VIDEO_DVD', 'DATA']
    """
    media_type = ''
    mount(cdrom_device, cdrom_mnt)
    if os.path.exists(cdrom_mnt + '/VIDEO_TS'):
        media_type = 'VIDEO_DVD'
    else:
        media_type = 'DATA'
    umount(cdrom_device)
    return media_type

def mount(cdrom_device, cdrom_mnt):
    """
    Mount cdrom drive
    """
    mount_command = 'mount ' + cdrom_device + ' ' + cdrom_mnt
    if verbose: print(mount_command)
    subprocess.call(mount_command.split(), stdout=dev_zero, stderr=dev_zero)

def umount(cdrom_device):
    """
    uMount cdrom drive
    """
    umount_command = 'umount ' + cdrom_device 
    if verbose: print(umount_command)
    subprocess.call(umount_command.split(), stdout=dev_zero, stderr=dev_zero)
    
def rip_large_tracks():
    """
    Call HandbrakeCLI to rip large tracks
    """
    handbrake_base_cmd = 'HandBrakeCLI -i /dev/sr0 -o /home/isaac/video/new/OUTFILE -e x264 -q 20.0 -a 1,2,3 -s 1,2,3 -E ffaac -B 160 -6 dpl2 -R Auto -D 0.0 --audio-copy-mask aac,ac3,dtshd,dts,mp3 --audio-fallback ffac3 -f mp4 --loose-anamorphic --modulus 2 -m --x264-preset ' + rip_speed + ' --h264-profile main --h264-level 4.0 --optimize'
    track_num = 1
    while track_num <= max_tracks:
        outfile_name = 'new_video_' + str(datetime.datetime.now()).replace(' ', '_') + '.mp4'
        handbrake_cmd = handbrake_base_cmd.replace('OUTFILE', outfile_name) + ' -t ' + str(track_num)
        track_num += 1
        if verbose: print(handbrake_cmd)
        subprocess.call(handbrake_cmd.split(), stdout=dev_zero, stderr=dev_zero)

def copy_large_files():
    """ 
    Copy large files from cdrom
    """
    mount(cdrom_device, cdrom_mnt)
    file_list = get_recursive_file_list(cdrom_mnt)
    for file_path in file_list:
        size_in_bytes = os.path.getsize(file_path)
        if size_in_bytes / mega > min_file_size:
            if verbose: print('copying ' + file_path + ' to ' + data_dir)
            shutil.copy(file_path, data_dir)        
    umount(cdrom_device)

def get_recursive_file_list(root_dir):
    """
    Get a recursive listing of files in
    root_dir: string, the root dir to start the file listing
    """
    if verbose: print("Getting recursive file list for " + root_dir)
    file_list = []
    for root, sub_folders, files in os.walk(root_dir):
        for file in files:
            file_list.append(os.path.join(root,file))
    return file_list


if __name__ == '__main__':
    tray_open = subprocess.call(['/usr/local/bin/trayopen', cdrom_device])
    if tray_open == 0: sys.exit(0)
    if os.path.exists(no_exec_file):
        if verbose: print('Exiting, found no exec file ' + no_exec_file)
        sys.exit(0)
    media_type = determine_media_type()
    if verbose: print('Media type found is ' + media_type)
    if media_type == 'VIDEO_DVD':
        rip_large_tracks()
    if media_type == 'DATA':
        copy_large_files()
    # eject when done
    subprocess.call(['eject'], stdout=dev_zero, stderr=dev_zero)
