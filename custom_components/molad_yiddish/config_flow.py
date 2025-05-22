# /config/custom_components/molad_yiddish/config_flow.py

"""Config flow for Molad Yiddish."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({})

# Default offsets (minutes)
DEFAULT_CANDLELIGHT_OFFSET = 15
DEFAULT_HAVDALAH_OFFSET = 72


class MoladYiddishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Show the form for integration options."""
        if user_input is None:
            # Build a form that includes your existing strip_nikud toggle
            # plus the two new offset fields.
            schema = vol.Schema(
                {
                    vol.Optional(
                        "נעם אראפ די נְקֻודּוֹת",
                        default=self._config_entry.options.get("strip_nikud", False),
                    ): bool,
                    vol.Optional(
                        "וויפיל מינוט פארן שקיעה איז הדלקת הנירות",
                        default=self.config_entry.options.get(
                            "candlelighting_offset", DEFAULT_CANDLELIGHT_OFFSET
                        ),
                    ): int,
                    vol.Optional(
                        "וויפיל מינוט נאכן שקיעה איז מוצאי",
                        default=self.config_entry.options.get(
                            "havdalah_offset", DEFAULT_HAVDALAH_OFFSET
                        ),
                    ): int,
                }
            )
            return self.async_show_form(step_id="init", data_schema=schema)

        # User submitted the form: save all three options
        return self.async_create_entry(title="", data=user_input)
