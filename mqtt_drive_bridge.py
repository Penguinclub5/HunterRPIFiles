#!/usr/bin/python3
# coding=utf-8

from __future__ import annotations

import json
import socket
import time
from typing import Callable, Final

try:
    import paho.mqtt.client as mqtt
except ImportError as exc:
    raise RuntimeError(
        "paho-mqtt is required. Install with: pip install paho-mqtt"
    ) from exc


DEFAULT_BROKER_HOST: Final[str] = "192.168.6.168"
DEFAULT_BROKER_PORT: Final[int] = 1883
DEFAULT_PUBLISH_HZ: Final[float] = 40.0


COMMAND_TO_DRIVE_FUNCTION: Final[dict[str, str]] = {
    "MOVE_FORWARD": "forward",
    "MOVE_BACKWARD": "backward",
    "TURN_LEFT": "rotate_counterclockwise",
    "TURN_RIGHT": "rotate_clockwise",
    "STOP": "stop",
}


COMMAND_TO_ARM_FUNCTION: Final[dict[str, str]] = {
    "PICKUP": "pickup_sequence",
    "DUNK": "dunk_sequence",
}


DEFAULT_EMULATED_COMMANDS: Final[tuple[str, ...]] = (
    "PICKUP",
    "DUNK",
    "STOP",
    "MOVE_FORWARD",
    "MOVE_BACKWARD",
    "TURN_LEFT",
    "TURN_RIGHT",
)


# ------------------------------------------------------------
# MQTT callback functions
# Fan-lab style
# ------------------------------------------------------------

def on_connect(client, userdata, flags, rc):
    publisher = userdata

    if rc == 0:
        publisher.connected = True

        print(f"Connected with result code {rc}")
        print("Publishing drive commands to", publisher.drive_function_topic)
        print("Publishing arm commands to", publisher.arm_function_topic)
        print("Publishing status to", publisher.status_topic)

    else:
        print(f"MQTT connect failed with result code {rc}")


def on_message(client, userdata, msg):
    message = msg.payload.decode(errors="ignore")
    print(f"Received message on {msg.topic}: {message}")


def on_disconnect(client, userdata, rc):
    publisher = userdata
    publisher.connected = False
    print(f"MQTT disconnected with result code {rc}")


# ------------------------------------------------------------
# MQTT publisher class
# ------------------------------------------------------------

class MqttDrivePublisher:
    def __init__(
        self,
        client_id: str,
        source: str,
        my_name: str,
        partner_name: str,
        broker_host: str = DEFAULT_BROKER_HOST,
        broker_port: int = DEFAULT_BROKER_PORT,
    ) -> None:
        self.source = source
        self.my_name = my_name
        self.partner_name = partner_name

        self.broker_host = broker_host
        self.broker_port = broker_port

        # Fan-lab style topic naming.
        #
        # If host runs:
        #   python3 app/main_pi.py host robot 192.168.6.168
        #
        # Then:
        #   my_name = host
        #   partner_name = robot
        #
        # Host publishes to:
        #   host/robot/drive/function
        #   host/robot/arm/function
        #   host/robot/drive/status
        self.drive_function_topic = f"{my_name}/{partner_name}/drive/function"
        self.arm_function_topic = f"{my_name}/{partner_name}/arm/function"
        self.status_topic = f"{my_name}/{partner_name}/drive/status"

        self.connected = False

        self.client = mqtt.Client(client_id=client_id)
        self.client.user_data_set(self)

        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.on_disconnect = on_disconnect

    @staticmethod
    def build_envelope(source: str) -> dict[str, float | str]:
        return {
            "timestamp": time.time(),
            "source": source,
        }

    @staticmethod
    def strength_to_speed(strength: float) -> int:
        return int(max(0, min(100, round(abs(strength) * 100))))

    @staticmethod
    def map_to_function_call(command: str, strength: float):
        if command in COMMAND_TO_DRIVE_FUNCTION:
            function_name = COMMAND_TO_DRIVE_FUNCTION[command]

            payload = {
                "function": function_name,
                "args": [],
                "kwargs": {
                    "speed": MqttDrivePublisher.strength_to_speed(strength),
                },
                "command": command,
            }

            if function_name == "stop":
                payload["kwargs"] = {}

            return "drive", payload

        if command in COMMAND_TO_ARM_FUNCTION:
            payload = {
                "function": COMMAND_TO_ARM_FUNCTION[command],
                "args": [],
                "kwargs": {},
                "command": command,
            }

            return "arm", payload

        return None, None

    def publish_json(
        self,
        topic: str,
        payload: dict,
        qos: int = 1,
        retain: bool = False,
    ) -> None:
        message = json.dumps(payload)

        result = self.client.publish(
            topic,
            payload=message,
            qos=qos,
            retain=retain,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(
                f"MQTT publish failed for topic '{topic}' with rc={result.rc}"
            )

    def connect(self) -> None:
        print(f"Connecting to MQTT broker {self.broker_host}:{self.broker_port}")

        try:
            self.client.connect(self.broker_host, self.broker_port, 60)

        except socket.gaierror as error:
            raise RuntimeError(
                f"MQTT broker hostname could not be resolved: {self.broker_host}"
            ) from error

        self.client.loop_start()

        deadline = time.monotonic() + 5.0

        while not self.connected and time.monotonic() < deadline:
            time.sleep(0.05)

        if not self.connected:
            raise RuntimeError("Timed out waiting for MQTT connection.")

        self.publish_json(
            self.status_topic,
            {
                "status": "online",
                **self.build_envelope(self.source),
            },
            qos=1,
            retain=True,
        )

    def publish_drive_command(self, command: str, strength: float) -> None:
        call_target, function_payload = self.map_to_function_call(
            command,
            float(strength),
        )

        if call_target is None or function_payload is None:
            return

        envelope = self.build_envelope(self.source)

        if call_target == "drive":
            topic = self.drive_function_topic
        else:
            topic = self.arm_function_topic

        self.publish_json(
            topic,
            {
                **function_payload,
                **envelope,
            },
            qos=1,
        )

    def disconnect(self) -> None:
        self.publish_json(
            self.status_topic,
            {
                "status": "offline",
                **self.build_envelope(self.source),
            },
            qos=1,
            retain=True,
        )

        self.client.loop_stop()
        self.client.disconnect()


def bind_default_commands(
    register_command: Callable[[str, Callable[[str, float], None]], None],
    callback: Callable[[str, float], None],
) -> None:
    for command_name in DEFAULT_EMULATED_COMMANDS:
        register_command(command_name, callback)
