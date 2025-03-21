#!/bin/bash

if ! docker compose ps | grep -q "server.*running"; then
    echo "Starting server..."
    docker compose up -d server
    sleep 2
else
    echo "Server already running"
fi

docker compose run --rm test bash -c "$(cat netcat_test.sh)"
TEST_RESULT=$?

# Report result in required format
if [ $TEST_RESULT -eq 0 ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi

docker compose down -t 0 > /dev/null 2>&1 