# auto_copy
Automatically copy CD/DVD contents after tray close. This is usefull for a headless
computer that you want to use to copy lots of optical disks to a hard drive.
This will only work on a Linux machine. I used a fedora 22 server when I developed it, but it
should work on any Linux distro that has python, HandBrakeCLI and abcde. Note that the latter
two are 
usually not provided in the standard repos, but are available in some additional repo. Google
will be your friend.

## Requirements
Requirements are currently not retrieved automatically, but you are responsible to install
them on your system. For a list of requirements, please check `requirements.txt`.

## Setup
Use the provided installer to install all the files on your system:

    sudo ./setup.sh install

Similarly, you can get rid of everything:

    sudo ./setup.sh remove

## Configuration
After installation, there will be a configuration file on your system, `/etc/auto_copy.yml`. 
As the name suggests, the syntax is yaml. Most options should be described in detail 
within the comments, so I won't describe them here.

Note that abcde, the tool used to rip audio CDs, has its own commented configuration file at 
`/etc/abcde.conf`. Most usefull to me were the paramters `OUTPUTDIR` and `OUTPUTTYPE`. But
there are a lot more, have a look.

In June 2020 freedb.org stopped its service. At least for older installations of abcde,
freedb.org is the default cddb database. Alternatives exist, but need to be configured
if not already done. In `/etc/abcde.conf`, set e.g.

    CDDBURL="http://gnudb.gnudb.org/~cddb/cddb.cgi"


## How it works
The script `auto_copy.py` will distinguish between data disks, audio CDs and video DVDs.
The contents of data disks (files larger then a configurable size) will be
copied to a configurable directory.
Video DVDs will be ripped with HandBrakeCLI, so you will need to install
that too.
Audio CDs will be ripped using abcde (which in turn uses a bunch of other tools).

While `auto_copy.py` is the core worker involved here, there is quite a bit of stuff around
it nessessary to make it work as a daemone that is triggered via insertion of an optical disk.

First, there is `auto_copy_daemon.py`, which is run as a systemd service (`autocopy.service`).
It receives a signal (`send_siguser1.sh`) from udev uppon insertion (`autodvd.rules`). Since udev fires not only
when the tray is closed, but also when it opens, we need to distinghuish between open and close.
Therefore we need a small custom binary, `trayopen`. I did some research, but it seems there is
no standard tool for that task, so I took the liberty to copy/paste some C code from a forum.

That is basically it.

If you like to use this and need help setting things up, or have any questions or comments, feel free to 
contact me at isaac.hailperin@gmail.com.

Happy ripping.

## Known Issues
A while ago I did an attempt at extracting dvd titles automatically. I have added the code,
even though it does not work yet. I might work on this in the future.
