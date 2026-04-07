import RPi.GPIO as GPIO
import time 
import sys
import spidev

device = 0
bus = 0
vref
channel = 0
# Enable SPI
spi = spidev.SpiDev()
spi.open(bus, device)
spi.max_speed_hz = 100000

def read_adc(channel):
    tx = [0x06 | ((channel & 0x04) >> 2), (channel & 0x03) << 6, 0x00]
    rx = spi.xfer(tx)
    value = ((rx[1] & 0x0F) << 8) | rx[2]

    return value

try: 
    while True:
        raw_value = read_adc(channel)
        voltage = (raw_value/4095.0)*vref
        print('voltage: {voltage:.4f} V')
        time.sleep(1)



except KeyboardInterrupt:
    print("Got Keyboard Interrupt. Cleaning up and exiting")
    GPIO.output(LED_0_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit()
