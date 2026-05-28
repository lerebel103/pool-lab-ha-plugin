"""Sensor platform for Pool Lab integration.

Exposes read-only measurement values: water temperature, pH level,
chlorine level, chlorinator output, and pump speed.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolLabCoordinator
from .models import PoolLabState


@dataclass(frozen=True, kw_only=True)
class PoolLabSensorDescription(SensorEntityDescription):
    """Describes a Pool Lab sensor entity."""

    value_fn: Callable[[PoolLabState], float | int | str | None]


SENSOR_DESCRIPTIONS: tuple[PoolLabSensorDescription, ...] = (
    PoolLabSensorDescription(
        key="water_temperature",
        translation_key="water_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.water_temp,
    ),
    PoolLabSensorDescription(
        key="ph_level",
        translation_key="ph_level",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:ph",
        value_fn=lambda state: state.ph_level,
    ),
    PoolLabSensorDescription(
        key="chlorine_level",
        translation_key="chlorine_level",
        native_unit_of_measurement="ppm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flask-outline",
        value_fn=lambda state: state.chlorine_level,
    ),
    PoolLabSensorDescription(
        key="chlorinator_target",
        translation_key="chlorinator_target",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        value_fn=lambda state: state.chlorinator_target,
    ),
    PoolLabSensorDescription(
        key="chlorinator_actual",
        translation_key="chlorinator_actual",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        value_fn=lambda state: state.chlorinator_actual,
    ),
    PoolLabSensorDescription(
        key="pump_speed",
        translation_key="pump_speed",
        icon="mdi:pump",
        value_fn=lambda state: state.pump_speed.name.lower(),
    ),
    PoolLabSensorDescription(
        key="pool_set_temperature",
        translation_key="pool_set_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.pool_set_temp,
    ),
    PoolLabSensorDescription(
        key="spa_set_temperature",
        translation_key="spa_set_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.spa_set_temp,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Lab sensor entities."""
    coordinator: PoolLabCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PoolLabSensor(coordinator, description, entry) for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class PoolLabSensor(CoordinatorEntity[PoolLabCoordinator], SensorEntity):
    """A sensor entity for a Pool Lab device."""

    entity_description: PoolLabSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolLabCoordinator,
        description: PoolLabSensorDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> float | int | str | None:
        """Return the current sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
