# =========================
# FILE: subsystems/remote/controller_api.py
# FULL MQTT-ENABLED VERSION
# =========================

#!/usr/bin/python3
# coding=utf-8

from __future__ import annotations

import dataclasses
import threading
import time
import json
from collections import deque
from typing import Callable, Deque, Dict, Iterable, Optional, Tuple

try:
    import pygame
except ImportError as exc:
    raise RuntimeError(
        "pygame is required for controller input. Install with: pip install pygame"
    ) from exc

try:
    import paho.mqtt.client as mqtt
except ImportError as exc:
    raise RuntimeError(
        "paho-mqtt is required for MQTT support. Install with: pip install paho-mqtt"
    ) from exc


ButtonCallback = Callable[[], None]
AxisCallback = Callable[[float], None]


@dataclasses.dataclass(frozen=True)
class RemoteEvent:
    event_type: str
    control: str
    value: float
    timestamp: float


@dataclasses.dataclass(frozen=True)
class ControllerState:
    connected: bool
    device_name: str
    axes: Tuple[float, ...]
    buttons: Tuple[int, ...]
    hats: Tuple[Tuple[int, int], ...]
    timestamp: float


class RemoteControllerAPI:
    """
    Cross-platform controller input API with optional MQTT publishing.
    """

    def __init__(
        self,
        deadzone: float = 0.15,
        poll_hz: float = 120.0,
        queue_size: int = 512,
        reconnect_interval_s: float = 1.0,
    ):
        self.deadzone = max(0.0, min(0.9, deadzone))
        self.poll_hz = max(10.0, poll_hz)
        self.reconnect_interval_s = max(0.2, reconnect_interval_s)

        self._button_bindings: Dict[str, ButtonCallback] = {}
        self._axis_bindings: Dict[str, AxisCallback] = {}
        self._event_queue: Deque[RemoteEvent] = deque(maxlen=max(32, queue_size))

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._device: Optional["pygame.joystick.Joystick"] = None
        self._device_instance_id: Optional[int] = None
        self._last_axes: Dict[int, float] = {}
        self._last_reconnect_attempt = 0.0

        # MQTT support
        self.mqtt_client: Optional[mqtt.Client] = None
        self.mqtt_topic: str = "robot/controller"

    # =========================
    # MQTT SETUP
    # =========================
    def enable_mqtt(
        self,
        broker_ip: str,
        topic: str = "robot/controller",
        port: int = 1883,
    ) -> None:
        self.mqtt_topic = topic
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(broker_ip, port, 60)
        self.mqtt_client.loop_start()
        print(f"[MQTT] Connected to broker at {broker_ip}:{port}")

    def disable_mqtt(self) -> None:
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.mqtt_client = None
            print("[MQTT] Disconnected")

    # =========================
    # BINDINGS
    # =========================
    def bind_button(self, button_name: str, callback: ButtonCallback) -> None:
        self._button_bindings[button_name] = callback

    def bind_axis(self, axis_name: str, callback: AxisCallback) -> None:
        self._axis_bindings[axis_name] = callback

    # =========================
    # START/STOP
    # =========================
    def start(self, threaded: bool = True) -> None:
        with self._lock:
            if self._running:
                return

            pygame.init()
            pygame.joystick.init()
            self._running = True

            if threaded:
                self._thread = threading.Thread(target=self._poll_loop, daemon=True)
                self._thread.start()
            else:
                self._thread = None
                self._last_reconnect_attempt = 0.0

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)

        self._thread = None

        if self._device is not None:
            try:
                self._device.quit()
            except Exception:
                pass

        self._device = None
        self._device_instance_id = None

        pygame.joystick.quit()
        pygame.quit()

        self.disable_mqtt()

    def is_running(self) -> bool:
        return self._running

    # =========================
    # EVENTS
    # =========================
    def get_events(self, clear: bool = True) -> Tuple[RemoteEvent, ...]:
        with self._lock:
            snapshot = tuple(self._event_queue)
            if clear:
                self._event_queue.clear()
        return snapshot

    def get_state_snapshot(self) -> ControllerState:
        if self._device is None:
            return ControllerState(
                connected=False,
                device_name="disconnected",
                axes=tuple(),
                buttons=tuple(),
                hats=tuple(),
                timestamp=time.time(),
            )

        joystick = self._device
        if not joystick.get_init():
            return ControllerState(
                connected=False,
                device_name="disconnected",
                axes=tuple(),
                buttons=tuple(),
                hats=tuple(),
                timestamp=time.time(),
            )

        axis_count = joystick.get_numaxes()
        button_count = joystick.get_numbuttons()
        hat_count = joystick.get_numhats()

        axes = tuple(
            self._apply_deadzone(float(joystick.get_axis(i)))
            for i in range(axis_count)
        )

        buttons = tuple(
            int(joystick.get_button(i))
            for i in range(button_count)
        )

        hats = tuple(
            (int(joystick.get_hat(i)[0]), int(joystick.get_hat(i)[1]))
            for i in range(hat_count)
        )

        return ControllerState(
            connected=True,
            device_name=joystick.get_name(),
            axes=axes,
            buttons=buttons,
            hats=hats,
            timestamp=time.time(),
        )

    # =========================
    # POLLING
    # =========================
    def _poll_loop(self) -> None:
        sleep_time = 1.0 / self.poll_hz

        while self._running:
            self.poll_once()
            time.sleep(sleep_time)

    def poll_once(self) -> None:
        if not self._running:
            return

        now = time.monotonic()

        if (
            self._device is None
            and now - self._last_reconnect_attempt >= self.reconnect_interval_s
        ):
            self._last_reconnect_attempt = now
            self._try_connect()

        for pg_event in pygame.event.get():
            self._handle_pygame_event(pg_event)

    def _try_connect(self) -> None:
        pygame.joystick.quit()
        pygame.joystick.init()

        count = pygame.joystick.get_count()
        if count <= 0:
            return

        joystick = pygame.joystick.Joystick(0)
        joystick.init()

        self._device = joystick
        self._device_instance_id = joystick.get_instance_id()
        self._last_axes.clear()

    # =========================
    # EVENT HANDLING
    # =========================
    def _handle_pygame_event(self, pg_event) -> None:
        if pg_event.type == pygame.JOYDEVICEREMOVED:
            removed_id = getattr(pg_event, "instance_id", None)

            if self._device_instance_id is None or removed_id == self._device_instance_id:
                self._device = None
                self._device_instance_id = None
                self._last_axes.clear()
            return

        if pg_event.type == pygame.JOYDEVICEADDED and self._device is None:
            self._try_connect()
            return

        if pg_event.type == pygame.JOYBUTTONDOWN:
            button_name = f"button_{pg_event.button}"

            event = RemoteEvent(
                "button_down",
                button_name,
                1.0,
                time.time()
            )

            self._record_and_dispatch(event)

            callback = self._button_bindings.get(button_name)
            if callback:
                callback()
            return

        if pg_event.type == pygame.JOYBUTTONUP:
            button_name = f"button_{pg_event.button}"

            event = RemoteEvent(
                "button_up",
                button_name,
                0.0,
                time.time()
            )

            self._record_and_dispatch(event)
            return

        if pg_event.type == pygame.JOYAXISMOTION:
            axis_index = int(pg_event.axis)
            axis_name = f"axis_{axis_index}"

            raw_value = float(pg_event.value)
            value = self._apply_deadzone(raw_value)

            previous = self._last_axes.get(axis_index, 0.0)

            if abs(value - previous) < 0.02:
                return

            self._last_axes[axis_index] = value

            event = RemoteEvent(
                "axis_motion",
                axis_name,
                value,
                time.time()
            )

            self._record_and_dispatch(event)

            callback = self._axis_bindings.get(axis_name)
            if callback:
                callback(value)
            return

    # =========================
    # RECORD + MQTT SEND
    # =========================
    def _record_and_dispatch(self, event: RemoteEvent) -> None:
        with self._lock:
            self._event_queue.append(event)

        if self.mqtt_client:
            try:
                self.mqtt_client.publish(
                    self.mqtt_topic,
                    json.dumps(dataclasses.asdict(event))
                )
            except Exception as exc:
                print(f"[MQTT ERROR] {exc}")

    # =========================
    # HELPERS
    # =========================
    def _apply_deadzone(self, value: float) -> float:
        if abs(value) < self.deadzone:
            return 0.0
        return max(-1.0, min(1.0, value))

    @staticmethod
    def list_connected_devices() -> Iterable[str]:
        pygame.init()
        pygame.joystick.init()

        devices = []

        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            devices.append(j.get_name())
            j.quit()

        pygame.joystick.quit()
        pygame.quit()

        return tuple(devices)
