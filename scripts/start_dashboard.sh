#!/usr/bin/env bash
# Launches the Servo Condition Monitoring Dashboard on Raspberry Pi 5
PORT=${1:-8000}
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "======================================================================"
echo " Starting Servo Condition Monitoring Dashboard on Port $PORT..."
echo " URL: http://localhost:$PORT"
echo "======================================================================"
python3 raspberry_pi/dashboard/server.py "$PORT"
