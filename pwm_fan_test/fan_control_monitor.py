#Nathan Hunter Pi_Lab3
    
import time
import os
import sys
import RPi.GPIO as GPIO

sys.path.insert(0, '../utilities') #pulled from led_dimmer
import utilities

SENSE_PIN = 16
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SENSE_PIN, GPIO.IN)

pwm = utilities.HW_PWM(25000)
pwm.set_duty_cycle(100.0)

with open("rpm_value_file.txt", "w") as fileName:
    fileName.write('')

past = time.time_ns()
count = 1
ListRPM = []

def tachometer_callback(SENSE_PIN):
    global count
    global past
    global ListRPM
    global current

    current = time.time_ns()
    if current != past:
        period = (current - past) * 1e-9
        freq = 1 / period
        RPM = (freq * 60) / 2
        ListRPM.append(RPM)

        if (count != 10):
            count = count + 1

        elif (count == 10):
            with open("rpm_value_file.txt", "a") as fileName:
                Average = sum(ListRPM) / 10
                fileName.write(str(Average))
                fileName.write("\n")
            
            ListRPM.clear()
            count = 1
        
        past = current
        
GPIO.add_event_detect(SENSE_PIN, GPIO.FALLING, callback = tachometer_callback, bouncetime = 10)



try:
    while True:
        pwm_value = float(input("Enter desired PWM Duty Cycle (0.0 to 100.0): "))
        pwm.set_duty_cycle(pwm_value)
        if pwm_value < 0.0:
            print('ERROR: Duty cycle below 0.0')
        if pwm_value > 100.0:
            print('ERROR: Duty cycle below 100.0')
        time.sleep(.01)

except KeyboardInterrupt:
    print('Got Keyboard Interrupt. Cleaning up and exiting')
    pwm.set_duty_cycle(100.0)
    sys.exit()