"""The detailed snapshot behind the "details" card, and its WebSocket feed."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.vents_a21.alarms import CODES

from .simulator import A21Simulator

SUBSCRIBE = "vents_a21/subscribe_details"


def section(payload: dict, key: str) -> dict | None:
    return next((s for s in payload["sections"] if s["key"] == key), None)


def rows(payload: dict, key: str) -> dict[str, str]:
    found = section(payload, key)
    assert found is not None, f"section {key} missing"
    return {row["label"]: row.get("value", row.get("values")) for row in found["rows"]}


async def subscribe(hass, hass_ws_client, entry, language="fr", device=True):
    client = await hass_ws_client(hass)
    message = {"id": 1, "type": SUBSCRIBE, "language": language}
    if device:
        registry = dr.async_get(hass)
        message["device_id"] = registry.async_get_device(
            {("vents_a21", entry.entry_id)}
        ).id
    await client.send_json(message)
    assert (await client.receive_json())["success"]
    return client, (await client.receive_json())["event"]


def test_every_code_is_described() -> None:
    """Codes 0 to 45 of the manual all have a severity and both languages."""
    assert sorted(CODES) == list(range(46))
    for severity, french, english in CODES.values():
        assert severity in ("alarm", "warning")
        assert french and english


async def test_snapshot(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    _client, payload = await subscribe(hass, hass_ws_client, entry)
    assert payload["name"] == "Zephyr 240 S Connect"
    assert payload["available"] is True and payload["on"] is True
    assert payload["level"] is None
    assert section(payload, "alarms") is None

    fans = section(payload, "fans")
    assert fans["columns"] == ["Soufflage", "Extraction"]
    assert rows(payload, "fans") == {
        "Puissance": ["70 %", "70 %"],
        "Régime": ["1480 tr/min", "1455 tr/min"],
        "Réglage de la vitesse 2": ["70 %", "70 %"],
    }
    temps = rows(payload, "temps")
    assert temps["Air neuf"] == "6,3 °C"
    assert temps["Air rejeté"] == "8,9 °C"
    assert "Retour d'eau" not in temps  # no probe fitted
    state = rows(payload, "state")
    assert state["Mode"] == "Automatique"
    assert state["Vitesse"] == "Vitesse 2"
    assert state["Minuterie"] == "Inactif"
    exchanger = rows(payload, "exchanger")
    assert exchanger["Position du bypass"] == "Fermé"
    assert exchanger["Air dévié"] == "Air neuf"
    assert exchanger["Rendement de récupération"] == "85 %"
    service = rows(payload, "service")
    assert service["Prochain remplacement"] == "dans 62 j 5 h"
    assert service["Fonctionnement cumulé"] == "412 j 7 h"
    assert service["Pile de l'horloge"] == "3,01 V"
    assert service["Modèle"] == "Zephyr 240 S Connect (ZEPH240A21)"
    # No heater, no cooler on this unit: the section is not shown at all.
    assert section(payload, "heating") is None


async def test_optional_probes(
    hass: HomeAssistant,
    simulator: A21Simulator,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Probes that are not installed are left out and listed once."""
    client, payload = await subscribe(hass, hass_ws_client, entry)
    air = section(payload, "air")
    assert [row["label"] for row in air["rows"]] == ["Humidité"]
    assert air["rows"][0]["value"] == "47 %"
    assert air["rows"][0]["hint"] == "seuil 60 %"
    assert [item["label"] for item in air["absent"]] == ["CO₂", "PM2.5", "COV"]
    assert "econology.fr" in air["absent"][0]["url"]
    assert "url" not in air["absent"][1]

    # A CO2 probe is fitted and reads above its threshold; a 0-10 V probe too.
    simulator.set_coil(7, True)
    simulator.set_input(12, 1350)
    simulator.set_discrete(4, True)
    simulator.set_input(40, 60)
    simulator.set_coil(16, True)
    simulator.set_input(18, 35)
    await entry.runtime_data.async_refresh()
    payload = (await client.receive_json())["event"]
    air = section(payload, "air")
    by_label = {row["label"]: row for row in air["rows"]}
    assert by_label["CO₂"]["value"] == "1350 ppm"
    assert by_label["CO₂"]["level"] == "warning"
    assert by_label["Entrée 0-10 V"]["value"] == "35 %"
    assert by_label["Surventilation demandée"]["value"] == "60 %"
    assert [item["label"] for item in air["absent"]] == ["PM2.5", "COV"]


async def test_alarms_in_words(
    hass: HomeAssistant,
    simulator: A21Simulator,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    simulator.set_input(38, 1)
    for code in (0, 38, 40, 50):
        simulator.set_discrete(19 + code, True)
    hass.config.language = "fr"
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    sensor = hass.states.get("sensor.zephyr_240_s_connect_active_alarms")
    assert sensor.state == "4"
    assert sensor.attributes["codes"] == [0, 38, 40, 50]
    # Code 50 is not in the manual: it keeps its number and the overall severity.
    assert sensor.attributes["alarms"] == [
        "0 – Défaut du ventilateur de soufflage",
        "50 – Code 50",
    ]
    assert sensor.attributes["warnings"] == [
        "38 – Bypass en mode manuel",
        "40 – Échéance des filtres atteinte",
    ]
    assert sensor.attributes["active"][0] == {
        "code": 0,
        "type": "alarm",
        "text": "Défaut du ventilateur de soufflage",
    }

    _client, payload = await subscribe(hass, hass_ws_client, entry, language="en")
    assert payload["level"] == "alarm"
    alarms = section(payload, "alarms")
    assert [(r["label"], r["value"], r["level"]) for r in alarms["rows"]] == [
        ("0", "Supply fan fault", "alarm"),
        ("38", "Bypass in manual mode", "warning"),
        ("40", "Filter timer expired", "warning"),
        ("50", "Code 50", "alarm"),
    ]


async def test_bypass_and_rotor(
    hass: HomeAssistant,
    simulator: A21Simulator,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    client, _ = await subscribe(hass, hass_ws_client, entry)
    simulator.set_input(51, 100)
    simulator.set_holding(74, 1)
    simulator.set_holding(110, 1)
    await entry.runtime_data.async_refresh()
    exchanger = rows((await client.receive_json())["event"], "exchanger")
    assert exchanger["Position du bypass"] == "Ouvert"
    assert exchanger["Commande"] == "Forcé ouvert"
    assert exchanger["Air dévié"] == "Air extrait"
    assert "Rendement de récupération" not in exchanger
    bypass = hass.states.get("sensor.zephyr_240_s_connect_bypass_opening")
    assert bypass.state == "100"
    assert bypass.attributes["exchanger"] == "bypass"
    assert bypass.attributes["bypassed_air"] == "extract"

    # Frost protection by the bypass: a hand-driven bypass gets a reminder.
    simulator.set_holding(56, 2)
    await entry.runtime_data.async_refresh()
    exchanger = section((await client.receive_json())["event"], "exchanger")
    control = next(r for r in exchanger["rows"] if r["label"] == "Commande")
    assert control["value"] == "Forcé ouvert"
    assert "repassez en automatique" in control["hint"]
    assert (
        hass.states.get("sensor.zephyr_240_s_connect_bypass_opening").attributes[
            "frost_protection"
        ]
        == "bypass"
    )
    simulator.set_holding(74, 2)  # back to automatic: no reminder
    await entry.runtime_data.async_refresh()
    exchanger = section((await client.receive_json())["event"], "exchanger")
    control = next(r for r in exchanger["rows"] if r["label"] == "Commande")
    assert control["value"] == "Automatique"
    assert "hint" not in control
    simulator.set_holding(74, 1)

    # Heat is still recovered when indoor and outdoor air are close, only
    # the figure is missing: the row says so instead of vanishing.
    simulator.set_input(51, 0)
    simulator.set_temperature(1, 19.0)
    await entry.runtime_data.async_refresh()
    exchanger = section((await client.receive_json())["event"], "exchanger")
    row = next(
        r for r in exchanger["rows"] if r["label"] == "Rendement de récupération"
    )
    assert row["value"] == "Non mesurable"
    assert "2,4 °C d'écart, il en faut 4 °C" in row["hint"]
    simulator.set_temperature(1, 6.3)

    simulator.set_holding(57, 4)  # modulating rotary exchanger
    simulator.set_input(51, 40)
    simulator.set_input(45, 40)
    await entry.runtime_data.async_refresh()
    exchanger = rows((await client.receive_json())["event"], "exchanger")
    assert exchanger["Échangeur rotatif"] == "Ralenti à 60 %"
    assert exchanger["Commande envoyée"] == "40 %"
    assert "Air dévié" not in exchanger


async def test_feed_follows_the_unit(
    hass: HomeAssistant,
    simulator: A21Simulator,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Unreachable, back, reloaded: the card is told each time."""
    # Without a device id, the only unit is used.
    client, payload = await subscribe(hass, hass_ws_client, entry, device=False)
    assert payload["available"] is True

    port = simulator.port
    await simulator.stop()
    await entry.runtime_data.async_refresh()
    payload = (await client.receive_json())["event"]
    assert payload == {
        "name": "Zephyr 240 S Connect",
        "available": False,
        "sections": [],
    }

    simulator.port = port
    await simulator.start()
    await entry.runtime_data.async_refresh()
    assert (await client.receive_json())["event"]["available"] is True

    await hass.config_entries.async_reload(entry.entry_id)
    assert (await client.receive_json())["event"] == {"reload": True}


async def test_unknown_unit(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": SUBSCRIBE, "device_id": "nope"})
    answer = await client.receive_json()
    assert answer["success"] is False
    assert answer["error"]["code"] == "not_found"
