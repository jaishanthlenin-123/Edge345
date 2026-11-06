#!/usr/bin/env bash
# Collects structured telemetry dataset
MODE=${1:-normal}
DURATION=${2:-60}
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

python3 raspberry_pi/data_logger.py --mode "$MODE" --duration "$DURATION"
