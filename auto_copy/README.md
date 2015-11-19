# auto_copy
Automatically copy CD/DVD contents after tray close. This is usefull for a headless
computer that you want to use to copy lots of optical disks to a hard drive.
This will only work on a Linux machine. I used a fedora 22 server when I developed it, but it
should work on any Linux distro that has python and HandBrakeCLI. Note that the latter is
usually not provided in the standard repos, but is available in some additional repo. Google
will be your friend.

The script auto_copy.py will distinguish between data disks and video DVDs.
The contents of data disks (files larger then a configurable size) will be
copied to a configurable directory.
Video DVDs will be ripped with HandBrakeCLI, so you will need to install
that too.

## Setup
For now this is very rudimentary and not very userfriendly, but the relevant
intormation should be there.

### auto_copy.py
Put the script somewhere on your system, possibly where you have access as a normal user as you
might want to adapt some settings from time to time. I use `/home/isaac/bin/auto_copy.py`.
Adapt it to your needs, and make sure you put that path in the udev rule described below.

### udev
Deploy the following udev rule (adapt to your local system)

    SUBSYSTEM=="block", KERNEL=="sr0", ACTION=="change", RUN+="/home/isaac/bin/auto_copy.py"

Put this in a file called /etc/udev/rules.d/auto_copy.rule (or whatever name suits you).  Reboot or reload the udev config with `udevadm control --reload`.

### trayopen
The script also needs to determine if the tray is open or closed (as this is not
determined by udev - udev just notices changes). Unfortunatly there is no standard
tool on Linux to determine this.

Therefor a small C programm is
provided called `trayopen`. Use the binary from this repo or compile it from source which is
also provided here (`trayopen.c`).
You must put the binary in `/usr/local/bin` and make it executable:

    gcc -o trayopen trayopen.c
    sudo cp trayopen /usr/local/bin
    sudo chmod 755 /usr/local/bin/trayopen

### HandBrakeCLI
You will need HandBrakeCLI installed on your system. Use google to find out how to install
HandBrakeCLI on your linux distribution.
