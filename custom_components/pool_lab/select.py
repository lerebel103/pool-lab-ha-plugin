"""Select platform for Pool Lab integration.

Exposes tri-state controls (OFF/ON/AUTO) as select entities:
filter, AUX outputs, valves, and grouped outputs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OutputMode, PumpSpeed, SystemFlag, SystemFlag2
from .coordinator import PoolLabCoordinator
from .entity import build_device_info
from .models import PoolLabState
from .protocol import (
    cmd_aux,
    cmd_blower,
    cmd_cleaner,
    cmd_filter,
    cmd_fountain,
    cmd_infloor,
    cmd_pool_light,
    cmd_pump_speed,
    cmd_spa_boost,
    cmd_spa_light,
    cmd_valve,
)

# String options exposed to Home Assistant
OPTIONS = ["off", "on", "auto"]

# Mapping between HA string values and internal enum
_STR_TO_MODE = {"off": OutputMode.OFF, "on": OutputMode.ON, "auto": OutputMode.AUTO}
_MODE_TO_STR = {v: k for k, v in _STR_TO_MODE.items()}


@dataclass(frozen=True, kw_only=True)
class PoolLabSelectDescription(SelectEntityDescription):
    """Describes a Pool Lab select entity."""

    value_fn: Callable[[PoolLabState], OutputMode]
    set_mode_cmd: Callable[[OutputMode], str]
    available_fn: Callable[[PoolLabState], bool] | None = None


# ---------------------------------------------------------------------------
# Static select definitions
# ---------------------------------------------------------------------------

_CORE_SELECTS: tuple[PoolLabSelectDescription, ...] = (
    PoolLabSelectDescription(
        key="filter_mode",
        translation_key="filter_mode",
        icon="mdi:air-filter",
        options=OPTIONS,
        value_fn=lambda s: s.filter_mode,
        set_mode_cmd=lambda mode: cmd_filter(mode),
    ),
)

_GROUP_SELECTS: tuple[PoolLabSelectDescription, ...] = (
    PoolLabSelectDescription(
        key="pool_light_mode",
        translation_key="pool_light_mode",
        icon="mdi:lightbulb",
        options=OPTIONS,
        value_fn=lambda s: s.pool_light,
        set_mode_cmd=lambda mode: cmd_pool_light(mode),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.POOL_LIGHT_GROUP),
    ),
    PoolLabSelectDescription(
        key="spa_light_mode",
        translation_key="spa_light_mode",
        icon="mdi:lightbulb",
        options=OPTIONS,
        value_fn=lambda s: s.spa_light,
        set_mode_cmd=lambda mode: cmd_spa_light(mode),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.SPA_LIGHT_GROUP),
    ),
    PoolLabSelectDescription(
        key="spa_boost_mode",
        translation_key="spa_boost_mode",
        icon="mdi:rocket-launch",
        options=OPTIONS,
        value_fn=lambda s: s.spa_boost,
        set_mode_cmd=lambda mode: cmd_spa_boost(mode),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.SPA_BOOST_GROUP),
    ),
    PoolLabSelectDescription(
        key="blower_mode",
        translation_key="blower_mode",
        icon="mdi:fan",
        options=OPTIONS,
        value_fn=lambda s: s.spa_blower,
        set_mode_cmd=lambda mode: cmd_blower(mode),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.SPA_BLOWER_GROUP),
    ),
    PoolLabSelectDescription(
        key="infloor_mode",
        translation_key="infloor_mode",
        icon="mdi:robot-vacuum",
        options=OPTIONS,
        value_fn=lambda s: s.infloor,
        set_mode_cmd=lambda mode: cmd_infloor(mode),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.INFLOOR_GROUP),
    ),
    PoolLabSelectDescription(
        key="cleaner_mode",
        translation_key="cleaner_mode",
        icon="mdi:robot-vacuum",
        options=OPTIONS,
        value_fn=lambda s: s.cleaner,
        set_mode_cmd=lambda mode: cmd_cleaner(mode),
        available_fn=lambda s: bool(s.system_flags_2 & SystemFlag2.CLEANER_GROUP),
    ),
    PoolLabSelectDescription(
        key="fountain_mode",
        translation_key="fountain_mode",
        icon="mdi:fountain",
        options=OPTIONS,
        value_fn=lambda s: s.fountain,
        set_mode_cmd=lambda mode: cmd_fountain(mode),
        available_fn=lambda s: bool(s.system_flags_2 & SystemFlag2.FOUNTAIN_GROUP),
    ),
)


def _build_aux_select(num: int) -> PoolLabSelectDescription:
    """Build a select description for an AUX output."""
    flag = SystemFlag(1 << (6 + num))  # AUX1 = bit 7, AUX2 = bit 8, etc.
    return PoolLabSelectDescription(
        key=f"aux_{num}_mode",
        translation_key=f"aux_{num}_mode",
        icon="mdi:electric-switch",
        options=OPTIONS,
        value_fn=lambda s, n=num: s.aux_modes.get(n, OutputMode.OFF),
        set_mode_cmd=lambda mode, n=num: cmd_aux(n, mode),
        available_fn=lambda s, f=flag: bool(s.system_flags & f),
    )


def _build_valve_select(num: int) -> PoolLabSelectDescription:
    """Build a select description for a valve."""
    flag = SystemFlag.VALVE3 if num == 3 else SystemFlag.VALVE4
    return PoolLabSelectDescription(
        key=f"valve_{num}_mode",
        translation_key=f"valve_{num}_mode",
        icon="mdi:valve",
        options=OPTIONS,
        value_fn=lambda s, n=num: s.valve3_mode if n == 3 else s.valve4_mode,
        set_mode_cmd=lambda mode, n=num: cmd_valve(n, mode),
        available_fn=lambda s, f=flag: bool(s.system_flags & f),
    )


# Pump speed options
PUMP_SPEED_OPTIONS = ["low", "medium", "high"]
_STR_TO_SPEED = {"low": PumpSpeed.LOW, "medium": PumpSpeed.MEDIUM, "high": PumpSpeed.HIGH}
_SPEED_TO_STR = {v: k for k, v in _STR_TO_SPEED.items()}

_PUMP_SPEED_SELECT = PoolLabSelectDescription(
    key="pump_speed_control",
    translation_key="pump_speed_control",
    icon="mdi:pump",
    options=PUMP_SPEED_OPTIONS,
    value_fn=lambda s: s.pump_speed,
    set_mode_cmd=lambda mode: cmd_pump_speed(mode),
    available_fn=lambda s: bool(s.system_flags & SystemFlag.MS_PUMP),
)


_AUX_SELECTS = tuple(_build_aux_select(n) for n in range(1, 10))
_VALVE_SELECTS = tuple(_build_valve_select(n) for n in (3, 4))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Lab select entities."""
    coordinator: PoolLabCoordinator = hass.data[DOMAIN][entry.entry_id]

    all_descriptions = _CORE_SELECTS + _GROUP_SELECTS + _AUX_SELECTS + _VALVE_SELECTS
    entities: list[SelectEntity] = [
        PoolLabSelect(coordinator, description, entry) for description in all_descriptions
    ]

    # Add pump speed select (uses different option mapping)
    entities.append(PoolLabPumpSpeedSelect(coordinator, _PUMP_SPEED_SELECT, entry))

    async_add_entities(entities)


class PoolLabSelect(CoordinatorEntity[PoolLabCoordinator], SelectEntity):
    """A select entity for a Pool Lab tri-state control."""

    entity_description: PoolLabSelectDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolLabCoordinator,
        description: PoolLabSelectDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = build_device_info(entry)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self.coordinator.data is None:
            return None
        mode = self.entity_description.value_fn(self.coordinator.data)
        return _MODE_TO_STR.get(mode, "off")

    @property
    def available(self) -> bool:
        """Return True if the entity is available."""
        if not super().available:
            return False
        if self.entity_description.available_fn is None:
            return True
        if self.coordinator.data is None:
            return False
        return self.entity_description.available_fn(self.coordinator.data)

    async def async_select_option(self, option: str) -> None:
        """Handle the user selecting an option."""
        mode = _STR_TO_MODE[option]
        command = self.entity_description.set_mode_cmd(mode)
        await self.coordinator.async_send_command(command)


class PoolLabPumpSpeedSelect(CoordinatorEntity[PoolLabCoordinator], SelectEntity):
    """A select entity for the Pool Lab pump speed control."""

    entity_description: PoolLabSelectDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolLabCoordinator,
        description: PoolLabSelectDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the pump speed select entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = build_device_info(entry)

    @property
    def options(self) -> list[str]:
        """Return available options."""
        return PUMP_SPEED_OPTIONS

    @property
    def current_option(self) -> str | None:
        """Return the current pump speed."""
        if self.coordinator.data is None:
            return None
        speed = self.coordinator.data.pump_speed
        return _SPEED_TO_STR.get(speed, "low")

    @property
    def available(self) -> bool:
        """Return True if the entity is available."""
        if not super().available:
            return False
        if self.coordinator.data is None:
            return False
        return bool(self.coordinator.data.system_flags & SystemFlag.MS_PUMP)

    async def async_select_option(self, option: str) -> None:
        """Handle the user selecting a pump speed."""
        speed = _STR_TO_SPEED[option]
        command = cmd_pump_speed(speed)
        await self.coordinator.async_send_command(command)
