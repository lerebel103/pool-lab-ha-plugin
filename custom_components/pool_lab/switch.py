"""Switch platform for Pool Lab integration.

Exposes true binary on/off controls: heater, solar heat, and pool/spa mode.
Tri-state controls (OFF/ON/AUTO) are handled by the select platform.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OutputMode, PoolSpaMode, SystemFlag
from .coordinator import PoolLabCoordinator
from .models import PoolLabState
from .protocol import (
    cmd_heater,
    cmd_pool_spa,
    cmd_solar_heat,
)


@dataclass(frozen=True, kw_only=True)
class PoolLabSwitchDescription(SwitchEntityDescription):
    """Describes a Pool Lab switch entity."""

    is_on_fn: Callable[[PoolLabState], bool]
    turn_on_cmd: Callable[[], str]
    turn_off_cmd: Callable[[], str]
    available_fn: Callable[[PoolLabState], bool] | None = None


SWITCH_DESCRIPTIONS: tuple[PoolLabSwitchDescription, ...] = (
    PoolLabSwitchDescription(
        key="spa_mode",
        translation_key="spa_mode",
        icon="mdi:hot-tub",
        is_on_fn=lambda s: s.spa_mode == PoolSpaMode.SPA,
        turn_on_cmd=lambda: cmd_pool_spa(PoolSpaMode.SPA),
        turn_off_cmd=lambda: cmd_pool_spa(PoolSpaMode.POOL),
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Lab switch entities."""
    coordinator: PoolLabCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PoolLabSwitch(coordinator, description, entry) for description in SWITCH_DESCRIPTIONS
    ]
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
