"""The dashboard card ships with the integration, and diagnostics work."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.vents_a21.const import MODELS, SHOP_URL
from custom_components.vents_a21.diagnostics import async_get_config_entry_diagnostics


async def test_card_is_served(
    hass: HomeAssistant, entry: MockConfigEntry, hass_client: ClientSessionGenerator
) -> None:
    """The card is loaded by every dashboard without any manual resource."""
    urls = [url for url in hass.data[DATA_EXTRA_MODULE_URL].urls if "vents_a21" in url]
    assert urls == ["/vents_a21/vents-a21-card.js?v=0.1.0"]

    client = await hass_client()
    response = await client.get(urls[0])
    assert response.status == 200
    assert "vents-a21-card" in await response.text()


async def test_diagnostics(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Diagnostics carry the raw tables, without the address or the password."""
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["entry"]["data"]["host"] == "**REDACTED**"
    assert diagnostics["firmware"] == "2.15 (2023-04-18)"
    assert diagnostics["input_registers"]["37"] == 1
    assert diagnostics["holding_registers"]["44"] == 23
    assert "124" not in diagnostics["holding_registers"]


def test_card_knows_every_model() -> None:
    """The filter links of the card follow the model list of the integration."""
    card = Path("custom_components/vents_a21/frontend/vents-a21-card.js").read_text()
    for model in MODELS.values():
        if model.filters_url is None:
            continue
        page = model.filters_url.removeprefix(SHOP_URL).split("?")[0]
        assert f'"{model.name}": "{page}"' in card, model.name
