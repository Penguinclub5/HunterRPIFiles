#!/usr/bin/python3
# coding=utf-8

"""
mqtt_remote_receiver.py

Receives RemoteEvent MQTT messages from controller Raspberry Pi
and converts them into robot commands.

Usage:
    python3 mqtt_remote_receiver.py <my_name> <partner_name>

Example:
    python3 mqtt_remote_receiver.py robotpi controllerpi
"""

from __future__ import annotations

import sys
import json
import time
import paho.mqtt.client as mqtt


# =========================
# TOPIC SETUP
# =========================
if len(sys.argv) < 3:
    print("Usage:")
    print("python3 mqtt_remote_receiver.py <my_name> <partner_name>")
    sys.exit(1)

my_name = sys.argv[1]
partner_name = sys.argv[2]

# Subscribe to controller events
sub_topic_name = partner_name + "/controller/remote_events"

# Publish robot status back
pub_topic_name = my_name + "/robot/status"


# =========================
# ROBOT CONTROL PLACEHOLDERS
# Replace these with your real subsystem imports
# =========================
def move_forward(speed: float):
    print(f"[ROBOT] Moving forward at speed {abs(speed):.2f}")


def move_backward(speed: float):
    print(f"[ROBOT] Moving backward at speed {abs(speed):.2f}")


def turn_left(amount: float):
    print(f"[ROBOT] Turning left {abs(amount):.2f}")


def turn_right(amount: float):
    print(f"[ROBOT] Turning right {abs(amount):.2f}")


def stop_robot():
    print("[ROBOT] STOP")


def pickup():
    print("[ROBOT] PICKUP")


def dunk():
    print("[ROBOT] DUNK")


# =========================
# MQTT CALLBACKS
# =========================
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    print(f"[MQTT] Subscribing to topic: {sub_topic_name}")
    client.subscribe(sub_topic_name)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        event_type = payload.get("event_type")
        control = payload.get("control")
        value = payload.get("value")

        print(f"[MQTT] Received: {payload}")

        # =========================
        # BUTTON COMMANDS
        # =========================
        if event_type == "button_down":
            if control == "button_0":
                pickup()

            elif control == "button_1":
                dunk()

            elif control == "button_2":
                stop_robot()

        # =========================
        # AXIS COMMANDS
        # =========================
        elif event_type == "axis_motion":
            # Left stick horizontal
            if control == "axis_0":
                if value > 0.45:
                    turn_right(value)
                elif value < -0.45:
                    turn_left(value)

            # Left stick vertical
            elif control == "axis_1":
                if value < -0.45:
                    move_forward(value)
                elif value > 0.45:
                    move_backward(value)
                else:
                    stop_robot()

        # =========================
        # Publish robot status
        # =========================
        client.publish(
            pub_topic_name,
            payload=json.dumps({
                "last_control": control,
                "last_value": value,
                "timestamp": time.time()
            }),
            qos=0,
            retain=False
        )

    except Exception as exc:
        print(f"[MQTT ERROR] {exc}")


# =========================
# MAIN
# =========================
def main():
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect("broker.emqx.io", 1883, 60)

    except Exception as exc:
        print(f"[MQTT ERROR] Could not connect to broker: {exc}")
        sys.exit(1)

    client.loop_start()

    print("[ROBOT] Receiver running... Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[ROBOT] Keyboard interrupt received. Shutting down...")

    finally:
        client.loop_stop()
        client.disconnect()
        print("[MQTT] Disconnected")


if __name__ == "__main__":
    main()
