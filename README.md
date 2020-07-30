[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

# FreeNAS Integration for Home Assistant

## Features

- Virtural machines and their running state
- Disks and their temperature

## Installation

1. Install using [HACS](https://github.com/custom-components/hacs). Or install manually by copying `custom_components/freenas` folder into `<config_dir>/custom_components`
2. Restart Home Assistant.
3. In the Home Assistant UI, navigate to `Configuration` then `Integrations`. Click on the add integration button at the bottom right and select `FreeNAS`. Fill out the options and save.
   - Host: the ip address or hostname of the FreeNAS server.
   - Username: the username used to login to the FreeNAS server.
   - Password: the password used to login to the FreeNAS server.

## Using Services

### freenas.vm_start

### freenas.vm_stop

### freenas.vm_restart