#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Please run with sudo"
    exit
else
    cp view.py /usr/bin/ctbb_view
    chmod +x /usr/bin/ctbb_view
fi
