"""USB badges 0416:5020 (Winbond, "LS32"): the "wang" record of the LSLED badges as HID reports.

Report size and pause follow https://github.com/jnweiger/led-name-badge-ls32; the code here is
written anew.
"""
from .base import Write
from .lsled import LsledDriver

REPORT_SIZE = 64


class LsledUsbDriver(LsledDriver):
    name = "lsled-usb"
    transport = "usb"
    # Not reachable over Bluetooth: the BLE scan and Web Bluetooth must not match it
    service_uuid = ""
    name_prefixes = ()
    usb_id = (0x0416, 0x5020)

    def build_writes(self, pages: list[list[list[int]]], mode: str, speed: int, brightness: int) -> list[Write]:
        data = self.build_record(pages, mode, speed, brightness)
        data += bytes(-len(data) % REPORT_SIZE)
        # led-name-badge-ls32 waits 0.1 s per report
        return [Write("", data[i:i + REPORT_SIZE], pause=0.1) for i in range(0, len(data), REPORT_SIZE)]
