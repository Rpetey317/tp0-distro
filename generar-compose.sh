#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Error: Wrong number of arguments"
    echo "Usage: $0 <filename> <num_clients>"
    exit 1
fi

unzip ./.data/dataset.zip -o -d ./.data
python3 generate_compose.py $1 $2