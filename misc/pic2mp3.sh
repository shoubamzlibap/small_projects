#!/bin/bash

# check if there is a .jpg in a folder of mp3
# If so, set it as cover pic

#add picture if present
picture=$(ls *.jpg *.JPG *.jpeg 2>/dev/null |tail -1)
if [ ! -f ${picture} ]; then
    echo "[INFO] did not find a picture in the current folder(${album_dir}) - no album art will be set."
    continue
fi
for i in *.mp3; do
    eyeD3 --add-image="${picture}":FRONT_COVER "${i}"
done

