#Nathan Hunter RPilab2


import RPi.GPIO as GPIO
import time
import spidev
import os
import sys
sys.path.insert(0, '../utilities') #pulled from led_dimmer
import utilities

#setup button to pin 16 on RPi
BUTTON_0_PIN = 16
GPIO.setmode(GPIO.BOARD) 
GPIO.setup(BUTTON_0_PIN, GPIO.IN)

#again just stole this from my adc_test from before
device = 0
bus = 0
vref = 3.3
channel = 0
# Enable SPI
spi = spidev.SpiDev()
spi.open(bus, device)
spi.max_speed_hz = 100000



def read_adc():

    byte1 = 0b00000110 #go back and double check why bit 2 is a '1', just took it from my adc_test
    byte2 = 0b00000000
    byte3 = 0b00000000
    value = [byte1, byte2, byte3]
    ret = spi.xfer(value)
    new_val = (ret[1] << 8) | (ret[2])

    return new_val

def wait_for_press():
    GPIO.wait_for_edge(BUTTON_0_PIN, GPIO.RISING, bouncetime = 10) #dontwork#broke
    time.sleep(0.2)

def comp(val, low, high):
    if val < low:
        return low
    if val > high:
        return high
    return val


pwm = utilities.HW_PWM(2000)
try: 
    pwm.set_duty_cycle(0.0) #read the covered photosensor
    print("Cover the photosensor then press the push button")
    wait_for_press()
    dark = read_adc()
    time.sleep(0.5)

    #read the illuminated photosensor
    print("Shine a flashlight on the photosensor and press the push button")
    wait_for_press()
    light = read_adc()
    time.sleep(0.5)

    print("Calibration complete")

    while True:
        sense = read_adc()
        sense = comp(sense, dark, light)
        if dark > light:
            duty_cycle = ((sense - light) / (dark - light)) * 100.0
        else:
            duty_cycle = ((light - sense) / (light - dark)) * 100.0

        duty_cycle = comp(duty_cycle, 0.0, 100.0)
        pwm.set_duty_cycle(duty_cycle) #set duty cycle to determine led state

        time.sleep(0.001)

except KeyboardInterrupt: #we all know
    print("Got Keyboard Interrupt. Cleaning up and exiting")
    GPIO.output(LED_0_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit()






