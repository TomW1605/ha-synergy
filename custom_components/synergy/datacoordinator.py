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


import enum
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from .SynergyDataFetcher import SynergyDataFetcher
from homeassistant.core import dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .barrier import Barrier, BarrierDeniedError
from .const import (
    DATA_ATTR_HISTORICAL_CONSUMPTION,
    DATA_ATTR_HISTORICAL_GENERATION,
    HISTORICAL_PERIOD_LENGHT,
)
from .entity import SynergyEntity


class DataSetType(int):
    HISTORICAL_CONSUMPTION = 0
    HISTORICAL_GENERATION = 1


_LOGGER = logging.getLogger(__name__)

# _DEFAULT_COORDINATOR_DATA: dict[str, Any] = {
#     DATA_ATTR_MEASURE_ACCUMULATED: None,
#     DATA_ATTR_MEASURE_INSTANT: None,
#     DATA_ATTR_HISTORICAL_CONSUMPTION: {
#         "accumulated": None,
#         "accumulated-co2": None,
#         "historical": [],
#     },
#     DATA_ATTR_HISTORICAL_GENERATION: {
#         "accumulated": None,
#         "accumulated-co2": None,
#         "historical": [],
#     },
#     DATA_ATTR_HISTORICAL_POWER_DEMAND: [],
# }


class SynergyCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass,
        api,
        # barriers: dict[DataSetType, Barrier],
        barrier: Barrier,
        update_interval: timedelta = timedelta(seconds=30),
    ):
        name = (
            f"synergy coordinator"
        )
        super().__init__(hass, _LOGGER, name=name, update_interval=update_interval)
        # self.data: CoordinatorData = {  # type: ignore[assignment]
        #     k: None
        #     for k in [
        #         DATA_ATTR_HISTORICAL_CONSUMPTION,
        #         DATA_ATTR_HISTORICAL_GENERATION,
        #     ]
        # }

        self.api = api
        self.barrier = barrier

        # FIXME: platforms from HomeAssistant should have types
        self.platforms: list[str] = []

        self.sensors: list[SynergyEntity] = []

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.

        See: https://developers.home-assistant.io/docs/integration_fetching_data/
        """

        # Raising 'asyncio.TimeoutError' or 'aiohttp.ClientError' are already
        # handled by the data update coordinator.

        # Raising ConfigEntryAuthFailed will cancel future updates
        # and start a config flow with SOURCE_REAUTH (async_step_reauth)

        # Raise UpdateFailed is something were wrong

        try:
            self.barrier.check()

        except BarrierDeniedError as deny:
            _LOGGER.debug(f"update denied: {deny.reason}")
            return

        end = datetime.today()
        start = end - HISTORICAL_PERIOD_LENGHT

        await self.api.fetch(start_date=start, end_date=end)
        data = self.api.parse()

        self.barrier.success()
        _LOGGER.debug(f"update successful")

        return data

    def register_sensor(self, sensor: SynergyEntity) -> None:
        self.sensors.append(sensor)
        _LOGGER.debug(f"Registered sensor '{sensor.__class__.__name__}'")

    def unregister_sensor(self, sensor: SynergyEntity) -> None:
        self.sensors.remove(sensor)
        _LOGGER.debug(f"Unregistered sensor '{sensor.__class__.__name__}'")

    def update_internal_data(self, data: dict[str, Any]):
        self.data = self.data | data  # type: ignore[assignment]
