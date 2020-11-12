#!/bin/bash
docker run --name mongo -d -p 27017:27017 mongo:latest || docker container start $(docker ps -a | grep 'mongo:latest' | grep -o "^[0-9a-f]*")
