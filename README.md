[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![hacs](https://github.com/sdwilsh/hass-truenas/workflows/hacs/badge.svg)
![hassfest](https://github.com/sdwilsh/hass-truenas/workflows/hassfest/badge.svg)

# TrueNAS Integration for Home Assistant

## Features

- Virtual machines and their running state
- Disks and their temperature

## Installation

1. Install using [HACS](https://github.com/custom-components/hacs). Or install manually by copying `custom_components/truenas` folder into `<config_dir>/custom_components`
2. Restart Home Assistant.
3. In the Home Assistant UI, navigate to `Configuration` then `Integrations`. Click on the add integration button at the bottom right and select `TrueNAS`. Fill out the options and save.
   - Host: the ip address or hostname of the TrueNAS server.
   - Username: the username used to login to the TrueNAS server.
   - Password: the password used to login to the TrueNAS server.

## Using Services

### truenas.vm_start

### truenas.vm_stop

### truenas.vm_restart

## Development

```
python3.8 -m venv .venv
source .venv/bin/activate

# Install Dev Requirements
pip install -r requirements-dev.txt

# One-Time Install of Commit Hooks
pre-commit install
```
