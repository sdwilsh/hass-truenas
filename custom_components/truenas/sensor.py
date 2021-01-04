from typing import Callable, List, Optional

from aiotruenas_client import CachingMachine as Machine
from aiotruenas_client.disk import Disk, DiskType
from homeassistant.components.sensor import DEVICE_CLASS_TEMPERATURE
from homeassistant.const import CONF_NAME, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify

from . import TrueNASDiskEntity, TrueNASSensor
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: dict,
    async_add_entities: Callable,
):
    """Set up the TrueNAS switches."""
    entities = _create_entities(hass, entry)
    async_add_entities(entities)


def _get_machine(hass: HomeAssistant, entry: dict) -> Machine:
    machine = hass.data[DOMAIN][entry.entry_id]["machine"]
    assert machine is not None
    return machine


def _create_entities(hass: HomeAssistant, entry: dict) -> List[Entity]:
    entities = []

    machine = _get_machine(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    name = entry.data[CONF_NAME]

    for disk in machine.disks:
        entities.append(DiskTemperatureSensor(entry, name, disk, coordinator))

    return entities


class DiskTemperatureSensor(TrueNASDiskEntity, TrueNASSensor, Entity):
    _disk: Disk

    def __init__(
        self, entry: dict, name: str, disk: Disk, coordinator: DataUpdateCoordinator
    ) -> None:
        self._disk = disk
        super().__init__(entry, name, coordinator)

    @property
    def name(self) -> str:
        """Return the name of the disk."""
        assert self._disk is not None
        return f"Disk {self._disk.serial} Temperature"

    @property
    def unique_id(self) -> str:
        assert self._disk is not None
        return slugify(
            f"{self._entry.unique_id}-{self._disk.serial}_temperature_sensor",
        )

    @property
    def icon(self) -> str:
        """Return an icon for the disk."""
        return "mdi:thermometer"

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_TEMPERATURE

    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    def _get_state(self) -> Optional[int]:
        """Returns the current temperature of the disk."""
        if self.available:
            return self._disk.temperature
        return None
