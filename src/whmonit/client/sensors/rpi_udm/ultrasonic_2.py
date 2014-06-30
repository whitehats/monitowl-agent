#!/usr/bin/python
'''Ultrasonic Distance Meter.'''

import time
import RPi.GPIO as GPIO


def do_it():
    '''Get data from sensor.'''
    # Use BCM GPIO references
    # instead of physical pin numbers
    GPIO.setmode(GPIO.BCM)

    # Define GPIO to use on Pi
    GPIO_TRIGGER = 23
    GPIO_ECHO = 24

    # Set pins as output and input
    GPIO.setup(GPIO_TRIGGER, GPIO.OUT)  # Trigger
    GPIO.setup(GPIO_ECHO, GPIO.IN)      # Echo

    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
    start = time.time()

    while GPIO.input(GPIO_ECHO) == 0:
        start = time.time()

    while GPIO.input(GPIO_ECHO) == 1:
        stop = time.time()

    elapsed = stop - start
    distance = (elapsed * 34300) / 2

    # Set trigger to False (Low)
    GPIO.output(GPIO_TRIGGER, False)

    GPIO.cleanup()
    if 4 < distance < 300:
        return distance
    return 0.0

if __name__ == '__main__':
    print do_it()
