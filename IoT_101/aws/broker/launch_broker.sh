#!/bin/bash

# Create cloud bridge network
docker network create --driver bridge iot101

# Build the docker image based on the broker Dockerfile
docker build -t broker -f Dockerfile.cloudbroker .

# launch
docker run -d --network iot101 --name broker -p 1883:1883 -ti broker mosquitto -v
