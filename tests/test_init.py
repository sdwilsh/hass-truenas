"""Tests for init module."""

from custom_components import truenas
from custom_components.truenas.const import CONF_AUTH_MODE, CONF_AUTH_PASSWORD, DOMAIN
from homeassistant.config_entries import CONN_CLASS_CLOUD_POLL, SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_config_flow_entry_migrate(hass):
    """Test that config flow entry is migrated correctly."""
    # Start with the config entry at Version 1.
    old_config_data = {
        CONF_NAME: "TrueNAS",
        CONF_USERNAME: "someusername",
        CONF_PASSWORD: "somepassword",
    }
    expected_new_config_data = {
        CONF_NAME: "TrueNAS",
        CONF_USERNAME: "someusername",
        CONF_PASSWORD: "somepassword",
        CONF_AUTH_MODE: CONF_AUTH_PASSWORD,
        CONF_API_KEY: None,
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=old_config_data,
        title="somehostname",
        version=1,
        source=SOURCE_USER,
        connection_class=CONN_CLASS_CLOUD_POLL,
    )

    entry.add_to_hass(hass)
    await truenas.async_migrate_entry(hass, entry)
    await hass.async_block_till_done()

    # Test that config entry is at the current version with new data
    assert entry.version == 2
    assert entry.data == expected_new_config_data
