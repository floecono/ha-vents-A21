"""Read and write an A21 controller over Modbus TCP."""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from .alarms import ALARM, WARNING, ActiveCode, describe
from .const import (
    ALARM_CODE_COUNT,
    CL_POWER,
    COIL_COUNT,
    DI_ALARM_FIRST,
    DI_STATUS_COOLER,
    DI_STATUS_HEATER,
    DISCRETE_COUNT,
    HOLDING_COUNT,
    HR_MAX_SPEED_MODE,
    INPUT_COUNT,
    IR_ALARM,
    IR_BYPASS_STATE,
    IR_DEVICE_TYPE,
    IR_FIRMWARE,
    IR_PREHEATER_OUTPUT,
    IR_EXTRACT_RPM,
    IR_RH_EXT,
    IR_RH_INT,
    IR_SUPPLY_RPM,
    IR_TEMP_EXHAUST,
    IR_TEMP_EXTRACT,
    IR_TEMP_OUTDOOR,
    IR_TEMP_SUPPLY,
    IR_TIMER_HOURS,
    IR_TIMER_MIN_SEC,
    IR_WORK_DAYS,
    IR_WORK_HOURS_MIN,
    TEMP_NO_SENSOR,
    TEMP_SHORT_CIRCUIT,
)
from .modbus import (
    EXC_ILLEGAL_DATA_ADDRESS,
    ModbusConnectionError,
    ModbusError,
    ModbusExceptionResponse,
    ModbusTcpClient,
)

_LOGGER = logging.getLogger(__name__)

# IR_ALARM: 0 none, 1 at least one alarm, 2 warnings only.
ALARM_LEVELS = ("ok", "alarm", "warning")

# Below this indoor/outdoor difference the efficiency figure is only noise:
# the error of the three probes is divided by that difference.
MIN_EFFICIENCY_DELTA = 4.0

# Why the efficiency can or cannot be worked out (A21Data.efficiency_status).
EFFICIENCY_MEASURED = "measured"
EFFICIENCY_OFF = "off"
EFFICIENCY_NO_PROBE = "no_probe"
EFFICIENCY_BYPASS = "bypass"
EFFICIENCY_HEATING = "heating"
EFFICIENCY_COOLING = "cooling"
EFFICIENCY_PREHEATING = "preheating"
EFFICIENCY_SMALL_DIFFERENCE = "small_difference"
# The supply fan is stopped while the extract fan runs: frost protection by
# fan stop (or its second stage behind a bypass that does not cope). The
# supply probe then sees still air and every figure is meaningless.
EFFICIENCY_DEFROSTING = "defrosting"

# Without a humidity probe, exhaust air this cold is taken to be condensing:
# the dew point of indoor air in winter sits between 6 and 10 °C.
CONDENSATION_GUESS_BELOW = 8.0
# Margin under the dew point: the plates are colder than the air leaving them.
CONDENSATION_MARGIN = 1.0
# Time the controller gets to apply a write before the state is read back.
_SETTLE_DELAY = 0.3
# The controller accepts a single TCP client; right after a disconnection it
# can refuse the next connection for a moment.
_CONNECT_RETRY_DELAY = 0.6


@dataclass(frozen=True, slots=True)
class CoilWrite:
    """Write one coil."""

    address: int
    value: bool


@dataclass(frozen=True, slots=True)
class RegisterWrite:
    """Write one holding register."""

    address: int
    value: int


Write = CoilWrite | RegisterWrite


def _signed(value: int) -> int:
    return value - 0x10000 if value > 0x7FFF else value


@dataclass(slots=True)
class A21Data:
    """One snapshot of the controller.

    A value is None when the firmware does not expose that address.
    """

    coils: list[bool | None]
    discrete: list[bool | None]
    inputs: list[int | None]
    holdings: list[int | None]
    # Alarm codes the owner asked not to be told about (see CONF_MANUAL_BYPASS).
    ignored_codes: frozenset[int] = frozenset()

    def coil(self, address: int) -> bool | None:
        """Return a coil."""
        return self.coils[address]

    def di(self, address: int) -> bool | None:
        """Return a discrete input."""
        return self.discrete[address]

    def ir(self, address: int) -> int | None:
        """Return a raw input register."""
        return self.inputs[address]

    def hr(self, address: int) -> int | None:
        """Return a raw holding register."""
        return self.holdings[address]

    def temperature(self, address: int) -> float | None:
        """Return an input register as °C, None without a working sensor."""
        raw = self.inputs[address]
        if raw is None or raw in (TEMP_NO_SENSOR, TEMP_SHORT_CIRCUIT):
            return None
        return _signed(raw) / 10

    @property
    def is_on(self) -> bool:
        """Return True when the unit is switched on."""
        return bool(self.coils[CL_POWER])

    @property
    def max_speed(self) -> int:
        """Return the number of preset speeds (3 to 5)."""
        raw = self.holdings[HR_MAX_SPEED_MODE]
        return min(max(raw, 1), 5) if raw else 3

    @property
    def alarm_codes(self) -> list[int]:
        """Return the active alarm codes (0 to 52), minus the ignored ones."""
        return [
            code
            for code in range(ALARM_CODE_COUNT)
            if self.discrete[DI_ALARM_FIRST + code] and code not in self.ignored_codes
        ]

    @property
    def ignored_active(self) -> bool:
        """Return True when an ignored code is active right now."""
        return any(self.discrete[DI_ALARM_FIRST + code] for code in self.ignored_codes)

    @property
    def alarm_level(self) -> str | None:
        """Return "ok", "alarm" or "warning", as the unit reports it.

        When an ignored code is active, the unit's own register still counts
        it, so the level is worked out again from the remaining codes.
        """
        raw = self.inputs[IR_ALARM]
        if raw is None:
            return None
        if not self.ignored_active:
            return ALARM_LEVELS[raw] if raw < len(ALARM_LEVELS) else None
        codes = self.active_codes(None)
        if any(item.severity == ALARM for item in codes):
            return "alarm"
        return "warning" if codes else "ok"

    @property
    def temperature_difference(self) -> float | None:
        """Return the gap between extract and outdoor air, in °C."""
        outdoor = self.temperature(IR_TEMP_OUTDOOR)
        extract = self.temperature(IR_TEMP_EXTRACT)
        if outdoor is None or extract is None:
            return None
        return round(abs(extract - outdoor), 1)

    @property
    def efficiency_status(self) -> str:
        """Say whether the efficiency can be worked out, and if not, why.

        The exchanger keeps recovering heat in the "heating", "cooling",
        "preheating" and "small_difference" cases: only the figure is
        missing, because something else changes the supply temperature or
        because indoor and outdoor air are too close to measure it.
        """
        difference = self.temperature_difference
        if difference is None or self.temperature(IR_TEMP_SUPPLY) is None:
            return EFFICIENCY_NO_PROBE
        if not self.is_on:
            return EFFICIENCY_OFF
        if self.inputs[IR_BYPASS_STATE]:
            return EFFICIENCY_BYPASS
        if self.discrete[DI_STATUS_HEATER]:
            return EFFICIENCY_HEATING
        if self.discrete[DI_STATUS_COOLER]:
            return EFFICIENCY_COOLING
        if self.inputs[IR_PREHEATER_OUTPUT]:
            return EFFICIENCY_PREHEATING
        if self.defrosting:
            return EFFICIENCY_DEFROSTING
        if difference < MIN_EFFICIENCY_DELTA:
            return EFFICIENCY_SMALL_DIFFERENCE
        return EFFICIENCY_MEASURED

    @property
    def defrosting(self) -> bool:
        """True while the supply fan is stopped and the extract fan runs.

        Frost protection by fan stop, or the second stage the firmware adds
        behind a bypass that does not cope. Only known with tachometers.
        """
        supply, extract = self.inputs[IR_SUPPLY_RPM], self.inputs[IR_EXTRACT_RPM]
        return bool(extract) and supply == 0

    @property
    def efficiency(self) -> int | None:
        """Return the supply-side heat recovery efficiency in percent.

        (supply - outdoor) / (extract - outdoor). Only meaningful while the
        exchanger alone changes the supply temperature, so nothing is
        reported when a heater or cooler runs, when the bypass is open or
        when indoor and outdoor air are too close: see efficiency_status.
        """
        outdoor = self.temperature(IR_TEMP_OUTDOOR)
        supply = self.temperature(IR_TEMP_SUPPLY)
        extract = self.temperature(IR_TEMP_EXTRACT)
        if (
            outdoor is None
            or supply is None
            or extract is None
            or self.efficiency_status != EFFICIENCY_MEASURED
        ):
            return None
        ratio = (supply - outdoor) / (extract - outdoor)
        return round(min(max(ratio, 0.0), 1.0) * 100)

    @property
    def efficiency_exhaust_side(self) -> int | None:
        """Return the exhaust-side temperature ratio in percent.

        (extract - exhaust) / (extract - outdoor): how much of its heat the
        extract air gave up. Equal to the supply-side figure with balanced
        flows; the two drift apart when they are not. Condensation on the
        extract side (latent heat) lowers it: see condensation_likely.
        """
        outdoor = self.temperature(IR_TEMP_OUTDOOR)
        extract = self.temperature(IR_TEMP_EXTRACT)
        exhaust = self.temperature(IR_TEMP_EXHAUST)
        if (
            outdoor is None
            or extract is None
            or exhaust is None
            or self.efficiency_status != EFFICIENCY_MEASURED
        ):
            return None
        ratio = (extract - exhaust) / (extract - outdoor)
        return round(min(max(ratio, 0.0), 1.0) * 100)

    @property
    def flow_ratio(self) -> float | None:
        """Return the apparent extract/supply flow ratio from the four probes.

        The heat the extract air gives up is the heat the supply air takes:
        extract flow x (extract - exhaust) = supply flow x (supply - outdoor),
        so the ratio of the flows is the ratio of the temperature rises. It
        is the ratio of the real flows, whatever the fan settings, and it
        follows filter clogging. Only sensible heat is counted: with
        condensation on the extract side the figure comes out low (see
        condensation_likely). None when the efficiency is not measurable or
        when the exhaust-side rise is too small to divide by.
        """
        outdoor = self.temperature(IR_TEMP_OUTDOOR)
        supply = self.temperature(IR_TEMP_SUPPLY)
        extract = self.temperature(IR_TEMP_EXTRACT)
        exhaust = self.temperature(IR_TEMP_EXHAUST)
        if (
            outdoor is None
            or supply is None
            or extract is None
            or exhaust is None
            or self.efficiency_status != EFFICIENCY_MEASURED
        ):
            return None
        given_up = extract - exhaust
        taken = supply - outdoor
        if given_up < 1.0 or taken < 0:
            return None
        return round(taken / given_up, 2)

    @property
    def indoor_humidity(self) -> int | None:
        """Relative humidity of the extract air, from either probe, or None."""
        for address in (IR_RH_INT, IR_RH_EXT):
            value = self.inputs[address]
            if value:
                return value
        return None

    @property
    def dew_point(self) -> float | None:
        """Dew point of the extract air in °C (Magnus), None without humidity."""
        extract = self.temperature(IR_TEMP_EXTRACT)
        humidity = self.indoor_humidity
        if extract is None or humidity is None:
            return None
        a, b = 17.62, 243.12
        gamma = math.log(humidity / 100) + a * extract / (b + extract)
        return round(b * gamma / (a - gamma), 1)

    @property
    def condensation_likely(self) -> bool | None:
        """Whether the extract air is condensing in the exchanger.

        With a humidity probe: the exhaust air is at or under the dew point
        of the extract air (plus a margin, the plates being colder than the
        air leaving them). Without one: the exhaust air is simply cold.
        None without an exhaust probe.
        """
        exhaust = self.temperature(IR_TEMP_EXHAUST)
        if exhaust is None:
            return None
        dew_point = self.dew_point
        if dew_point is None:
            return exhaust < CONDENSATION_GUESS_BELOW
        return exhaust < dew_point + CONDENSATION_MARGIN

    @property
    def timer_remaining(self) -> int | None:
        """Return the seconds left on the main timer."""
        min_sec, hours = self.inputs[IR_TIMER_MIN_SEC], self.inputs[IR_TIMER_HOURS]
        if min_sec is None or hours is None:
            return None
        return (hours & 0xFF) * 3600 + (min_sec >> 8) * 60 + (min_sec & 0xFF)

    @property
    def operating_hours(self) -> int | None:
        """Return the motor run time in hours."""
        hours_min, days = self.inputs[IR_WORK_HOURS_MIN], self.inputs[IR_WORK_DAYS]
        if hours_min is None or days is None:
            return None
        return days * 24 + (hours_min >> 8)

    def active_codes(self, language: str | None) -> list[ActiveCode]:
        """Return the active alarms and warnings, described in a language."""
        # IR_ALARM: 1 when at least one alarm is active, 2 for warnings only.
        fallback = ALARM if self.inputs[IR_ALARM] == 1 else WARNING
        return [describe(code, language, fallback) for code in self.alarm_codes]

    @property
    def firmware(self) -> str | None:
        """Return the firmware version, e.g. '2.15 (2023-04-18)'."""
        version, date, year = self.inputs[IR_FIRMWARE : IR_FIRMWARE + 3]
        if version is None:
            return None
        text = f"{version >> 8}.{version & 0xFF}"
        if date and year:
            text += f" ({year}-{date & 0xFF:02d}-{date >> 8:02d})"
        return text


_Reader = Callable[[int, int], Awaitable[Sequence[int | bool]]]


class A21Api:
    """Serialised access to one A21 controller.

    Two modes. keep_connection (the default): one TCP connection is kept
    across polls and writes, stray AT text leaked by the module is ignored
    without closing it. Otherwise a connection is opened for each poll or
    write and closed right after, the way the manufacturer's own tools
    talk to the unit. On a DF 350 (firmware 0.43) the module froze twice
    while the kept connection was closed and reopened at every stray text
    (0.2.11); whether keeping it open for good, as now, avoids the freeze
    is what the default is testing. The per-poll mode remains an option.
    """

    def __init__(
        self, host: str, port: int, unit_id: int, keep_connection: bool = True
    ) -> None:
        self.host = host
        self.port = port
        self._client = ModbusTcpClient(host, port, unit_id)
        self._lock = asyncio.Lock()
        self.keep_connection = keep_connection
        # Alarm codes left out of every snapshot (see CONF_MANUAL_BYPASS).
        self.ignored_codes: frozenset[int] = frozenset()
        # Number of readable addresses per table, learnt on older firmware.
        self._limits: dict[str, int] = {}

    async def _connect(self) -> None:
        try:
            await self._client.connect()
        except ModbusConnectionError:
            await asyncio.sleep(_CONNECT_RETRY_DELAY)
            await self._client.connect()

    async def async_identify(self) -> int:
        """Return the device type register (1 for an A21).

        Used by the setup form. A connection opened just for this is closed
        again; the connection of a running unit is left as it is.
        """
        async with self._lock:
            opened = not self._client.connected
            await self._connect()
            try:
                return (await self._client.read_input_registers(IR_DEVICE_TYPE, 1))[0]
            except ModbusError:
                await self._client.close()
                raise
            finally:
                if opened:
                    await self._client.close()

    async def async_poll(self) -> A21Data:
        """Read every table."""
        async with self._lock:
            await self._connect()
            try:
                # On a transport or protocol error the client drops the
                # socket itself; the next poll opens a fresh one.
                return await self._read_all()
            finally:
                if not self.keep_connection:
                    await self._client.close()

    async def async_write(self, writes: Sequence[Write]) -> A21Data:
        """Apply writes in order, then return the state read back."""
        async with self._lock:
            await self._connect()
            try:
                for write in writes:
                    if isinstance(write, CoilWrite):
                        await self._client.write_coil(write.address, write.value)
                    else:
                        await self._client.write_register(
                            write.address, write.value
                        )
                await asyncio.sleep(_SETTLE_DELAY)
                return await self._read_all()
            finally:
                if not self.keep_connection:
                    await self._client.close()

    @property
    def stats(self) -> dict:
        """Counters of the connection, for diagnostics and error messages."""
        return self._client.stats.as_dict()

    async def async_close(self) -> None:
        """Close the connection, when the unit is unloaded or Home Assistant stops."""
        async with self._lock:
            await self._client.close()

    async def _read_all(self) -> A21Data:
        client = self._client
        return A21Data(
            coils=await self._read_table("coils", client.read_coils, COIL_COUNT),
            discrete=await self._read_table(
                "discrete inputs", client.read_discrete_inputs, DISCRETE_COUNT
            ),
            inputs=await self._read_table(
                "input registers", client.read_input_registers, INPUT_COUNT
            ),
            holdings=await self._read_table(
                "holding registers", client.read_holding_registers, HOLDING_COUNT
            ),
            ignored_codes=self.ignored_codes,
        )

    async def _read_table(self, name: str, reader: _Reader, count: int) -> list:
        """Read addresses 0..count-1, tolerating firmware with a shorter table.

        Older firmware answers "illegal data address" when a request reaches
        past the end of its table. The readable length is then searched once
        and remembered; missing addresses are returned as None.
        """
        limit = self._limits.get(name, count)
        values: list = []
        if limit:
            try:
                values = list(await reader(0, limit))
            except ModbusExceptionResponse as err:
                if err.code != EXC_ILLEGAL_DATA_ADDRESS:
                    raise
                limit = await self._probe_limit(reader, limit)
                self._limits[name] = limit
                _LOGGER.info(
                    "%s: this firmware exposes %d of %d %s",
                    self.host,
                    limit,
                    count,
                    name,
                )
                values = list(await reader(0, limit)) if limit else []
        return values + [None] * (count - len(values))

    @staticmethod
    async def _probe_limit(reader: _Reader, failing: int) -> int:
        """Return the largest readable count below a count known to fail."""
        low, high = 0, failing
        while high - low > 1:
            middle = (low + high) // 2
            try:
                await reader(0, middle)
            except ModbusExceptionResponse as err:
                if err.code != EXC_ILLEGAL_DATA_ADDRESS:
                    raise
                high = middle
            else:
                low = middle
        return low
