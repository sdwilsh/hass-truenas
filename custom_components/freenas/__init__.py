"""The FreeNAS integration."""
import abc
import asyncio
import async_timeout
import logging

import voluptuous as vol

from .pyfreenas import Controller, Disk, VirturalMachine

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

from datetime import timedelta
from enum import Enum, unique
from typing import Any, Dict, Optional
from websockets.exceptions import WebSocketException

from .const import (
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
    """Set up the FreeNAS component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FreeNAS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data.get(CONF_HOST)
    password = entry.data.get(CONF_PASSWORD)
    try:
        controller = await Controller.create(host, password)

        async def async_update_data():
            """Fetch data from the FreeNAS machine."""
            _LOGGER.debug("refreshing data")
            async with async_timeout.timeout(TIMEOUT):
                try:
                    await controller.refresh()
                except Exception as exc:
                    raise UpdateFailed("Error fetching FreeNAS state") from exc
                return controller._state

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)
        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="FreeNAS resource status",
            update_method=async_update_data,
            update_interval=timedelta(seconds=scan_interval),
        )

        # Fetch initial data so we have data when entities subscribe
        await coordinator.async_refresh()

        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "controller": controller,
        }
    except WebSocketException as exc:
        _LOGGER.error(f"Unable to connect to FreeNAS machine: {exc}")
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
                hass.config_entries.async_forward_entry_unload(
                    entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        await hass.data[DOMAIN]["controller"]._client.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class FreeNASEntity(RestoreEntity):
    """Define a generic FreeNAS entity."""

    def __init__(self, entry: dict, name: str, coordinator: DataUpdateCoordinator) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._name = name

    @abc.abstractmethod
    def _get_state(self) -> Any:
        """Retrieve the state."""
        raise NotImplementedError

    @property
    def controller(self) -> Controller:
        assert self.hass is not None
        return self.hass.data[DOMAIN][self._entry.entry_id]["controller"]

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


class FreeNASBinarySensor(FreeNASEntity):
    """Define a generic FreeNAS binary sensor."""

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self._get_state()


@unique
class FreeNASEntityType(Enum):
    DISK = "disk"
    VIRTURAL_MACHINE = "virtural_machine"


class FreeNASSensor(FreeNASEntity):
    """Define a generic FreeNAS sensor."""

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._get_state()


class FreeNASDiskEntity:
    """Represents a disk on the FreeNAS host."""

    _disk: Optional[Disk] = None

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

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return device specific state attributes."""
        attributes = {"freenas_type": FreeNASEntityType.DISK.value}
        return attributes


class FreeNASVirturalMachineEntity:
    """Represents a virtural machine on the FreeNAS host."""

    _vm: Optional[VirturalMachine] = None

    @property
    def device_info(self):
        assert self._vm is not None
        return {
            "name": self._vm.name,
        }

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return device specific state attributes."""
        attributes = {"freenas_type": FreeNASEntityType.VIRTURAL_MACHINE.value}
        return attributes

    async def start(self, overcommit: bool = False) -> None:
        """Starts a Virtural Machine"""
        assert self._vm is not None
        await self._vm.start(overcommit=overcommit)

    async def stop(self, force: bool = False) -> None:
        """Starts a Virtural Machine"""
        assert self._vm is not None
        await self._vm.stop(force=force)

    async def restart(self) -> None:
        """Starts a Virtural Machine"""
        assert self._vm is not None
        await self._vm.restart()
