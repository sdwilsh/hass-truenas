"""Config flow for TrueNAS integration."""
import logging
from typing import Any, Dict, Mapping, Optional

import voluptuous as vol
from aiotruenas_client import CachingMachine as Machine
from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from websockets.exceptions import InvalidURI, SecurityError

from .const import (  # pylint:disable=unused-import
    CONF_AUTH_API_KEY,
    CONF_AUTH_MODE,
    CONF_AUTH_PASSWORD,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_AUTH_MODE): vol.In([CONF_AUTH_PASSWORD, CONF_AUTH_API_KEY]),
        vol.Optional(CONF_NAME, default="TrueNAS"): str,
    }
)

DATA_SCHEMA_PASSWORD = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    },
)

DATA_SCHEMA_API_KEY = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    },
)


async def validate_input(hass: core.HomeAssistant, data) -> Dict:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    try:
        machine = await Machine.create(
            host=data[CONF_HOST],
            password=data[CONF_PASSWORD],
            username=data[CONF_USERNAME],
            api_key=data[CONF_API_KEY],
        )
    except SecurityError as exc:
        raise InvalidAuth from exc
    except InvalidURI as exc:
        raise CannotConnect from exc

    info = await machine.get_system_info()
    await machine.close()
    return {
        "hostname": info["hostname"],
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FreeNAS."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    _user_data: Dict[str, Any] = {}

    async def async_step_user(self, user_input: Optional[Mapping[str, Any]] = None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            self._user_data = dict(user_input)
            if user_input[CONF_AUTH_MODE] == CONF_AUTH_PASSWORD:
                return await self.async_step_auth_password()
            elif user_input[CONF_AUTH_MODE] == CONF_AUTH_API_KEY:
                return await self.async_step_auth_api_key()
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA_USER, errors=errors
        )

    async def async_step_auth_password(
        self, user_input: Optional[Mapping[str, Any]] = None
    ):
        errors = {}
        if user_input is not None:
            self._user_data.update(user_input)
            self._user_data[CONF_API_KEY] = None
            try:
                info = await validate_input(self.hass, self._user_data)
                return self.async_create_entry(
                    title=info["hostname"], data=self._user_data
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="auth_password", data_schema=DATA_SCHEMA_PASSWORD, errors=errors
        )

    async def async_step_auth_api_key(
        self, user_input: Optional[Mapping[str, Any]] = None
    ):
        errors = {}
        if user_input is not None:
            self._user_data.update(user_input)
            self._user_data[CONF_PASSWORD] = None
            self._user_data[CONF_USERNAME] = None
            try:
                info = await validate_input(self.hass, self._user_data)
                return self.async_create_entry(
                    title=info["hostname"], data=self._user_data
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="auth_api_key", data_schema=DATA_SCHEMA_API_KEY, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
