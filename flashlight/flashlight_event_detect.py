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


def button_callback(channel):
    GPIO.output(LED_0_PIN, GPIO.HIGH)
    print("In rising edge callback")
    while GPIO.input(BUTTON_0_PIN) == GPIO.HIGH:
        print("abc")
        time.sleep(0.1)

    GPIO.output(LED_0_PIN, GPIO.LOW)
    print("Leaving edge callback")
GPIO.add_event_detect(BUTTON_0_PIN, GPIO.RISING, button_callback, bouncetime = 10)


c = 0
try:  
    while True:
        time.sleep(1)
        print(c)
        c = c + 1
    
except KeyboardInterrupt:
    print("Got Keyboard Interrupt. Cleaning up and exiting")
    GPIO.output(LED_0_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit()