"""USB transport via hidapi: find plugged-in badges and execute a driver's writes as HID reports."""
import asyncio

import hid

from ..core.i18n import LocalizedError
from ..drivers import DRIVERS, Driver, Write
from . import Found


async def scan(timeout: float) -> list[Found]:
    # Enumeration answers at once; timeout only keeps the signature of ble.scan
    found = []
    for driver in DRIVERS.values():
        if driver.transport == "usb":
            for device in hid.enumerate(*driver.usb_id):
                found.append(Found(device["path"].decode(), device["product_string"] or "", None, driver.name))
    return found


async def first_address(driver: Driver) -> str:
    """Path of the first plugged-in badge, for sending without --address."""
    found = [badge for badge in await scan(0) if badge.driver == driver.name]
    if not found:
        raise LocalizedError("err.no_usb_badge")
    return found[0].address


async def execute(address: str, driver: Driver, writes: list[Write]) -> None:
    device = hid.device()
    try:
        device.open_path(address.encode())
    except OSError as error:
        raise LocalizedError("err.usb_not_found", address=address) from error
    try:
        for write in writes:
            # Report id 0 goes in front of the report
            if device.write(b"\0" + write.data) < 0:
                raise OSError(device.error())
            if write.pause:
                await asyncio.sleep(write.pause)
    finally:
        device.close()
