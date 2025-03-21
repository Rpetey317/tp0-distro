FROM ubuntu:latest

RUN apt-get update -qq && apt-get install -qq netcat-traditional > /dev/null 2>&1

COPY test-server/netcat_test.sh /netcat_test.sh

ENTRYPOINT ["/bin/bash"]