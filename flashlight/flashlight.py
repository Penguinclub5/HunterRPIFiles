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
previous_button_state = GPIO.input(BUTTON_0_PIN)

try:
    while True:
        #these examples were buns to figure out
        current_button_state = GPIO.input(BUTTON_0_PIN)

        if current_button_state == GPIO.HIGH and previous_button_state == GPIO.LOW:
            led_state = not led_state
        else:
            pass
        
        if led_state == True:
            GPIO.output(LED_0_PIN, GPIO.HIGH)
        else:
            GPIO.output(LED_0_PIN, GPIO.LOW)

        previous_button_state = current_button_state
        time.sleep(0.01)

#Code copied over from lab manual
except KeyboardInterrupt:
    print("Got Keyboard Interrupt. Cleaning up and exiting")
    GPIO.output(LED_0_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit()