#!/bin/bash
# installer script for audio_output

SCRIPT=audio_output
BIN_PATH=/usr/local/bin
DESKTOP_APP_PATH=/usr/share/applications

usage() {
echo "usage: sudo ./install.sh [-r|--remove] [-h|--help]"
echo "Without any options, this will install audio_control."
echo
echo "-r --remove:  remove installed files"
echo "-h --help:    display this message."
exit 0
}

install() {
cp "${SCRIPT}" "${BIN_PATH}"
chmod 755 "${BIN_PATH}"/"${SCRIPT}"
cp "${SCRIPT}".desktop "${DESKTOP_APP_PATH}"
chmod 644 "${DESKTOP_APP_PATH}"/"${SCRIPT}".desktop
exit 0
}

remove() {
rm "${BIN_PATH}"/"${SCRIPT}"
rm "${DESKTOP_APP_PATH}"/"${SCRIPT}".desktop
exit 0
}

case $1 in
    -h|--help) usage;;
    -r|--remove) remove;;
    *) install
esac

exit 0
