#!/bin/bash

echo "Installing netcat..."
apk add --no-cache --quiet netcat-openbsd > /dev/null 2>&1

MESSAGE="lorem ipsum dolor sit amet"

echo "Sending test message: $MESSAGE"
RESPONSE=$(echo "$MESSAGE" | nc -v server.tp0_testing_net 12345)
echo "Received response: $RESPONSE"

# Check if response matches sent message
if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "Test successful"
    exit 0
else
    echo "Test failed"
    exit 1
fi