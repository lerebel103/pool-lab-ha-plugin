"""Binary sensor platform for Pool Lab integration.

Exposes boolean state indicators: flow detection, faults,
salt warnings, reagent levels, and water analyzer status.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ChlorinatorStatus, SystemStatus, WaterAnalyzerStatus
from .coordinator import PoolLabCoordinator
from .models import PoolLabState


@dataclass(frozen=True, kw_only=True)
class PoolLabBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Pool Lab binary sensor entity."""

    value_fn: Callable[[PoolLabState], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[PoolLabBinarySensorDescription, ...] = (
    # Chlorinator status
    PoolLabBinarySensorDescription(
        key="cell_flow",
        translation_key="cell_flow",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:water-pump",
        value_fn=lambda s: bool(s.chlorinator_status & ChlorinatorStatus.CELLFLOW),
    ),
    PoolLabBinarySensorDescription(
        key="low_flow_fault",
        translation_key="low_flow_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:water-off",
        value_fn=lambda s: bool(s.chlorinator_status & ChlorinatorStatus.LOW_FLOW),
    ),
    PoolLabBinarySensorDescription(
        key="low_salt",
        translation_key="low_salt",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:shaker-outline",
        value_fn=lambda s: bool(s.chlorinator_status & ChlorinatorStatus.LO_SALT),
    ),
    PoolLabBinarySensorDescription(
        key="high_salt",
        translation_key="high_salt",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:shaker",
        value_fn=lambda s: bool(s.chlorinator_status & ChlorinatorStatus.HI_SALT),
    ),
    PoolLabBinarySensorDescription(
        key="cell_output_fault",
        translation_key="cell_output_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle",
        value_fn=lambda s: bool(s.chlorinator_status & ChlorinatorStatus.OUTPUT_FAULT),
    ),
    PoolLabBinarySensorDescription(
        key="pump_protect",
        translation_key="pump_protect",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:shield-alert",
        value_fn=lambda s: bool(s.chlorinator_status & ChlorinatorStatus.PUMP_PROTECT),
    ),
    PoolLabBinarySensorDescription(
        key="chlorinator_active",
        translation_key="chlorinator_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:flash",
        value_fn=lambda s: bool(s.chlorinator_status & ChlorinatorStatus.CHLR_CMD),
    ),
    # System status
    PoolLabBinarySensorDescription(
        key="water_sensor_fault",
        translation_key="water_sensor_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:thermometer-alert",
        value_fn=lambda s: bool(s.system_status & SystemStatus.WATER_SENSOR_FAULT),
    ),
    PoolLabBinarySensorDescription(
        key="solar_hot_sensor_fault",
        translation_key="solar_hot_sensor_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:thermometer-alert",
        value_fn=lambda s: bool(s.system_status & SystemStatus.HOT_SENSOR_FAULT),
    ),
    PoolLabBinarySensorDescription(
        key="solar_cold_sensor_fault",
        translation_key="solar_cold_sensor_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:thermometer-alert",
        value_fn=lambda s: bool(s.system_status & SystemStatus.COLD_SENSOR_FAULT),
    ),
    # Reagent levels
    PoolLabBinarySensorDescription(
        key="reagent_ph",
        translation_key="reagent_ph",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:flask",
        value_fn=lambda s: not s.reagent_ph,  # True = problem (empty)
    ),
    PoolLabBinarySensorDescription(
        key="reagent_chlorine_1",
        translation_key="reagent_chlorine_1",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:flask",
        value_fn=lambda s: not s.reagent_cl1,
    ),
    PoolLabBinarySensorDescription(
        key="reagent_chlorine_2",
        translation_key="reagent_chlorine_2",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:flask",
        value_fn=lambda s: not s.reagent_cl2,
    ),
    # Water analyzer status
    PoolLabBinarySensorDescription(
        key="acid_pump_active",
        translation_key="acid_pump_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:pump",
        value_fn=lambda s: bool(s.water_analyzer_status & WaterAnalyzerStatus.ACID_ON),
    ),
    PoolLabBinarySensorDescription(
        key="chlorine_below_target",
        translation_key="chlorine_below_target",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:flask-minus",
        value_fn=lambda s: bool(s.water_analyzer_status & WaterAnalyzerStatus.SUST_CL_DEV),
    ),
    PoolLabBinarySensorDescription(
        key="ph_above_target",
        translation_key="ph_above_target",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:flask-plus",
        value_fn=lambda s: bool(s.water_analyzer_status & WaterAnalyzerStatus.SUST_PH_DEV),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Lab binary sensor entities."""
    coordinator: PoolLabCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PoolLabBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class PoolLabBinarySensor(CoordinatorEntity[PoolLabCoordinator], BinarySensorEntity):
    """A binary sensor entity for a Pool Lab device."""

    entity_description: PoolLabBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolLabCoordinator,
        description: PoolLabBinarySensorDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
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
        """Return the binary sensor state."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
