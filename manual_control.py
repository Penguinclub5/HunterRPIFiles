#!/usr/bin/python3
# coding=utf-8

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Callable


# Keep script/module runnable from either repo root or app/ directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from subsystems.remote.live_visual_emulator import LiveRemoteAPIEmulator
from subsystems.remote.mqtt_drive_bridge import (
    DEFAULT_PUBLISH_HZ,
    MqttDrivePublisher,
    bind_default_commands,
)


def run_manual_control(
    is_manual_mode: Callable[[], bool],
    my_name: str,
    partner_name: str,
    broker_host: str,
) -> None:
    emulator = LiveRemoteAPIEmulator()

    publisher = MqttDrivePublisher(
        client_id=f"{my_name}-manual-control",
        source=f"{my_name}-manual",
        my_name=my_name,
        partner_name=partner_name,
        broker_host=broker_host,
    )

    def forward_command(command_name: str, strength: float) -> None:
        publisher.publish_drive_command(command_name, strength)

    bind_default_commands(emulator.on_command, forward_command)

    publisher.connect()
    emulator.start()

    try:
        while is_manual_mode():
            emulator.poll()
            time.sleep(1.0 / DEFAULT_PUBLISH_HZ)

    finally:
        # Tell the robot to stop if the controller exits.
        publisher.publish_drive_command("STOP", 1.0)
        emulator.stop()
        publisher.disconnect()
