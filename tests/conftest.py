"""Fixtures: a simulated A21 controller and a configured integration."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vents_a21.const import CONF_MODEL, CONF_UNIT_ID, DOMAIN

from .simulator import A21Simulator

DEVICE = "zephyr_240_s_connect"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load the integration from custom_components."""


@pytest.fixture(autouse=True)
def _no_identity_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip the UDP question to the unit (3 s of silence from the simulator)."""

    async def nothing(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(
        "custom_components.vents_a21.coordinator.async_read_identifier", nothing
    )


@pytest.fixture
async def simulator(socket_enabled: None) -> AsyncGenerator[A21Simulator]:
    """Run a simulated controller on a free local port."""
    sim = A21Simulator()
    await sim.start()
    yield sim
    await sim.stop()


def make_entry(sim: A21Simulator, model: str = DEVICE) -> MockConfigEntry:
    """Return a config entry pointing at the simulator."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Zephyr 240 S Connect",
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: sim.port,
            CONF_UNIT_ID: 1,
            CONF_MODEL: model,
        },
    )


async def setup_entry(hass: HomeAssistant, sim: A21Simulator) -> MockConfigEntry:
    """Set the integration up against the simulator."""
    entry = make_entry(sim)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def entry(hass: HomeAssistant, simulator: A21Simulator) -> MockConfigEntry:
    """Return the integration set up against the simulator."""
    return await setup_entry(hass, simulator)
