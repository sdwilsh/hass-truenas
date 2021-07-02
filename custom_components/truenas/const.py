"""Constants for the FreeNAS integration."""
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

DOMAIN = "truenas"

CONF_AUTH_MODE = "auth_mode"
CONF_AUTH_PASSWORD = "Username + Password"
CONF_AUTH_API_KEY = "API Key"

DEFAULT_SCAN_INTERVAL_SECONDS = 30

SERVICE_JAIL_START = "jail_start"
SCHEMA_SERVICE_JAIL_START = {}
SERVICE_JAIL_STOP = "jail_stop"
SCHEMA_SERVICE_JAIL_STOP = {
    vol.Optional("force"): cv.boolean,
}
SERVICE_JAIL_RESTART = "jail_restart"
SCHEMA_SERVICE_JAIL_RESTART = {}

SERVICE_VM_START = "vm_start"
SCHEMA_SERVICE_VM_START = {
    vol.Optional("overcommit"): cv.boolean,
}
SERVICE_VM_STOP = "vm_stop"
SCHEMA_SERVICE_VM_STOP = {
    vol.Optional("force"): cv.boolean,
}
SERVICE_VM_RESTART = "vm_restart"
SCHEMA_SERVICE_VM_RESTART = {}
