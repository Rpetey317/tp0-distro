#!/bin/bash

echo "Installing netcat..."
apt-get update -qq && apt-get install -qq netcat-traditional > /dev/null 2>&1

echo "Sending test message..."
RESPONSE=$(echo "Test message" | nc server 12345)

# Check if response matches sent message
if [ "$RESPONSE" = "Test message" ]; then
    echo "Test successful"
    exit 0
else
    echo "Test failed"
    exit 1
fi