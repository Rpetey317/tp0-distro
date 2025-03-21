#!/bin/bash

if ! docker compose -f docker-compose-dev.yaml ps | grep -q "server"; then
    echo "Starting server..."
    docker compose -f docker-compose-dev.yaml up -d server
    sleep 2
else
    echo "Server already running"
fi

echo "Running test..."
docker compose -f docker-compose-dev.yaml up -d test"

TEST_RESULT=$?

# Report result in required format
if [ $TEST_RESULT -eq 0 ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi

echo "Cleaning up..."
docker compose -f docker-compose-dev.yaml down -t 0 > /dev/null 2>&1
