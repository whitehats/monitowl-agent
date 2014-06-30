#!/bin/bash
HERE=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
git clone git://git.drogon.net/wiringPi
cd "$HERE/wiringPi"
./build
cd "$HERE"
gcc -o ./dht11 ./dht11.c -L/usr/local/lib -lwiringPi

