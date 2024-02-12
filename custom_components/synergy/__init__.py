# Copyright (C) 2021-2022 Luis López <luis@cuarentaydos.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


import asyncio
import logging
import math
from datetime import timedelta

from .SynergyDataFetcher import SynergyDataFetcher
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo

from .barrier import TimeDeltaBarrier, TimeWindowBarrier  # NoopBarrier,
from .const import (
    API_USER_SESSION_TIMEOUT,
    CONF_PREMISE_ID,
    DOMAIN,
    MAX_RETRIES,
    MIN_SCAN_INTERVAL,
    UPDATE_WINDOW_END_MINUTE,
    UPDATE_WINDOW_START_MINUTE,
)
from .datacoordinator import DataSetType, SynergyCoordinator
from .updates import update_integration

PLATFORMS: list[str] = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = SynergyAPI(entry)

    device_info = SynergyDeviceInfo(entry.data[CONF_PREMISE_ID])

    coordinator = SynergyCoordinator(
        hass=hass,
        api=api,
        barrier=TimeWindowBarrier(
                allowed_window_hours=(0, 1)
            ),
        # Use default update_interval and relay on barriers for now
        # MEASURE barrier should deny if last attempt (success or not) is too recent to
        # prevent api smashing or subsequent baning
        # update_interval=_calculate_datacoordinator_update_interval(),
        update_interval=timedelta(hours=12),
    )

    # Don't refresh coordinator yet since there isn't any sensor registered
    # await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN] = hass.data.get(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = (coordinator, device_info)

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator, _ = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _calculate_datacoordinator_update_interval() -> timedelta:
    #
    # Calculate SCAN_INTERVAL to allow two updates within the update window
    #
    update_window_width = (
        UPDATE_WINDOW_END_MINUTE * 60 - UPDATE_WINDOW_START_MINUTE * 60
    )
    update_interval = math.floor(update_window_width / 2)
    update_interval = max([MIN_SCAN_INTERVAL, update_interval])

    return timedelta(seconds=update_interval)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry):
    api = SynergyAPI(entry)

    update_integration(hass, entry, SynergyDeviceInfo(entry.data[CONF_PREMISE_ID]))
    return True


def SynergyDeviceInfo(premise_id):
    return DeviceInfo(
        identifiers={
            ("premise_id", premise_id),
        },
        name=premise_id,
    )


def SynergyAPI(entry: ConfigEntry):
    return SynergyDataFetcher(
        premise_id=entry.data[CONF_PREMISE_ID],
        email_address=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        email_server=entry.data[CONF_HOST],
        email_port=entry.data[CONF_PORT],
    )
