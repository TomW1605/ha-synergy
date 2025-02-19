# WARNING: this is currently unstable and WILL cause apparent database coruption. this is fully recoverable (the DB isnt actually corrupt) but any data between the corruption and recovering the old DB will be lost. i recomend against using it untill the issues with the historical sensor intergrations have been fixed

# This is still in very early development, the config flow works but none of the fields are labelled and errors are not handled well

# Synergy Custom Integration for Home Assistant


[Synergy](https://github.com/TomW1605/synergyPowerScraper) integration for [home-assistant](https://home-assistant.io/)

Synergy Custom Integration for Home Assistant, providing sensors for Western Australian energy distributor [Synergy](https://www.synergy.net.au/).

**⚠️ Make sure to read the '[FAQ](https://github.com/ldotlopez/ha-ideenergy/blob/main/FAQ.md)', 'Dependencies' and 'Warning' sections**


## Features

* Integration with the Home Assistant Energy Panel.

* Historical sensors (both consumption and solar generation) with better (sub-kWh) precision. This data is not realtime and usually has a 24-hour to 48-hour offset.

* Configuration through [Home Assistant Interface](https://developers.home-assistant.io/docs/config_entries_options_flow_handler) without the need to edit YAML files.

* Fully [asynchronous](https://developers.home-assistant.io/docs/asyncio_index) and integrated with HomeAssistant.


# Everything below here is for the fork source and needs updating
## Dependencies

You must have an i-DE username and access to the Clients' website. You may register here: [Área Clientes | I-DE - Grupo Iberdrola](https://www.i-de.es/consumidores/web/guest/login).

It also necessary to have an "Advanced User" profile. Should you not have one already, you need to fill the request for from your [Profile Area](https://www.i-de.es/consumidores/web/home/personal-area/userData).


## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

1. Copy this repository URL: [https://github.com/ldotlopez/ha-ideenergy](https://github.com/ldotlopez/ha-ideenergy/)

2. In the HACS section, add this repository as a custom one:


  - On the "repositorysitory" field put the URL copied before
  - On the "Category" select "Integration"
  - Click the "Download" button and download latest version.

  ![Custom repositorysitory](https://user-images.githubusercontent.com/59612788/171965822-4a89c14e-9eb2-4134-8de2-1d3f380663e4.png)

3. Restart HA

4. Configure the integration

  - (Option A) Click the "Add integration" button → [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ideenergy)

  - (Option B) Go to "Settings"  "Devices & Services" and click "+ ADD INTEGRATION" and select "i-de.es energy sensors".  
    ![image](https://user-images.githubusercontent.com/59612788/171966005-e58f6b88-a952-4033-82c6-b1d4ea665873.png)

5. Follow the configuration steps: provide your credentials for access to i-DE and select the contract that you want to monitor. (Should you need to add more contracts, just follow the previous step as many times as needed).


### Manually

1. Download/clone this repository: [https://github.com/ldotlopez/ha-ideenergy](https://github.com/ldotlopez/ha-ideenergy/)

2. Copy the `custom_components/ideenergy` folder into your custom_components folder into your HA installation

3. Restart HA

4. Configure the integration

  - (Option A) Click on this button → [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ideenergy)
  - (Option B) Go to "Settings" → "Devices & Services" and click "+ ADD INTEGRATION" and select "i-de.es energy sensors".  
    ![image](https://user-images.githubusercontent.com/59612788/171966005-e58f6b88-a952-4033-82c6-b1d4ea665873.png)

5. Follow the configuration steps: provide your credentials for access to i-DE and select the contract that you want to monitor. (Should you need to add more contracts, just follow the previous step as many times as needed).

## Snapshots

*Accumulated energy sensor*

![snapshot](screenshots/accumulated.png)

*Historical energy sensor*

![snapshot](screenshots/historical.png)

*Configuration wizard*

![snapshot](screenshots/configuration-1.png)
![snapshot](screenshots/configuration-2.png)

## Warnings
This extension provides an 'historical' sensor to incorporate data from the past into Home Assistant database. For your own safety the sensor is not enabled by default and must be enabled manually.

☠️ Historic sensor is based on a **high experimental hack** and can broke and/or corrupt your database and/or statistics. **Use at your own risk**.

## License

This project is licensed under the GNU General Public License v3.0 License - see the LICENSE file for details


## Disclaimer

THIS PROJECT IS NOT IN ANY WAY ASSOCIATED WITH OR RELATED TO THE IBERDROLA GROUP COMPANIES OR ANY OTHER. The information here and online is for educational and resource purposes only and therefore the developers do not endorse or condone any inappropriate use of it, and take no legal responsibility for the functionality or security of your devices.
