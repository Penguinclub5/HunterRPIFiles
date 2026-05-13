#!/usr/bin/python3
# coding=utf-8

from __future__ import annotations

import sys
from pathlib import Path


# Keep script runnable from either repo root or app/ directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from app.manual_control import run_manual_control
except ModuleNotFoundError:
    from manual_control import run_manual_control


manual = True


def is_manual_mode() -> bool:
    return manual


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python3 main_pi.py <my_name> <partner_name> [broker_ip]")
        print("Example: python3 main_pi.py host robot 192.168.6.168")
        sys.exit(1)

    my_name = sys.argv[1]
    partner_name = sys.argv[2]

    if len(sys.argv) >= 4:
        broker_host = sys.argv[3]
    else:
        broker_host = "192.168.6.168"

    print("Host Pi control loop started.")
    print("My name:", my_name)
    print("Partner name:", partner_name)
    print("Broker host:", broker_host)

    try:
        run_manual_control(
            is_manual_mode=is_manual_mode,
            my_name=my_name,
            partner_name=partner_name,
            broker_host=broker_host,
        )

    except KeyboardInterrupt:
        print("\nHost Pi control loop stopped.")


if __name__ == "__main__":
    main()
