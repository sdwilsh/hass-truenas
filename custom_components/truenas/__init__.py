"""The TrueNAS integration."""
import abc
import asyncio
import logging
from datetime import timedelta
from enum import Enum, unique
from typing import Any, Dict, Optional

import async_timeout
import voluptuous as vol
from aiotruenas_client import CachingMachine as Machine
from aiotruenas_client.websockets.disk import CachingDisk
from aiotruenas_client.websockets.jail import CachingJail
from aiotruenas_client.websockets.pool import CachingPool
from aiotruenas_client.websockets.virtualmachine import CachingVirtualMachine
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify
from websockets.exceptions import WebSocketException

from .const import (
    CONF_AUTH_API_KEY,
    CONF_AUTH_MODE,
    CONF_AUTH_PASSWORD,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = [
    "binary_sensor",
    "sensor",
]
TIMEOUT = 10


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the TrueNAS component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TrueNAS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    password = entry.data[CONF_PASSWORD]
    username = entry.data[CONF_USERNAME]
    api_key = entry.data[CONF_API_KEY]
    try:
        machine = await Machine.create(
            host=host,
            password=password,
            username=username,
            api_key=api_key,
        )

        async def async_update_data():
            """Fetch data from the TrueNAS machine."""
            _LOGGER.debug("refreshing data")
            async with async_timeout.timeout(TIMEOUT):
                try:
                    await asyncio.gather(
                        machine.get_disks(include_temperature=True),
                        machine.get_jails(),
                        machine.get_pools(),
                        machine.get_vms(),
                    )
                except Exception as exc:
                    raise UpdateFailed("Error fetching TrueNAS state") from exc

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS
        )
        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="TrueNAS resource status",
            update_method=async_update_data,
            update_interval=timedelta(seconds=scan_interval),
        )

        # Fetch initial data so we have data when entities subscribe
        await coordinator.async_refresh()

        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "machine": machine,
        }
    except WebSocketException as exc:
        _LOGGER.error(f"Unable to connect to TrueNAS machine: {exc}")
        raise ConfigEntryNotReady

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        await hass.data[DOMAIN][entry.entry_id]["machine"].close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # Version 1 only accepted username and password auth
        data = {**config_entry.data}

        data[CONF_AUTH_MODE] = CONF_AUTH_PASSWORD
        data[CONF_API_KEY] = None

        hass.config_entries.async_update_entry(config_entry, data=data)

        config_entry.version = 2

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True


class TrueNASEntity(RestoreEntity):
    """Define a generic TrueNAS entity."""

    def __init__(
        self, entry: ConfigEntry, name: str, coordinator: DataUpdateCoordinator
    ) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._name = name

    @abc.abstractmethod
    def _get_state(self) -> Any:
        """Retrieve the state."""
        raise NotImplementedError

    @property
    def machine(self) -> Machine:
        assert self.hass is not None
        return self.hass.data[DOMAIN][self._entry.entry_id]["machine"]

    @property
    def should_poll(self):
        """No need to poll!  Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self._coordinator.last_update_success

    async def async_added_to_hass(self):
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update latest state."""
        await self._coordinator.async_request_refresh()


class TrueNASBinarySensor(TrueNASEntity):
    """Define a generic TrueNAS binary sensor."""

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the binary sensor is on."""
        return self._get_state()


class TrueNASSensor(TrueNASEntity):
    """Define a generic TrueNAS sensor."""

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        return self._get_state()


class TrueNASDiskEntity:
    """Represents a disk on the TrueNAS host."""

    _disk: Optional[CachingDisk] = None

    @property
    def available(self) -> bool:
        assert self._disk is not None
        return self._disk.available

    @property
    def device_info(self):
        assert self._disk is not None
        return {
            "identifiers": {
                (DOMAIN, slugify(self._disk.serial)),
            },
            "name": self._disk.name,
            "model": self._disk.model,
        }


class TrueNASPoolEntity:
    """Represents a pool on the TrueNAS host."""

    _pool: Optional[CachingPool] = None

    @property
    def available(self) -> bool:
        assert self._pool is not None
        return self._pool.available

    @property
    def device_info(self):
        assert self._pool is not None
        return {
            "identifiers": {
                (DOMAIN, slugify(self._pool.guid)),
            },
            "name": self._pool.name,
            "manufacturer": f"TrueNAS",
        }

    @property
    def unique_id(self):
        assert self._pool is not None
        return self._pool.guid


class TrueNASJailEntity:
    """Represents a jail on the TrueNAS host."""

    _jail: CachingJail

    @property
    def available(self) -> bool:
        return self._jail.available

    @property
    def device_info(self):
        return {
            "name": self._jail.name,
        }

    async def start(self) -> None:
        """Starts a Jail"""
        assert self.available
        await self._jail.start()

    async def stop(self, force: bool = False) -> None:
        """Starts a Jail"""
        assert self.available
        await self._jail.stop(force=force)

    async def restart(self) -> None:
        """Starts a Jail"""
        assert self.available
        await self._jail.restart()


class TrueNASVirtualMachineEntity:
    """Represents a virtual machine on the TrueNAS host."""

    _vm: CachingVirtualMachine

    @property
    def available(self) -> bool:
        return self._vm.available

    @property
    def device_info(self):
        assert self._vm is not None
        return {
            "name": self._vm.name,
        }

    async def start(self, overcommit: bool = False) -> None:
        """Starts a Virtual Machine"""
        assert self.available
        await self._vm.start(overcommit=overcommit)

    async def stop(self, force: bool = False) -> None:
        """Starts a Virtual Machine"""
        assert self.available
        await self._vm.stop(force=force)

    async def restart(self) -> None:
        """Starts a Virtual Machine"""
        assert self.available
        await self._vm.restart()
