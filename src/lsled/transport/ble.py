"""Bluetooth LE transport via bleak: find badges and execute a driver's writes."""
import asyncio

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDeviceNotFoundError

from ..core.i18n import LocalizedError
from ..drivers import DRIVERS, Driver, Write
from . import Found


async def scan(timeout: float) -> list[Found]:
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    found = []
    for device, adv in devices.values():
        name = device.name or adv.local_name
        for driver in DRIVERS.values():
            if driver.matches(name, adv.service_uuids):
                found.append(Found(device.address, name or "", adv.rssi, driver.name))
                break
    return found


async def execute(address: str, driver: Driver, writes: list[Write]) -> None:
    try:
        async with BleakClient(address, timeout=20) as client:
            for characteristic in driver.notify_characteristics:
                await client.start_notify(characteristic, lambda _sender, _data: None)
            for write in writes:
                await client.write_gatt_char(write.characteristic, write.data, response=write.response)
                if write.pause:
                    await asyncio.sleep(write.pause)
    except BleakDeviceNotFoundError as error:
        raise LocalizedError("err.device_not_found", address=address) from error
