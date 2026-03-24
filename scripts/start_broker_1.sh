#!/bin/bash
echo "Starting Broker 1 (localhost:5001) - Initial Leader Candidate"
# Add the -u flag for unbuffered output
python3 -u -m broker.main 1 localhost:5001 localhost:5002