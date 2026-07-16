"""Time platform for Pool Lab integration.

Exposes filter timer start/stop times as editable time entities.
Timer 1 and Timer 2 each have a start and stop time.

The write command format is not documented by the manufacturer.
On first use, this module tries multiple guessed command formats
and logs which one the device accepts.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolLabCoordinator
from .entity import build_device_info
from .models import PoolLabState

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PoolLabTimeDescription(TimeEntityDescription):
    """Describes a Pool Lab time entity."""

    value_fn: Callable[[PoolLabState], time]
    timer_number: int
    is_start: bool


def _build_timer_command_candidates(
    state: PoolLabState,
    timer_number: int,
    is_start: bool,
    new_time: time,
) -> list[str]:
    """Build a list of guessed timer command formats to try.

    Returns 10 different command string candidates. The device will
    respond to the correct one and ignore/disconnect on wrong ones.
    """
    if timer_number == 1:
        sh = new_time.hour if is_start else state.timer1_start_hr
        sm = new_time.minute if is_start else state.timer1_start_min
        eh = new_time.hour if not is_start else state.timer1_stop_hr
        em = new_time.minute if not is_start else state.timer1_stop_min
    else:
        sh = new_time.hour if is_start else state.timer2_start_hr
        sm = new_time.minute if is_start else state.timer2_start_min
        eh = new_time.hour if not is_start else state.timer2_stop_hr
        em = new_time.minute if not is_start else state.timer2_stop_min

    n = timer_number

    return [
        # 1. "s1,8,0,9,30;" — "s" + timer number, all four values
        f"s{n},{sh},{sm},{eh},{em};\r",
        # 2. "tm,1,8,0,9,30;" — "tm" command with timer number as first param
        f"tm,{n},{sh},{sm},{eh},{em};\r",
        # 3. "tr,1,8,0,9,30;" — "tr" (timer run)
        f"tr,{n},{sh},{sm},{eh},{em};\r",
        # 4. "st,1,8,0,9,30;" — "st" (set timer)
        f"st,{n},{sh},{sm},{eh},{em};\r",
        # 5. "t1,8,0,9,30;" — "t" + number (original guess)
        f"t{n},{sh},{sm},{eh},{em};\r",
        # 6. "ti,1,8,0,9,30;" — "ti" (timer)
        f"ti,{n},{sh},{sm},{eh},{em};\r",
        # 7. "ft,1,8,0,9,30;" — "ft" (filter timer)
        f"ft,{n},{sh},{sm},{eh},{em};\r",
        # 8. "fs,1,8,0,9,30;" — "fs" (filter schedule)
        f"fs,{n},{sh},{sm},{eh},{em};\r",
        # 9. "sc,1,8,0,9,30;" — "sc" (schedule)
        f"sc,{n},{sh},{sm},{eh},{em};\r",
        # 10. "ts,1,0800,0930;" — "ts" with HHMM combined format
        f"ts,{n},{sh:02d}{sm:02d},{eh:02d}{em:02d};\r",
    ]


TIME_DESCRIPTIONS: tuple[PoolLabTimeDescription, ...] = (
    PoolLabTimeDescription(
        key="timer_1_start",
        translation_key="timer_1_start",
        icon="mdi:clock-start",
        timer_number=1,
        is_start=True,
        value_fn=lambda s: time(s.timer1_start_hr, s.timer1_start_min),
    ),
    PoolLabTimeDescription(
        key="timer_1_stop",
        translation_key="timer_1_stop",
        icon="mdi:clock-end",
        timer_number=1,
        is_start=False,
        value_fn=lambda s: time(s.timer1_stop_hr, s.timer1_stop_min),
    ),
    PoolLabTimeDescription(
        key="timer_2_start",
        translation_key="timer_2_start",
        icon="mdi:clock-start",
        timer_number=2,
        is_start=True,
        value_fn=lambda s: time(s.timer2_start_hr, s.timer2_start_min),
    ),
    PoolLabTimeDescription(
        key="timer_2_stop",
        translation_key="timer_2_stop",
        icon="mdi:clock-end",
        timer_number=2,
        is_start=False,
        value_fn=lambda s: time(s.timer2_stop_hr, s.timer2_stop_min),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Lab time entities."""
    coordinator: PoolLabCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [PoolLabTime(coordinator, description, entry) for description in TIME_DESCRIPTIONS]
    async_add_entities(entities)


class PoolLabTime(CoordinatorEntity[PoolLabCoordinator], TimeEntity):
    """A time entity for a Pool Lab timer configuration."""

    entity_description: PoolLabTimeDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolLabCoordinator,
        description: PoolLabTimeDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the time entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = build_device_info(entry)

    @property
    def native_value(self) -> time | None:
        """Return the current time value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_value(self, value: time) -> None:
        """Set the new time value by trying multiple command formats.

        Iterates through guessed command formats. If the device responds,
        the successful format is logged. If it disconnects (wrong command),
        we reconnect and try the next format.
        """
        if self.coordinator.data is None:
            return

        candidates = _build_timer_command_candidates(
            self.coordinator.data,
            self.entity_description.timer_number,
            self.entity_description.is_start,
            value,
        )

        for i, command in enumerate(candidates, 1):
            _LOGGER.info(
                "Timer command attempt %d/10: %s",
                i,
                command.strip(),
            )
            try:
                await self.coordinator.async_send_command(command)
                _LOGGER.warning(
                    "Timer command SUCCESS with format #%d: %s",
                    i,
                    command.strip(),
                )
                return
            except Exception:
                _LOGGER.debug(
                    "Timer command attempt %d failed, trying next format",
                    i,
                )
                continue

        _LOGGER.error(
            "All 10 timer command formats failed. "
            "The timer set command is not supported by this device firmware."
        )
