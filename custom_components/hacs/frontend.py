"""Starting setup task: Frontend."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, URL_BASE
from .hacs_frontend import VERSION as FE_VERSION, locate_dir

try:
    from homeassistant.components.frontend import add_extra_js_url
except ImportError:

    def add_extra_js_url(hass: HomeAssistant, url: str, es5: bool = False) -> None:
        hacs: HacsBase = hass.data.get(DOMAIN)
        hacs.log.error("Could not import add_extra_js_url from frontend.")
        if "frontend_extra_module_url" not in hass.data:
            hass.data["frontend_extra_module_url"] = set()
        hass.data["frontend_extra_module_url"].add(url)


if TYPE_CHECKING:
    from .base import HacsBase


async def async_register_frontend(hass: HomeAssistant, hacs: HacsBase) -> None:
    """Register the frontend."""

    # Register frontend
    if hacs.configuration.dev and (frontend_path := os.getenv("HACS_FRONTEND_DIR")):
        hacs.log.warning(
            "<HacsFrontend> Frontend development mode enabled. Do not run in production!"
        )
        hass.http.register_static_path(
            f"{URL_BASE}/frontend", f"{frontend_path}/hacs_frontend", cache_headers=False
        )
        hacs.frontend_version = "dev"
    else:
        hass.http.register_static_path(f"{URL_BASE}/frontend", locate_dir(), cache_headers=False)
        hacs.frontend_version = FE_VERSION

    # Custom iconset
    hass.http.register_static_path(
        f"{URL_BASE}/iconset.js", str(hacs.integration_dir / "iconset.js")
    )
    add_extra_js_url(hass, f"{URL_BASE}/iconset.js")

    # Add to sidepanel if needed
    if DOMAIN not in hass.data.get("frontend_panels", {}):
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=hacs.configuration.sidepanel_title,
            sidebar_icon=hacs.configuration.sidepanel_icon,
            frontend_url_path=DOMAIN,
            config={
                "_panel_custom": {
                    "name": "hacs-frontend",
                    "embed_iframe": True,
                    "trust_external": False,
                    "js_url": f"/hacsfiles/frontend/entrypoint.js?hacstag={hacs.frontend_version}",
                }
            },
            require_admin=True,
        )

    # Setup plugin endpoint if needed
    await hacs.async_setup_frontend_endpoint_plugin()
