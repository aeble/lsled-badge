"""Driver interface: turns a pixel canvas into the GATT writes one badge type expects."""
from dataclasses import dataclass

from ..core.render import Display


@dataclass(frozen=True)
class Write:
    characteristic: str
    data: bytes
    response: bool = True
    # Seconds to wait after this write before the next one
    pause: float = 0.0


class Driver:
    name: str
    display: Display
    modes: tuple[str, ...]
    service_uuid: str
    name_prefixes: tuple[str, ...] = ()
    # Characteristics whose notifications must be enabled before writing
    notify_characteristics: tuple[str, ...] = ()
    # Modes in which the badge scrolls a strip of any width; all others show one screen
    scroll_modes: tuple[str, ...] = ("left", "right")
    # Columns the badge shifts one-screen content to the right, per mode
    x_shift: dict[str, int] = {}

    def is_fixed(self, mode: str) -> bool:
        return mode not in self.scroll_modes

    def usable_width(self, mode: str) -> int:
        return self.display.width - self.x_shift.get(mode, 0)

    def matches(self, name: str | None, service_uuids: list[str]) -> bool:
        return self.service_uuid in service_uuids or (name or "").upper().startswith(self.name_prefixes)

    def build_writes(self, canvas: list[list[int]], mode: str, speed: int, brightness: int) -> list[Write]:
        """canvas from core.render.layout; speed 1-8; brightness in percent (1-100)."""
        raise NotImplementedError
