"""Transports reach a badge and execute a driver's writes; every module has scan() and execute()."""
from dataclasses import dataclass


@dataclass
class Found:
    address: str
    name: str
    # None for USB
    rssi: int | None
    driver: str
