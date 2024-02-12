#
# Copyright (C) 2021 Luis López <luis@cuarentaydos.com>
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


import os
from typing import Any

from .SynergyDataFetcher import SynergyDataFetcher, get_premise_id, AddressError
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_EMAIL, CONF_PASSWORD, CONF_HOST, CONF_PORT
from homeassistant.core import callback  # noqa: F401
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from . import _LOGGER
from .const import CONF_PREMISE_ID, CONFIG_ENTRY_VERSION, DOMAIN

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS, msg="Synergy Account Address"): str,
        vol.Required(CONF_EMAIL, msg="Email Address"): str,
        vol.Required(CONF_PASSWORD, msg="Email Password"): str,
        vol.Required(CONF_HOST, msg="Email Host"): str,
        vol.Optional(CONF_PORT, msg="Email Port", default=993): int,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    VERSION = CONFIG_ENTRY_VERSION

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info = {}
        self.api = None

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            # Not used correctly, check
            # https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#unique-ids
            #
            # await self.async_set_unique_id(user_input[CONF_NAME])
            # self._abort_if_unique_id_configured()

            physical_address= user_input[CONF_ADDRESS]
            email_address = user_input[CONF_EMAIL]
            email_password = user_input[CONF_PASSWORD]
            email_server = user_input[CONF_HOST]
            email_port = user_input[CONF_PORT]

            premise_id = None
            try:
                premise_id = get_premise_id(physical_address)

            except AddressError:
                errors["base"] = "invalid_address"

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if  premise_id is not None:
                try:
                    self.api = await create_api(premise_id, email_address, email_password, email_server, email_port)

                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

                else:
                    self.info.update(
                        {
                            CONF_PREMISE_ID: premise_id,
                            CONF_EMAIL: email_address,
                            CONF_PASSWORD: email_password,
                            CONF_HOST: email_server,
                            CONF_PORT: email_port,
                        }
                    )
                    title = f"Premise {premise_id}"
                    return self.async_create_entry(title=title, data=self.info)

        return self.async_show_form(
            step_id="user",
            data_schema=AUTH_SCHEMA,
            errors=errors,
        )


# class OptionsFlowHandler(config_entries.OptionsFlow):
#     def __init__(self, config_entry):
#         """Initialize options flow."""
#         self.config_entry = config_entry
#
#     async def async_step_init(self, user_input=None):
#         if user_input is not None:
#             return self.async_create_entry(title="", data=user_input)
#
#         OPTIONS_SCHEMA = vol.Schema({})
#
#         return self.async_show_form(step_id="init", data_schema=OPTIONS_SCHEMA)


async def create_api(premise_id, email_address, email_password, email_server, email_port):
    return SynergyDataFetcher(
        premise_id=premise_id,
        email_address=email_address,
        password=email_password,
        email_server=email_server,
        email_port=email_port,
    )
