#LAb 1, Nathan Hunter
#3/31/2026

import RPi.GPIO as GPIO
import time #needed from example code copied over
import sys #needed from example code copied over

BUTTON_0_PIN = 16
LED_0_PIN = 18

#Honestly 90% of the difficulty here
GPIO.setmode(GPIO.BOARD) 
GPIO.setup(BUTTON_0_PIN, GPIO.IN)
GPIO.setup(LED_0_PIN, GPIO.OUT)
GPIO.output(LED_0_PIN, GPIO.LOW)

led_state = False

try:
    while True:
        #THIS IS SO NICE, I love python though boucetime is kinda confusing
        GPIO.wait_for_edge(BUTTON_0_PIN, GPIO.RISING, bouncetime = 10)
        led_state = not led_state

        if led_state == True:
            GPIO.output(LED_0_PIN, GPIO.HIGH)
        else:
            GPIO.output(LED_0_PIN, GPIO.LOW)

#Code copied over from lab manual
except KeyboardInterrupt:
    print("Got Keyboard Interrupt. Cleaning up and exiting")
    GPIO.output(LED_0_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit()
