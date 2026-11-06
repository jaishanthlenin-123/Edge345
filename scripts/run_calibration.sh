#!/usr/bin/env bash
# Runs sensor calibration and electrical health check
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

python3 raspberry_pi/sensor_calibration.py
