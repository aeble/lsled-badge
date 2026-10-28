"""Registry of badge drivers."""
from .base import Driver, Write
from .lsled import LsledDriver
from .timhodson import TimHodsonDriver

DRIVERS: dict[str, Driver] = {driver.name: driver for driver in (LsledDriver(), TimHodsonDriver())}
DEFAULT_DRIVER = "lsled"
ALL_MODES = tuple(dict.fromkeys(mode for driver in DRIVERS.values() for mode in driver.modes))

__all__ = ["ALL_MODES", "DEFAULT_DRIVER", "DRIVERS", "Driver", "Write"]
