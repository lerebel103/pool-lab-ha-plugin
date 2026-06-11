"""Number platform for Pool Lab integration.

Exposes adjustable set points: pool/spa temperature targets,
pH target, chlorine target, and chlorinator output percentage.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolLabCoordinator
from .models import PoolLabState
from .protocol import (
    cmd_chlorinator_output,
    cmd_chlorine_target,
    cmd_ph_target,
    cmd_pool_temp_target,
    cmd_spa_temp_target,
)


@dataclass(frozen=True, kw_only=True)
class PoolLabNumberDescription(NumberEntityDescription):
    """Describes a Pool Lab number entity."""

    value_fn: Callable[[PoolLabState], float | None]
    set_value_cmd: Callable[[float], str]


NUMBER_DESCRIPTIONS: tuple[PoolLabNumberDescription, ...] = (
    PoolLabNumberDescription(
        key="pool_temp_target",
        translation_key="pool_temp_target",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=10.0,
        native_max_value=40.0,
        native_step=0.5,
        mode=NumberMode.BOX,
        icon="mdi:thermometer-water",
        value_fn=lambda s: s.pool_set_temp,
        set_value_cmd=lambda v: cmd_pool_temp_target(v),
    ),
    PoolLabNumberDescription(
        key="spa_temp_target",
        translation_key="spa_temp_target",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=10.0,
        native_max_value=40.0,
        native_step=0.5,
        mode=NumberMode.BOX,
        icon="mdi:thermometer-water",
        value_fn=lambda s: s.spa_set_temp,
        set_value_cmd=lambda v: cmd_spa_temp_target(v),
    ),
    PoolLabNumberDescription(
        key="ph_target",
        translation_key="ph_target",
        native_min_value=6.5,
        native_max_value=8.5,
        native_step=0.1,
        mode=NumberMode.BOX,
        icon="mdi:ph",
        value_fn=lambda s: s.ph_target,
        set_value_cmd=lambda v: cmd_ph_target(v),
    ),
    PoolLabNumberDescription(
        key="chlorine_target",
        translation_key="chlorine_target",
        native_unit_of_measurement="ppm",
        native_min_value=0.0,
        native_max_value=9.9,
        native_step=0.1,
        mode=NumberMode.BOX,
        icon="mdi:flask-outline",
        value_fn=lambda s: s.chlorine_target,
        set_value_cmd=lambda v: cmd_chlorine_target(v),
    ),
    PoolLabNumberDescription(
        key="chlorinator_output",
        translation_key="chlorinator_output",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        icon="mdi:gauge",
        value_fn=lambda s: float(s.chlorinator_target),
        set_value_cmd=lambda v: cmd_chlorinator_output(int(v)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Lab number entities."""
    coordinator: PoolLabCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PoolLabNumber(coordinator, description, entry) for description in NUMBER_DESCRIPTIONS
    ]
    async_add_entities(entities)


class PoolLabNumber(CoordinatorEntity[PoolLabCoordinator], NumberEntity):
    """A number entity for a Pool Lab device set point."""

    entity_description: PoolLabNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolLabCoordinator,
        description: PoolLabNumberDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Pool Lab ({entry.data['host']})",
            "manufacturer": "lerebel103",
            "model": "PL MAX Series",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        """Set the new value."""
        command = self.entity_description.set_value_cmd(value)
        await self.coordinator.async_send_command(command)
