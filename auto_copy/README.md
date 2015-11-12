# auto_copy
Automatically copy CD/DVD contents after tray close. This is usefull for a headless
computer that you want to use to copy lots of optical disks to a hard drive.

The script auto_copy.py will distinguish between data disks and video DVDs.
The contents of data disks (files larger then a configurable size) will be
copied to a configurable directory.
Video DVDs will be ripped with HandBrakeCLI, so you will need to install
that too.

# Setup
For now this is very rudimentary and not very userfriendly, but the relevant
intormation should be there.

Have a look at the first few lines of auto_copy.py - there you will find an
example for a udev rule that will trigger the script. Put it in a file with a .rule
extension in /etc/udev/rules.d. Reboot or reload the udev config with 'udevadm control --reload'.

The script also needs to determine if the tray is open or closed (as this is not
determined by udev - udev just notices changes). Therefor a small C programm is
provided called trayopen. Use the binary from this repo or compile it from source.
Have a look at the source on how to do this. You must put the binary in /usr/local/bin
and make sure it is executable.
