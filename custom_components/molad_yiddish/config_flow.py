"""
Molad Yiddish config flow
"""
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

class MoladYiddishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Molad Yiddish config flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({}),
            )
        return self.async_create_entry(
            title="Molad (ייִדיש)",
            data={},
        )
