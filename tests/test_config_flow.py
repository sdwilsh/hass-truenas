"""Test the TrueNAS config flow."""
from unittest.mock import patch

import pytest
from custom_components.truenas.config_flow import CannotConnect, InvalidAuth
from custom_components.truenas.const import DOMAIN
from homeassistant import config_entries, setup
from websockets.exceptions import InvalidURI, SecurityError


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def test_form_password(hass):
    """Test we get the forms using password auth."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "custom_components.truenas.config_flow.Machine.create",
    ) as mock_machine, patch(
        "custom_components.truenas.async_setup", return_value=True
    ) as mock_setup, patch(
        "custom_components.truenas.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:

        mock_machine.return_value.get_system_info.return_value = {
            "hostname": "somehostname"
        }

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "name": "TrueNAS",
                "auth_mode": "Username + Password",
            },
        )
        await hass.async_block_till_done()

        assert result2["type"] == "form"
        assert result2["step_id"] == "auth_password"

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )
        await hass.async_block_till_done()

        assert result3["type"] == "create_entry"
        assert result3["title"] == "somehostname"

        assert result3["data"] == {
            "host": "1.1.1.1",
            "username": "test-username",
            "password": "test-password",
            "name": "TrueNAS",
            "auth_mode": "Username + Password",
            "api_key": None,
        }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_api_key(hass):
    """Test we get the forms using api key auth."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "custom_components.truenas.config_flow.Machine.create",
    ) as mock_machine, patch(
        "custom_components.truenas.async_setup", return_value=True
    ) as mock_setup, patch(
        "custom_components.truenas.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:

        mock_machine.return_value.get_system_info.return_value = {
            "hostname": "somehostname"
        }

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "name": "TrueNAS",
                "auth_mode": "API Key",
            },
        )
        await hass.async_block_till_done()

        assert result2["type"] == "form"
        assert result2["step_id"] == "auth_api_key"

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                "api_key": "someapikey",
            },
        )
        await hass.async_block_till_done()

        assert result3["type"] == "create_entry"
        assert result3["title"] == "somehostname"

        assert result3["data"] == {
            "host": "1.1.1.1",
            "username": None,
            "password": None,
            "name": "TrueNAS",
            "auth_mode": "API Key",
            "api_key": "someapikey",
        }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(hass):
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.truenas.config_flow.Machine.create",
        side_effect=SecurityError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "name": "TrueNAS",
                "auth_mode": "API Key",
            },
        )
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                "api_key": "someapikey",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] == "form"
    assert result3["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.truenas.config_flow.Machine.create",
        side_effect=InvalidURI(uri="1.1.1.1", msg="invalid_uri"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "name": "TrueNAS",
                "auth_mode": "API Key",
            },
        )
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                "api_key": "someapikey",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] == "form"
    assert result3["errors"] == {"base": "cannot_connect"}
