"""Config flow for Molad Yiddish."""
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({})

class MoladYiddishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Molad Yiddish."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step (nothing to configure)."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        return self.async_create_entry(title="Molad (ייִדיש)", data={})
