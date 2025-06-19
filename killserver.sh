#!/bin/bash
# Script to kill Django development server
echo "Searching for Django runserver processes..."
pids=$(ps aux | grep "[p]ython.*runserver" | awk '{print $2}')

if [ -z "$pids" ]; then
    echo "No Django runserver processes found."
    exit 0
else
    echo "Found Django runserver processes with PIDs: $pids"
    echo "Killing processes..."
    for pid in $pids; do
        echo "Killing process $pid"
        kill -9 $pid
    done
    echo "All Django runserver processes have been terminated."
fi

# Double check if any processes remain
remaining=$(ps aux | grep "[p]ython.*runserver" | awk '{print $2}')
if [ -n "$remaining" ]; then
    echo "Warning: Some processes may still be running: $remaining"
    echo "You may need to kill them manually or run this script again."
else
    echo "Success: No more Django runserver processes found."
fi
