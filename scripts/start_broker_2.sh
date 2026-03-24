#!/bin/bash
echo "Starting Broker 2 (localhost:5002) - Follower"
# Add the -u flag for unbuffered output
python3 -u -m broker.main 2 localhost:5002 localhost:5001