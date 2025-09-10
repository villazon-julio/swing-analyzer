#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/juliovillazon/.Xauthority
exec >> /tmp/golf_autostart_debug.log 2>&1
set -x

# Wait 30 seconds after boot
sleep 30

# Check for connected Bluetooth audio devices
BT_CONNECTED=$(bluetoothctl info | grep "Connected: yes")

if [ -z "$BT_CONNECTED" ]; then
    # No Bluetooth device connected, run the golf analyzer
    /home/juliovillazon/Documents/Projects/swing-analyzer/run_golf.sh
fi