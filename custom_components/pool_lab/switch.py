"""Switch platform for Pool Lab integration.

Exposes controllable on/off outputs: filter, heater, solar heat,
AUX outputs, valves, and grouped outputs (lights, blower, etc.).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OutputMode, SystemFlag, SystemFlag2
from .coordinator import PoolLabCoordinator
from .models import PoolLabState
from .protocol import (
    cmd_aux,
    cmd_blower,
    cmd_cleaner,
    cmd_filter,
    cmd_fountain,
    cmd_heater,
    cmd_infloor,
    cmd_pool_light,
    cmd_pool_spa,
    cmd_solar_heat,
    cmd_spa_boost,
    cmd_spa_light,
    cmd_valve,
)


@dataclass(frozen=True, kw_only=True)
class PoolLabSwitchDescription(SwitchEntityDescription):
    """Describes a Pool Lab switch entity."""

    is_on_fn: Callable[[PoolLabState], bool]
    turn_on_cmd: Callable[[], str]
    turn_off_cmd: Callable[[], str]
    available_fn: Callable[[PoolLabState], bool] | None = None


# ---------------------------------------------------------------------------
# Static switch definitions
# ---------------------------------------------------------------------------

_CORE_SWITCHES: tuple[PoolLabSwitchDescription, ...] = (
    PoolLabSwitchDescription(
        key="filter",
        translation_key="filter",
        icon="mdi:air-filter",
        is_on_fn=lambda s: s.filter_mode == OutputMode.ON,
        turn_on_cmd=lambda: cmd_filter(OutputMode.ON),
        turn_off_cmd=lambda: cmd_filter(OutputMode.OFF),
    ),
    PoolLabSwitchDescription(
        key="spa_mode",
        translation_key="spa_mode",
        icon="mdi:hot-tub",
        is_on_fn=lambda s: s.spa_mode.value == 1,
        turn_on_cmd=lambda: cmd_pool_spa(None),  # toggle to SPA
        turn_off_cmd=lambda: cmd_pool_spa(None),  # toggle to POOL
        available_fn=lambda s: (
            bool(s.system_flags & SystemFlag.POOL) and bool(s.system_flags & SystemFlag.SPA)
        ),
    ),
    PoolLabSwitchDescription(
        key="solar_heat",
        translation_key="solar_heat",
        icon="mdi:solar-power",
        is_on_fn=lambda s: s.solar_mode != OutputMode.OFF,
        turn_on_cmd=lambda: cmd_solar_heat(OutputMode.ON),
        turn_off_cmd=lambda: cmd_solar_heat(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags & (SystemFlag.SOLARPOOL | SystemFlag.SOLARSPA)),
    ),
    PoolLabSwitchDescription(
        key="heater",
        translation_key="heater",
        icon="mdi:fire",
        is_on_fn=lambda s: s.heat_mode != OutputMode.OFF,
        turn_on_cmd=lambda: cmd_heater(OutputMode.ON),
        turn_off_cmd=lambda: cmd_heater(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags & (SystemFlag.HEATPOOL | SystemFlag.HEATSPA)),
    ),
)

_GROUP_SWITCHES: tuple[PoolLabSwitchDescription, ...] = (
    PoolLabSwitchDescription(
        key="pool_light",
        translation_key="pool_light",
        icon="mdi:lightbulb",
        is_on_fn=lambda s: s.pool_light == OutputMode.ON,
        turn_on_cmd=lambda: cmd_pool_light(OutputMode.ON),
        turn_off_cmd=lambda: cmd_pool_light(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.POOL_LIGHT_GROUP),
    ),
    PoolLabSwitchDescription(
        key="spa_light",
        translation_key="spa_light",
        icon="mdi:lightbulb",
        is_on_fn=lambda s: s.spa_light == OutputMode.ON,
        turn_on_cmd=lambda: cmd_spa_light(OutputMode.ON),
        turn_off_cmd=lambda: cmd_spa_light(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.SPA_LIGHT_GROUP),
    ),
    PoolLabSwitchDescription(
        key="spa_boost",
        translation_key="spa_boost",
        icon="mdi:rocket-launch",
        is_on_fn=lambda s: s.spa_boost == OutputMode.ON,
        turn_on_cmd=lambda: cmd_spa_boost(OutputMode.ON),
        turn_off_cmd=lambda: cmd_spa_boost(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.SPA_BOOST_GROUP),
    ),
    PoolLabSwitchDescription(
        key="blower",
        translation_key="blower",
        icon="mdi:fan",
        is_on_fn=lambda s: s.spa_blower == OutputMode.ON,
        turn_on_cmd=lambda: cmd_blower(OutputMode.ON),
        turn_off_cmd=lambda: cmd_blower(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.SPA_BLOWER_GROUP),
    ),
    PoolLabSwitchDescription(
        key="infloor",
        translation_key="infloor",
        icon="mdi:robot-vacuum",
        is_on_fn=lambda s: s.infloor == OutputMode.ON,
        turn_on_cmd=lambda: cmd_infloor(OutputMode.ON),
        turn_off_cmd=lambda: cmd_infloor(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags & SystemFlag.INFLOOR_GROUP),
    ),
    PoolLabSwitchDescription(
        key="cleaner",
        translation_key="cleaner",
        icon="mdi:robot-vacuum",
        is_on_fn=lambda s: s.cleaner == OutputMode.ON,
        turn_on_cmd=lambda: cmd_cleaner(OutputMode.ON),
        turn_off_cmd=lambda: cmd_cleaner(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags_2 & SystemFlag2.CLEANER_GROUP),
    ),
    PoolLabSwitchDescription(
        key="fountain",
        translation_key="fountain",
        icon="mdi:fountain",
        is_on_fn=lambda s: s.fountain == OutputMode.ON,
        turn_on_cmd=lambda: cmd_fountain(OutputMode.ON),
        turn_off_cmd=lambda: cmd_fountain(OutputMode.OFF),
        available_fn=lambda s: bool(s.system_flags_2 & SystemFlag2.FOUNTAIN_GROUP),
    ),
)


def _build_aux_switch(num: int) -> PoolLabSwitchDescription:
    """Build a switch description for an AUX output."""
    flag = SystemFlag(1 << (6 + num))  # AUX1 = bit 7, AUX2 = bit 8, etc.
    return PoolLabSwitchDescription(
        key=f"aux_{num}",
        translation_key=f"aux_{num}",
        icon="mdi:electric-switch",
        is_on_fn=lambda s, n=num: s.aux_modes.get(n, OutputMode.OFF) == OutputMode.ON,
        turn_on_cmd=lambda n=num: cmd_aux(n, OutputMode.ON),
        turn_off_cmd=lambda n=num: cmd_aux(n, OutputMode.OFF),
        available_fn=lambda s, f=flag: bool(s.system_flags & f),
    )


def _build_valve_switch(num: int) -> PoolLabSwitchDescription:
    """Build a switch description for a valve."""
    flag = SystemFlag.VALVE3 if num == 3 else SystemFlag.VALVE4
    return PoolLabSwitchDescription(
        key=f"valve_{num}",
        translation_key=f"valve_{num}",
        icon="mdi:valve",
        is_on_fn=lambda s, n=num: (s.valve3_mode if n == 3 else s.valve4_mode) == OutputMode.ON,
        turn_on_cmd=lambda n=num: cmd_valve(n, OutputMode.ON),
        turn_off_cmd=lambda n=num: cmd_valve(n, OutputMode.OFF),
        available_fn=lambda s, f=flag: bool(s.system_flags & f),
    )


_AUX_SWITCHES = tuple(_build_aux_switch(n) for n in range(1, 10))
_VALVE_SWITCHES = tuple(_build_valve_switch(n) for n in (3, 4))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Lab switch entities."""
    coordinator: PoolLabCoordinator = hass.data[DOMAIN][entry.entry_id]

    all_descriptions = _CORE_SWITCHES + _GROUP_SWITCHES + _AUX_SWITCHES + _VALVE_SWITCHES
    entities = [PoolLabSwitch(coordinator, description, entry) for description in all_descriptions]
    async_add_entities(entities)


class PoolLabSwitch(CoordinatorEntity[PoolLabCoordinator], SwitchEntity):
    """A switch entity for a Pool Lab device."""

    entity_description: PoolLabSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolLabCoordinator,
        description: PoolLabSwitchDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Pool Lab ({entry.data['host']})",
            "manufacturer": "Poolpower Australia",
            "model": "PL MAX Series",
        }

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data)

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

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self.coordinator.async_send_command(self.entity_description.turn_on_cmd())

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self.coordinator.async_send_command(self.entity_description.turn_off_cmd())
