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

    def matches(self, name: str | None, service_uuids: list[str]) -> bool:
        return self.service_uuid in service_uuids or (name or "").upper().startswith(self.name_prefixes)

    def build_writes(self, canvas: list[list[int]], mode: str, speed: int, brightness: int) -> list[Write]:
        """canvas from core.render.layout; speed 1-8; brightness in percent (1-100)."""
        raise NotImplementedError
