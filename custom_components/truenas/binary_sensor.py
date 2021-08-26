from typing import Callable, List, Optional

from aiotruenas_client import CachingMachine as Machine
from aiotruenas_client.pool import PoolStatus
from aiotruenas_client.websockets.jail import CachingJail, JailStatus
from aiotruenas_client.websockets.pool import CachingPool
from aiotruenas_client.websockets.virtualmachine import (
    CachingVirtualMachine,
    VirtualMachineState,
)
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify

from . import (
    TrueNASBinarySensor,
    TrueNASJailEntity,
    TrueNASPoolEntity,
    TrueNASVirtualMachineEntity,
)
from .const import (
    DOMAIN,
    SCHEMA_SERVICE_JAIL_RESTART,
    SCHEMA_SERVICE_JAIL_START,
    SCHEMA_SERVICE_JAIL_STOP,
    SCHEMA_SERVICE_VM_RESTART,
    SCHEMA_SERVICE_VM_START,
    SCHEMA_SERVICE_VM_STOP,
    SERVICE_JAIL_RESTART,
    SERVICE_JAIL_START,
    SERVICE_JAIL_STOP,
    SERVICE_VM_RESTART,
    SERVICE_VM_START,
    SERVICE_VM_STOP,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable,
):
    """Set up the TrueNAS switches."""
    entities = _create_entities(hass, entry)
    async_add_entities(entities)

    platform = entity_platform.current_platform.get()
    assert platform != None
    platform.async_register_entity_service(
        SERVICE_JAIL_START,
        SCHEMA_SERVICE_JAIL_START,
        "start",
    )
    platform.async_register_entity_service(
        SERVICE_JAIL_STOP,
        SCHEMA_SERVICE_JAIL_STOP,
        "stop",
    )
    platform.async_register_entity_service(
        SERVICE_JAIL_RESTART,
        SCHEMA_SERVICE_JAIL_RESTART,
        "restart",
    )
    platform.async_register_entity_service(
        SERVICE_VM_START,
        SCHEMA_SERVICE_VM_START,
        "start",
    )
    platform.async_register_entity_service(
        SERVICE_VM_STOP,
        SCHEMA_SERVICE_VM_STOP,
        "stop",
    )
    platform.async_register_entity_service(
        SERVICE_VM_RESTART,
        SCHEMA_SERVICE_VM_RESTART,
        "restart",
    )


def _get_machine(hass: HomeAssistant, entry: ConfigEntry) -> Machine:
    machine = hass.data[DOMAIN][entry.entry_id]["machine"]
    assert machine is not None
    return machine


def _create_entities(hass: HomeAssistant, entry: ConfigEntry) -> List[Entity]:
    entities = []

    machine = _get_machine(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    name = entry.data[CONF_NAME]

    for jail in machine.jails:
        entities.append(JailIsRunningBinarySensor(entry, name, jail, coordinator))
    for vm in machine.vms:
        entities.append(
            VirturalMachineIsRunningBinarySensor(entry, name, vm, coordinator)
        )
    for pool in machine.pools:
        entities.append(PoolIsDecryptedBinarySensor(entry, name, pool, coordinator))

    return entities


class JailIsRunningBinarySensor(
    TrueNASJailEntity, TrueNASBinarySensor, BinarySensorEntity
):
    def __init__(
        self,
        entry: ConfigEntry,
        name: str,
        jail: CachingJail,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        self._jail = jail
        super().__init__(entry, name, coordinator)

    @property
    def name(self) -> str:
        """Return the name of the jail."""
        return f"{self._jail.name} Jail Running"

    @property
    def unique_id(self) -> str:
        return slugify(
            f"{self._entry.unique_id}-{self._jail.name}_binary_sensor",
        )

    @property
    def icon(self) -> str:
        """Return an icon for the jail."""
        return "mdi:server"

    def _get_state(self) -> Optional[bool]:
        """Returns the current state of the jail."""
        if self._jail.available:
            return self._jail.status == JailStatus.UP
        return None


class PoolIsDecryptedBinarySensor(
    TrueNASPoolEntity, TrueNASBinarySensor, BinarySensorEntity
):
    def __init__(
        self,
        entry: ConfigEntry,
        name: str,
        pool: CachingPool,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        self._pool = pool
        super().__init__(entry, name, coordinator)

    @property
    def name(self) -> str:
        """Return the pool decryption status"""
        assert self._pool is not None
        return f"{self._pool.name} Pool Is Decrypted"

    @property
    def unique_id(self):
        assert self._pool is not None
        return f"{self._pool.name}_is_decrypted_binary_sensor"

    @property
    def icon(self) -> str:
        """Return an icon for the pool."""
        return "mdi:database"

    @property
    def entity_registry_enabled_default(self) -> bool:
        return False

    def _get_state(self) -> Optional[bool]:
        """Returns the current encryption status of the pool."""
        assert self._pool is not None
        return self._pool.is_decrypted


class VirturalMachineIsRunningBinarySensor(
    TrueNASVirtualMachineEntity, TrueNASBinarySensor, BinarySensorEntity
):
    def __init__(
        self,
        entry: ConfigEntry,
        name: str,
        virtural_machine: CachingVirtualMachine,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        self._vm = virtural_machine
        super().__init__(entry, name, coordinator)

    @property
    def name(self) -> str:
        """Return the name of the virtural machine."""
        return f"{self._vm.name} Virtural Machine Running"

    @property
    def unique_id(self) -> str:
        return slugify(
            f"{self._entry.unique_id}-{self._vm.id}_binary_sensor",
        )

    @property
    def icon(self) -> str:
        """Return an icon for the virtural machine."""
        return "mdi:server"

    def _get_state(self) -> Optional[bool]:
        """Returns the current state of the virtural machine."""
        if self._vm.available:
            return self._vm.status == VirtualMachineState.RUNNING
        return None
