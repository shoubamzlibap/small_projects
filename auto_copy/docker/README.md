# What can be found here?
Currently I run handbrake via docker, because there are up to date binaries for Ubuntu,
but my box runs CentOS. So I use handbrake inside a container.

Here I provide the Dockerfile I used to create the container, and the script used
to call the container.

You can use the script - copy it to /bin and make it executable. Make sure you adjust
the mounted volumes to reflect your enviroment.
