import time
import sys
import os

sys.path.insert(0, '../utilities')
import utilities

pwm = utilities.HW_PWM(25000)
pwm.set_duty_cycle(100.0)
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