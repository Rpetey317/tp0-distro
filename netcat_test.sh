#!/bin/bash

echo "Installing netcat..."
apk add --no-cache --quiet netcat-openbsd > /dev/null 2>&1

echo "Sending test message..."
RESPONSE=$(echo "Test message" | nc -v server.tp0_testing_net 12345)

# Check if response matches sent message
if [ "$RESPONSE" = "Test message" ]; then
    echo "Test successful"
    exit 0
else
    echo "Test failed"
    exit 1
fi