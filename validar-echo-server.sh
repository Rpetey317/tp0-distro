#!/bin/bash

echo "Starting server..."
make docker-compose-up
sleep 2

echo "Running test..."
docker compose -f docker-compose-dev.yaml run --rm test bash -c "$(cat test-server/netcat_test.sh)"

TEST_RESULT=$?

# Report result in required format
if [ $TEST_RESULT -eq 0 ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi

make docker-compose-down