# pa_scripts
A small pseudo gui to help set the pulseaudio output device.

## Installation
Run `sudo ./install.sh` to install the script and desktop icon. 
It should then show up in your applications menue.
Run `sudo ./install.sh -r` to remove the installed files again.

## Configuration
In `/usr/local/bin/audio_output`, set the variable 

    REMOTE_PA_SERVER=foobar

to your remote
pulseaudio server that should recieve your audio output.

