import RPi.GPIO as GPIO
import time 
import sys
import spidev

device = 0
bus = 0
vref = 3.3
channel = 0
# Enable SPI
spi = spidev.SpiDev()
spi.open(bus, device)
spi.max_speed_hz = 10000

byte1 = 0b00000110
byte2 = 0b00000000
byte3 = 0b00000000

try: 
    while True:
        to_send = [byte1, byte2, byte3]
        returnVal = spi.xfer(to_send)
        adcVal = (returnVal[1] << 8) | (returnVal[2])
        print(adcVal)
        voltage = adcVal * 3.3 / 4095.0
        print(voltage)
        time.sleep(1)
        #value = [byte1, byte2, byte3]
        #ret = spi.xfer(value)
        #new_val = (ret[1] << 8) | (ret[2])
        #voltage = (new_val/4095.0)*vref
        #print(new_val)
        #print(voltage)
        #time.sleep(1)



except KeyboardInterrupt:
    print("Got Keyboard Interrupt. Cleaning up and exiting")
    GPIO.cleanup()
    sys.exit()
