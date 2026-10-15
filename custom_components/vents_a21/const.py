"""Constants for the VENTS A21 integration.

Register addresses come from the VENTS document
"Modbus table for connecting A21 automation to BMS" (V55-8-1EN-02).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

DOMAIN: Final = "vents_a21"

CONF_UNIT_ID: Final = "unit_id"
CONF_MODEL: Final = "model"
CONF_ADVANCED: Final = "advanced"
# Password of the app/engineer menu, used once to ask the unit its identifier.
CONF_ENGINEER_PASSWORD: Final = "engineer_password"
# Option: the bypass is driven from Home Assistant, so the warning the unit
# raises while its bypass is in manual mode is expected and is not reported.
CONF_MANUAL_BYPASS: Final = "manual_bypass"

DEFAULT_PORT: Final = 502
DEFAULT_UNIT_ID: Final = 1
DEFAULT_SCAN_INTERVAL: Final = 15
MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 300

DEVICE_TYPE_A21: Final = 1

# --- Coils (functions 1, 5) -------------------------------------------------
CL_POWER: Final = 0
CL_TIMER: Final = 1
CL_WEEK: Final = 2
CL_BOOST_MODE: Final = 3
CL_FIREPLACE_MODE: Final = 4
CL_INT_RH_CTRL: Final = 5
CL_EXT_RH_CTRL: Final = 6
CL_INT_CO2_CTRL: Final = 7
CL_EXT_CO2_CTRL: Final = 8
CL_INT_PM25_CTRL: Final = 9
CL_EXT_PM25_CTRL: Final = 10
CL_INT_VOC_CTRL: Final = 11
CL_EXT_VOC_CTRL: Final = 12
CL_BOOST_SWITCH_CTRL: Final = 13
CL_FIREPLACE_SWITCH_CTRL: Final = 14
CL_FIRE_ALARM_CTRL: Final = 15
CL_10V_SENSOR_CTRL: Final = 16
CL_RESET_FILTER_TIMER: Final = 17
CL_RESET_ALARM: Final = 18
# 19 (restore factory settings) is deliberately never used.
COIL_COUNT: Final = 26

# --- Discrete inputs (function 2) -------------------------------------------
DI_BOOST_SWITCH: Final = 0
DI_FIREPLACE_SWITCH: Final = 1
DI_FIRE_ALARM: Final = 2
DI_STATUS_RH: Final = 3
DI_STATUS_CO2: Final = 4
DI_STATUS_PM25: Final = 5
DI_STATUS_VOC: Final = 6
DI_STATUS_HEATER: Final = 7
DI_STATUS_COOLER: Final = 8
DI_STATUS_FAN_BLOWING: Final = 9
DI_SUPPLY_FILTER_SWITCH: Final = 12
DI_EXTRACT_FILTER_SWITCH: Final = 13
DI_SUPPLY_FAN_SWITCH: Final = 16
DI_EXTRACT_FAN_SWITCH: Final = 17
DI_ALARM_FIRST: Final = 19
ALARM_CODE_COUNT: Final = 53
# Warnings "bypass in manual mode" and "rotary exchanger in manual mode".
MANUAL_BYPASS_CODES: Final = frozenset({38, 39})
DISCRETE_COUNT: Final = 72

# --- Input registers (function 4) -------------------------------------------
IR_TEMP_SELECTED: Final = 0
IR_TEMP_OUTDOOR: Final = 1  # supply air entering the unit, before preheating
IR_TEMP_SUPPLY: Final = 2  # supply air leaving the unit, after the reheater
IR_TEMP_EXTRACT: Final = 3  # extract air entering the unit
IR_TEMP_EXHAUST: Final = 4  # exhaust air leaving the unit
IR_TEMP_PANEL: Final = 5
IR_TEMP_AFTER_PREHEATER: Final = 6
IR_TEMP_BEFORE_REHEATER: Final = 7
IR_TEMP_WATER: Final = 8
IR_RTC_BATTERY: Final = 9
IR_RH_INT: Final = 10
IR_RH_EXT: Final = 11
IR_CO2_INT: Final = 12
IR_CO2_EXT: Final = 13
IR_PM25_INT: Final = 14
IR_PM25_EXT: Final = 15
IR_VOC_INT: Final = 16
IR_VOC_EXT: Final = 17
IR_10V_SENSOR: Final = 18
IR_SUPPLY_FLOW: Final = 19
IR_EXTRACT_FLOW: Final = 20
IR_SUPPLY_PRESSURE: Final = 21
IR_EXTRACT_PRESSURE: Final = 22
IR_SUPPLY_RPM: Final = 23
IR_EXTRACT_RPM: Final = 24
IR_TIMER_MIN_SEC: Final = 25  # high byte: minutes, low byte: seconds
IR_TIMER_HOURS: Final = 26  # low byte: hours
IR_FILTER_HOURS_MIN: Final = 27  # high byte: hours, low byte: minutes
IR_FILTER_DAYS: Final = 28
IR_WORK_HOURS_MIN: Final = 29  # high byte: hours, low byte: minutes
IR_WORK_DAYS: Final = 30
IR_FILTER_STATE: Final = 31
IR_WEEK_SPEED: Final = 32
IR_WEEK_TEMP: Final = 33
IR_FIRMWARE: Final = 34  # 34: major/minor, 35: day/month, 36: year
IR_DEVICE_TYPE: Final = 37
IR_ALARM: Final = 38
IR_RH_DEMAND: Final = 39
IR_CO2_DEMAND: Final = 40
IR_PM25_DEMAND: Final = 41
IR_VOC_DEMAND: Final = 42
IR_PREHEATER_OUTPUT: Final = 43
IR_REHEATER_OUTPUT: Final = 44
IR_BYPASS_OUTPUT: Final = 45
IR_COOLER_OUTPUT: Final = 46
IR_WATER_OUTPUT: Final = 47
IR_SUPPLY_SETPOINT: Final = 48
IR_BYPASS_STATE: Final = 51
IR_SUPPLY_FAN_PERCENT: Final = 52
IR_EXTRACT_FAN_PERCENT: Final = 53
INPUT_COUNT: Final = 54

# --- Holding registers (functions 3, 6) -------------------------------------
HR_VENTILATION_MODE: Final = 0  # 0: percent, 1: constant flow, 2: constant pressure
HR_MAX_SPEED_MODE: Final = 1
HR_SPEED_MODE: Final = 2  # 1..5, 255: manual
HR_MIN_SPEED: Final = 3
HR_MAX_SPEED: Final = 4
HR_SUPPLY_SPEED0: Final = 5  # then extract/supply pairs up to speed 5 (16)
HR_MANUAL_SPEED: Final = 17
HR_BOOST_SUPPLY_SPEED: Final = 19
HR_BOOST_EXTRACT_SPEED: Final = 20
HR_FIREPLACE_SUPPLY_SPEED: Final = 21
HR_FIREPLACE_EXTRACT_SPEED: Final = 22
HR_OPERATION_MODE: Final = 43  # 0: ventilation, 1: heating, 2: cooling, 3: auto
HR_SET_TEMP: Final = 44
HR_SET_RH: Final = 45
HR_SET_CO2: Final = 46
HR_SET_PM25: Final = 47
HR_SET_VOC: Final = 48
HR_TIMER_MODE: Final = 49
HR_TIMER_TEMP: Final = 50
HR_TIMER_TIME: Final = 51  # high byte: hours, low byte: minutes
HR_TEMP_SENSOR: Final = 53
HR_MAIN_HEATER_TYPE: Final = 54
HR_COOLER_TYPE: Final = 55
HR_DEFROST_MODE: Final = 56
HR_BYPASS_TYPE: Final = 57  # 0: none, 1: on/off, 2: analogue, 3/4: rotary, 5: 3-point
# The ECONOPRIME units all have a plate exchanger with a bypass damper. The
# A21 controller can also drive a rotary exchanger, found on other brands:
# that case is handled (wording, drawing) but is the exception.
ROTARY_TYPES: Final = frozenset({3, 4})
HR_FILTER_TIMER: Final = 58
HR_BOOST_OFF_DELAY: Final = 59
HR_BOOST_ON_DELAY: Final = 60
HR_BYPASS_MODE: Final = 74  # 0: closed, 1: open, 2: auto
HR_FAN_ALARM_CTRL: Final = 103  # 0: none, 1..254: tacho pulses, 255: pressure switch
HR_BYPASS_SIDE: Final = 110  # 0: bypasses the outdoor air, 1: the extract air
# 124-125 hold the engineering menu password: never read, never written.
HOLDING_COUNT: Final = 124

SPEED_MANUAL: Final = 255
TEMP_NO_SENSOR: Final = 0x8000
TEMP_SHORT_CIRCUIT: Final = 0x7FFF

SHOP_URL: Final = "https://www.econology.fr/"
_UTM: Final = "?utm_source=home-assistant&utm_medium=integration&utm_campaign=vents_a21"


@dataclass(frozen=True)
class Model:
    """A unit sold with the A21 controller."""

    manufacturer: str
    name: str
    reference: str | None = None
    product_url: str | None = None
    filters_url: str | None = None
    # Replacement filters, (class, shop SKU): what the card puts in the cart.
    filters: tuple[tuple[str, str], ...] = ()


def _shop(path: str) -> str:
    return f"{SHOP_URL}{path}{_UTM}"


# Shop home page, shown in the setup form.
SHOP_HOME_URL: Final = _shop("")


# Optional probes, suggested when the unit does not have them.
ACCESSORIES: Final[dict[str, str]] = {
    "humidity": _shop("hv2-econoprime-sonde-hygro.html"),
    "co2": _shop("econoprime-sonde-co2-0-10v.html"),
    "voc": _shop("econoprime-sonde-cov-0-10v.html"),
}

MODEL_GENERIC: Final = "generic"

MODELS: Final[dict[str, Model]] = {
    "zephyr_240_s_connect": Model(
        "ECONOPRIME",
        "Zephyr 240 S Connect",
        "ZEPH240A21",
        _shop("zephyr-240-connect-vmc-double-flux-zeph240a21-econoprime.html"),
        _shop("filtre-f7-vmc-double-flux-zephyr-240-fzeph240f7-econoprime.html"),
        (("G4", "REF128848"), ("F7", "REF128847")),
    ),
    "zephyr_270_v_connect_r": Model(
        "ECONOPRIME",
        "Zephyr 270 V Connect R",
        "114800002",
        _shop("zephyr-270-connect-econoprime-vmc-double-flux-114800002.html"),
        _shop("filtre-f7-zephyr-270-12300001-econoprime.html"),
        (("G4", "REF135207"), ("F7", "REF135206")),
    ),
    "zephyr_550_v_ph_connect_r": Model(
        "ECONOPRIME",
        "Zephyr 550 V PH Connect R",
        "114800003",
        _shop("vmc-double-flux-zephyr-550-v-ph-connect-r-econoprime-114800003.html"),
        _shop(
            "filtres-panneau-596x164x60-econoprime-filtres-de-rechange-pour-centrale-double-flux-596-x-164-x-60-mm.html"
        ),
        (("G4", "REF142162"), ("F7", "REF142163")),
    ),
    "df_180_flat_connect": Model(
        "ECONOPRIME",
        "DF 180 Flat Connect",
        "DFF18021",
        _shop("df-180-flat-connect-econoprime-vmc-double-flux.html"),
        _shop("filtre-vmc-double-flux-df-180-econoprime.html"),
        (("G4", "REF102165"), ("F7", "REF102166")),
    ),
    "df_270_connect": Model(
        "ECONOPRIME",
        "DF 270 Connect",
        "DF27021",
        _shop("df-270-connect-econoprime-vmc-double-flux.html"),
        _shop("filtre-vmc-double-flux-df-270-econoprime.html"),
        (("G4", "REF102170"), ("F8", "REF102171")),
    ),
    "df_350_connect": Model(
        "ECONOPRIME",
        "DF 350 Connect",
        "DF35021",
        _shop("df-350-connect-econoprime-vmc-double-flux.html"),
        _shop("filtre-vmc-double-flux-df-350-econoprime.html"),
        (("G4", "REF102185"), ("F7", "REF102186")),
    ),
    MODEL_GENERIC: Model("VENTS", "A21"),
}
