"""Internal config flow contract for Adaptive Control."""

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN


class AdaptiveControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Reject user setup until the first concrete Controller Type ships."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Prevent creation of an entry without a valid runtime type."""
        return self.async_abort(reason="no_controller_types")
