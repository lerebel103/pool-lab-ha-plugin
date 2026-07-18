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
from .entity import build_device_info
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
    """Set up Pool Lab switch entities.

    Only creates entities for hardware that is currently present.
    Removes stale entities from the registry if hardware is no longer present.
    Listens for coordinator updates to dynamically add new entities
    if hardware modules are added.
    """
    from homeassistant.helpers import entity_registry as er

    coordinator: PoolLabCoordinator = hass.data[DOMAIN][entry.entry_id]
    added_keys: set[str] = set()

    # Remove stale entities for hardware that is no longer present
    if coordinator.data is not None:
        registry = er.async_get(hass)
        entries = er.async_entries_for_config_entry(registry, entry.entry_id)
        for entity_entry in entries:
            if entity_entry.domain != "switch":
                continue
            for desc in SWITCH_DESCRIPTIONS:
                uid = f"{entry.unique_id or entry.entry_id}_{desc.key}"
                if entity_entry.unique_id == uid and desc.available_fn is not None:
                    if not desc.available_fn(coordinator.data):
                        registry.async_remove(entity_entry.entity_id)
                    break

    def _check_and_add_entities() -> None:
        """Add entities for newly available hardware."""
        if coordinator.data is None:
            return

        new_entities = []
        for description in SWITCH_DESCRIPTIONS:
            if description.key in added_keys:
                continue
            if description.available_fn is None or description.available_fn(coordinator.data):
                new_entities.append(PoolLabSwitch(coordinator, description, entry))
                added_keys.add(description.key)

        if new_entities:
            async_add_entities(new_entities)

    # Add initially available entities
    _check_and_add_entities()

    # Listen for updates to add entities for newly connected hardware
    entry.async_on_unload(coordinator.async_add_listener(_check_and_add_entities))


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
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = build_device_info(entry)

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
