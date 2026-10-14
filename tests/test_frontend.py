"""The dashboard card ships with the integration, and diagnostics work."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.components.lovelace import LOVELACE_DATA
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.vents_a21 import _async_register_resource
from custom_components.vents_a21.const import MODELS, SHOP_URL
from custom_components.vents_a21.diagnostics import async_get_config_entry_diagnostics


CARD = "/vents_a21/vents-a21-card.js?v=0.2.9"


async def test_card_is_served(
    hass: HomeAssistant, entry: MockConfigEntry, hass_client: ClientSessionGenerator
) -> None:
    """The card is a dashboard resource, registered without any manual step."""
    resources = hass.data[LOVELACE_DATA].resources
    urls = [item["url"] for item in resources.async_items() if "vents_a21" in item["url"]]
    assert urls == [CARD]
    assert [item["type"] for item in resources.async_items() if item["url"] == CARD] == [
        "module"
    ]
    # Not also as an extra module: the card would load twice.
    assert not [url for url in hass.data[DATA_EXTRA_MODULE_URL].urls if "vents_a21" in url]

    client = await hass_client()
    response = await client.get(urls[0])
    assert response.status == 200
    card = await response.text()
    assert '"vents-a21-card"' in card
    assert '"vents-a21-details-card"' in card


async def test_resource_follows_the_version(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """An old resource of the card is updated in place rather than duplicated."""
    resources = hass.data[LOVELACE_DATA].resources
    item = next(i for i in resources.async_items() if i["url"] == CARD)
    await resources.async_update_item(item["id"], {"url": "/vents_a21/vents-a21-card.js?v=0.1.0"})
    assert await _async_register_resource(hass, CARD)
    urls = [i["url"] for i in resources.async_items() if "vents_a21" in i["url"]]
    assert urls == [CARD]


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
