"""Driver interface: turns pixel canvases into the writes (GATT or HID) one badge type expects."""
from dataclasses import dataclass

from ..core.render import Display


@dataclass(frozen=True)
class Write:
    # Empty for USB, where every write is one HID report
    characteristic: str
    data: bytes
    response: bool = True
    # Seconds to wait after this write before the next one
    pause: float = 0.0


class Driver:
    name: str
    display: Display
    modes: tuple[str, ...]
    # Module in transport/ that reaches the badge: "ble" or "usb"
    transport: str = "ble"
    service_uuid: str
    # USB vendor and product id, only for transport "usb"
    usb_id: tuple[int, int] = (0, 0)
    name_prefixes: tuple[str, ...] = ()
    # Characteristics whose notifications must be enabled before writing
    notify_characteristics: tuple[str, ...] = ()
    # Modes in which the badge scrolls a strip of any width; all others show one screen
    scroll_modes: tuple[str, ...] = ("left", "right")
    # Messages one transmission can hold; the badge shows them one after another
    max_messages: int = 1

    def is_fixed(self, mode: str) -> bool:
        return mode not in self.scroll_modes

    def matches(self, name: str | None, service_uuids: list[str]) -> bool:
        return self.service_uuid in service_uuids or (name or "").upper().startswith(self.name_prefixes)

    def build_writes(self, pages: list[list[list[int]]], mode: str, speed: int, brightness: int) -> list[Write]:
        """One canvas from core.render.layout per message; speed 1-8; brightness in percent (1-100)."""
        raise NotImplementedError
