
import time
import sys
import paho.mqtt.client as mqtt
# this callback runs once when the client connects with the broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    print('Subscribing to topic ', sub_topic_name)
    client.subscribe(sub_topic_name)
# this callback runs whenever a message is received
def on_message(client, userdata, msg):
    fan_rpm_value = (float(msg.payload))
    print('Fan RPM Value = ', fan_rpm_value)
# Read command line arguments and set the publish and subscribe topic names
# based on the command line arguments
numArgs = len(sys.argv)
my_name = sys.argv[1]
pub_topic_name = my_name + '/command_center/desired_speed'
partner_name = sys.argv[2]
sub_topic_name = partner_name + '/mqtt_fan/fan_rpm_value'

# Initialize MQTT and connects to the broker
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.emqx.io", 1883, 60)
client.loop_start()

try:
    while True:
        desired_speed = (float(input("Enter desired Fan Speed (0.0 to 100.0): ")))
        if desired_speed < 0.0:
            print('ERROR: Desired speed below 0.0')
        elif desired_speed > 100.0:
            print('ERROR: Desired speed above 100.0')
        else:
            client.publish(pub_topic_name, payload=desired_speed, qos=0, retain=False)
        time.sleep(1)

except KeyboardInterrupt:
    print('Got Keyboard Interrupt. Cleaning up and exiting')
    sys.exit()
