"""Time platform for Pool Lab integration.

Exposes filter timer start/stop times as editable time entities.
Timer 1 and Timer 2 each have a start and stop time.
"""

from __future__ import annotations

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
from .protocol import (
    cmd_timer_end_hour,
    cmd_timer_end_minute,
    cmd_timer_start_hour,
    cmd_timer_start_minute,
)


@dataclass(frozen=True, kw_only=True)
class PoolLabTimeDescription(TimeEntityDescription):
    """Describes a Pool Lab time entity."""

    value_fn: Callable[[PoolLabState], time]
    timer_number: int
    is_start: bool


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
        """Set the new time value.

        Sends separate commands for hour and minute as required
        by the device protocol (e.g. s1h,8; s1m,30;).
        """
        timer_num = self.entity_description.timer_number

        if self.entity_description.is_start:
            hour_cmd = cmd_timer_start_hour(timer_num, value.hour)
            minute_cmd = cmd_timer_start_minute(timer_num, value.minute)
        else:
            hour_cmd = cmd_timer_end_hour(timer_num, value.hour)
            minute_cmd = cmd_timer_end_minute(timer_num, value.minute)

        await self.coordinator.async_send_command(hour_cmd)
        await self.coordinator.async_send_command(minute_cmd)
