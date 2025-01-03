#!/bin/sh

if [ -z $SAMBA_PATH ]; then
    echo "samba creds not provided, skip mounting"
else
    mkdir -p $RECORDINGS_MOUNT_POINT
    mount -t cifs -o username=$SAMBA_USERNAME,password=$SAMBA_PASSWORD,iocharset=utf8 $SAMBA_PATH $RECORDINGS_MOUNT_POINT
fi

python src/main.py
