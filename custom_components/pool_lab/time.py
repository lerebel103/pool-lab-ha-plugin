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


@dataclass(frozen=True, kw_only=True)
class PoolLabTimeDescription(TimeEntityDescription):
    """Describes a Pool Lab time entity."""

    value_fn: Callable[[PoolLabState], time]
    timer_number: int
    is_start: bool


def _build_set_timer_command(
    coordinator: PoolLabCoordinator,
    timer_number: int,
    is_start: bool,
    new_time: time,
) -> str:
    """Build a timer set command.

    Uses the guessed command format: t<n>,start_hr,start_min,stop_hr,stop_min;\\r
    The non-changing values are read from the current coordinator state.
    """
    state = coordinator.data
    if timer_number == 1:
        start_hr = new_time.hour if is_start else state.timer1_start_hr
        start_min = new_time.minute if is_start else state.timer1_start_min
        stop_hr = new_time.hour if not is_start else state.timer1_stop_hr
        stop_min = new_time.minute if not is_start else state.timer1_stop_min
    else:
        start_hr = new_time.hour if is_start else state.timer2_start_hr
        start_min = new_time.minute if is_start else state.timer2_start_min
        stop_hr = new_time.hour if not is_start else state.timer2_stop_hr
        stop_min = new_time.minute if not is_start else state.timer2_stop_min

    return f"t{timer_number},{start_hr},{start_min},{stop_hr},{stop_min};\r"


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
        """Set the new time value."""
        command = _build_set_timer_command(
            self.coordinator,
            self.entity_description.timer_number,
            self.entity_description.is_start,
            value,
        )
        await self.coordinator.async_send_command(command)
