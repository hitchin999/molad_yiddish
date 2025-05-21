# /config/custom_components/molad_yiddish/config_flow.py

"""Config flow for Molad Yiddish."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({})


class MoladYiddishConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle a config flow for Molad Yiddish."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step (nothing to configure)."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        return self.async_create_entry(title="Molad Yiddish", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Define an options flow for this integration."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Molad Yiddish options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Show the form to toggle stripping of nikud."""
        if user_input is None:
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            "strip_nikud",
                            default=self.config_entry.options.get(
                                "strip_nikud", False
                            ),
                        ): bool,
                    }
                ),
            )

        return self.async_create_entry(title="", data=user_input)
