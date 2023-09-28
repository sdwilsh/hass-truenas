"""Constants for the FreeNAS integration."""
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

DOMAIN = "truenas"

ATTR_ENCRYPT = "Encrypted"
ATTR_POOL_GUID = "GUID"
ATTR_POOL_IS_DECRYPTED = "Is Decrypted"
ATTR_POOL_NAME = "Pool Name"

CONF_AUTH_MODE = "auth_mode"
CONF_AUTH_PASSWORD = "Username + Password"
CONF_AUTH_API_KEY = "API Key"

DEFAULT_NAME: str = "TrueNAS"
DEFAULT_SCAN_INTERVAL_SECONDS = 30

SERVICE_JAIL_START = "jail_start"
SCHEMA_SERVICE_JAIL_START = vol.Schema({})
SERVICE_JAIL_STOP = "jail_stop"
SCHEMA_SERVICE_JAIL_STOP = vol.Schema(
    {
        vol.Optional("force"): cv.boolean,
    }
)
SERVICE_JAIL_RESTART = "jail_restart"
SCHEMA_SERVICE_JAIL_RESTART = vol.Schema({})

SERVICE_VM_START = "vm_start"
SCHEMA_SERVICE_VM_START = vol.Schema(
    {
        vol.Optional("overcommit"): cv.boolean,
    }
)
SERVICE_VM_STOP = "vm_stop"
SCHEMA_SERVICE_VM_STOP = vol.Schema(
    {
        vol.Optional("force"): cv.boolean,
    }
)
SERVICE_VM_RESTART = "vm_restart"
SCHEMA_SERVICE_VM_RESTART = vol.Schema({})
