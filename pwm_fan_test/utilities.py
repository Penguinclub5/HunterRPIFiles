#Nathan Hunter RPilab2

import time
import sys
import os

PWM_PATH = "/sys/class/pwm/pwmchip0"

class HW_PWM:
    def __init__(self, frequency):
        self.frequency = frequency
        self.period = int(1000000000 / frequency)
        self.duty_cycle_percent = 0
        self.duty_cycle = 0
        export_cmd = "echo 0 > " + PWM_PATH + "/export"
        enable_cmd = "echo 1 > " + PWM_PATH + "/pwm0/enable"
        print('Create PWM0')
        print(export_cmd)
        os.system(export_cmd)
        time.sleep(0.5)

        print('Set the period')
        period = int(1000000000 / frequency)
        period_cmd = "echo " + str(period) + " > " + PWM_PATH + "/pwm0/period"
        ##print(period_cmd)
        os.system(period_cmd)
        time.sleep(0.5)

        print('Set duty cycle to 0')
        duty_cycle_cmd = "echo 0 > " + PWM_PATH + "/pwm0/duty_cycle"
        #print(duty_cycle_cmd)
        os.system(duty_cycle_cmd)
        time.sleep(0.5)

        print('Enable PWM0')
        print(enable_cmd)
        os.system(enable_cmd)
        time.sleep(0.5)

    def set_duty_cycle(self, duty_cycle_percent):
    #TODO: Complete this function
        if duty_cycle_percent > 100:
            duty_cycle_percent = 100
        if duty_cycle_percent < 0:
            duty_cycle_percent = 0
        self.duty_cycle_percent = duty_cycle_percent
        self.duty_cycle = int((duty_cycle_percent*self.period)/100.0)

        #this is the stuff to change the duty cycke being sent to the os
        duty_cycle_cmd = "echo " + str(self.duty_cycle) + " > " + PWM_PATH + "/pwm0/duty_cycle"
        os.system(duty_cycle_cmd)