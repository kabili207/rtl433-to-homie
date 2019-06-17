#!/bin/sh
if [ -z "${PROTOCOLS// }" ]; then
    protocols="-G"
else
    protocols=`echo $PROTOCOLS | awk 'BEGIN { RS=","; FS="-"; ORS="" }
    NF > 1  { for (i=$1; i<=$2; ++i) { print "-R " i " "} next }
            { print "-R " $1 " " }'`
fi

rtl_433 -F json -M time:off -M level -M protocol -M newmodel $protocols | python rtl433-to-homie.py
