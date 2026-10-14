"""Everything the controller reports, laid out for the "details" card.

The details card shows far more than the entities do: fan power, speed,
airflow and pressure side by side, every probe, the state of the exchanger,
of the heaters, of the inputs, and the alarms in plain words. Creating an
entity for each of these values would flood the entity list and the
recorder, so the card gets them straight from the last poll instead.

A value only appears when the unit has the matching hardware: an optional
probe that is neither enabled nor reporting anything is left out, and listed
once as "not installed".
"""

from __future__ import annotations

from typing import Any

from .alarms import ALARM, WARNING, language_of
from .api import (
    EFFICIENCY_COOLING,
    EFFICIENCY_HEATING,
    EFFICIENCY_PREHEATING,
    EFFICIENCY_SMALL_DIFFERENCE,
    MIN_EFFICIENCY_DELTA,
    A21Data,
)
from .const import (
    ACCESSORIES,
    CL_10V_SENSOR_CTRL,
    CL_BOOST_MODE,
    CL_BOOST_SWITCH_CTRL,
    CL_EXT_CO2_CTRL,
    CL_EXT_PM25_CTRL,
    CL_EXT_RH_CTRL,
    CL_EXT_VOC_CTRL,
    CL_FIRE_ALARM_CTRL,
    CL_FIREPLACE_MODE,
    CL_FIREPLACE_SWITCH_CTRL,
    CL_INT_CO2_CTRL,
    CL_INT_PM25_CTRL,
    CL_INT_RH_CTRL,
    CL_INT_VOC_CTRL,
    CL_TIMER,
    CL_WEEK,
    DI_BOOST_SWITCH,
    DI_EXTRACT_FAN_SWITCH,
    DI_EXTRACT_FILTER_SWITCH,
    DI_FIRE_ALARM,
    DI_FIREPLACE_SWITCH,
    DI_STATUS_CO2,
    DI_STATUS_COOLER,
    DI_STATUS_FAN_BLOWING,
    DI_STATUS_HEATER,
    DI_STATUS_PM25,
    DI_STATUS_RH,
    DI_STATUS_VOC,
    DI_SUPPLY_FAN_SWITCH,
    DI_SUPPLY_FILTER_SWITCH,
    HR_BYPASS_MODE,
    HR_BYPASS_SIDE,
    HR_BYPASS_TYPE,
    HR_COOLER_TYPE,
    HR_DEFROST_MODE,
    HR_FAN_ALARM_CTRL,
    HR_FILTER_TIMER,
    HR_MAIN_HEATER_TYPE,
    HR_MANUAL_SPEED,
    HR_OPERATION_MODE,
    HR_SET_CO2,
    HR_SET_PM25,
    HR_SET_RH,
    HR_SET_TEMP,
    HR_SET_VOC,
    HR_SPEED_MODE,
    HR_SUPPLY_SPEED0,
    HR_TEMP_SENSOR,
    HR_VENTILATION_MODE,
    IR_10V_SENSOR,
    IR_BYPASS_OUTPUT,
    IR_BYPASS_STATE,
    IR_CO2_DEMAND,
    IR_CO2_EXT,
    IR_CO2_INT,
    IR_COOLER_OUTPUT,
    IR_EXTRACT_FAN_PERCENT,
    IR_EXTRACT_FLOW,
    IR_EXTRACT_PRESSURE,
    IR_EXTRACT_RPM,
    IR_FILTER_DAYS,
    IR_FILTER_HOURS_MIN,
    IR_FILTER_STATE,
    IR_PM25_DEMAND,
    IR_PM25_EXT,
    IR_PM25_INT,
    IR_PREHEATER_OUTPUT,
    IR_REHEATER_OUTPUT,
    IR_RH_DEMAND,
    IR_RH_EXT,
    IR_RH_INT,
    IR_RTC_BATTERY,
    IR_SUPPLY_FAN_PERCENT,
    IR_SUPPLY_FLOW,
    IR_SUPPLY_PRESSURE,
    IR_SUPPLY_RPM,
    IR_SUPPLY_SETPOINT,
    IR_TEMP_AFTER_PREHEATER,
    IR_TEMP_BEFORE_REHEATER,
    IR_TEMP_EXHAUST,
    IR_TEMP_EXTRACT,
    IR_TEMP_OUTDOOR,
    IR_TEMP_PANEL,
    IR_TEMP_SELECTED,
    IR_TEMP_SUPPLY,
    IR_TEMP_WATER,
    IR_VOC_DEMAND,
    IR_VOC_EXT,
    IR_VOC_INT,
    IR_WATER_OUTPUT,
    IR_WEEK_SPEED,
    IR_WEEK_TEMP,
    ROTARY_TYPES,
    SPEED_MANUAL,
    Model,
)

_T: dict[str, dict[str, str]] = {
    "fr": {
        # sections
        "s_alarms": "Alarmes et avertissements",
        "s_state": "Fonctionnement",
        "s_fans": "Ventilateurs",
        "s_temps": "Températures",
        "s_air": "Qualité d'air",
        "s_exchanger": "Échangeur et bypass",
        "s_heating": "Chauffage et rafraîchissement",
        "s_inputs": "Entrées",
        "s_service": "Entretien",
        # generic
        "on": "En marche",
        "off": "À l'arrêt",
        "active": "Actif",
        "inactive": "Inactif",
        "running": "En cours",
        "yes": "Oui",
        "no": "Non",
        "threshold": "seuil {}",
        "none": "Aucune",
        # state
        "unit": "Machine",
        "mode": "Mode",
        "mode_0": "Ventilation seule",
        "mode_1": "Chauffage",
        "mode_2": "Rafraîchissement",
        "mode_3": "Automatique",
        "speed": "Vitesse",
        "speed_n": "Vitesse {}",
        "speed_manual": "Manuelle, {} %",
        "regulation": "Régulation des ventilateurs",
        "regulation_0": "En pourcentage",
        "regulation_1": "Débit constant",
        "regulation_2": "Pression constante",
        "setpoint": "Consigne de température",
        "boost": "Boost",
        "fireplace": "Mode cheminée",
        "timer": "Minuterie",
        "timer_left": "reste {}",
        "schedule": "Programmation hebdomadaire",
        "schedule_now": "vitesse {}",
        "schedule_standby": "veille",
        # fans
        "supply": "Soufflage",
        "extract": "Extraction",
        "power": "Puissance",
        "rpm": "Régime",
        "flow": "Débit",
        "pressure": "Pression",
        "preset": "Réglage de la vitesse {}",
        "preset_standby": "Réglage de la veille",
        "fan_switch": "Pressostat",
        "u_rpm": "tr/min",
        # temperatures
        "t_outdoor": "Air neuf",
        "t_after_pre": "Air neuf après préchauffage",
        "t_before_re": "Air soufflé avant chauffage",
        "t_supply": "Air soufflé",
        "t_extract": "Air extrait",
        "t_exhaust": "Air rejeté",
        "t_panel": "Boîtier de commande",
        "t_water": "Retour d'eau",
        "t_control": "Température régulée",
        "t_control_0": "sur l'air extrait",
        "t_control_1": "sur le boîtier de commande",
        "t_control_2": "sur l'air soufflé",
        "t_control_supply": (
            "Avec la sonde sur l'air soufflé, le bypass régule l'air soufflé, pas la"
            " pièce. Pour rafraîchir la maison la nuit, choisissez l'air extrait."
        ),
        "t_supply_setpoint": "Consigne de soufflage calculée",
        # air quality
        "rh": "Humidité",
        "rh_ext": "Humidité, sonde externe",
        "co2": "CO₂",
        "co2_ext": "CO₂, sonde externe",
        "pm25": "PM2.5",
        "pm25_ext": "PM2.5, sonde externe",
        "voc": "COV",
        "voc_ext": "COV, sonde externe",
        "analog": "Entrée 0-10 V",
        "demand": "Surventilation demandée",
        "absent": "Sondes non installées",
        "a_humidity": "humidité",
        "a_co2": "CO₂",
        "a_pm25": "PM2.5",
        "a_voc": "COV",
        # exchanger
        "x_type": "Type",
        "x_type_1": "Bypass tout ou rien",
        "x_type_2": "Bypass modulant",
        "x_type_3": "Échangeur rotatif tout ou rien",
        "x_type_4": "Échangeur rotatif modulant",
        "x_type_5": "Bypass trois points",
        "x_position": "Position du bypass",
        "x_closed": "Fermé",
        "x_open": "Ouvert",
        "x_partial": "Ouvert à {} %",
        "x_rotor": "Échangeur rotatif",
        "x_rotor_full": "Pleine vitesse",
        "x_rotor_stopped": "À l'arrêt",
        "x_rotor_partial": "Ralenti à {} %",
        "x_mode": "Commande",
        "x_mode_0": "Forcé fermé",
        "x_mode_1": "Forcé ouvert",
        "x_mode_2": "Automatique",
        "x_mode_frost": (
            "Sans préchauffage, c'est le bypass qui protège l'échangeur du gel :"
            " en hiver, repassez en automatique."
        ),
        "x_side": "Air dévié",
        "x_side_0": "Air neuf",
        "x_side_1": "Air extrait",
        "x_signal": "Commande envoyée",
        "x_signal_moving": "Le registre est en mouvement vers cette valeur.",
        "x_efficiency": "Rendement de récupération",
        "x_efficiency_unmeasured": "Non mesurable",
        "x_efficiency_small_difference": (
            "L'échangeur récupère la chaleur, mais intérieur et extérieur sont"
            " trop proches pour chiffrer le rendement : {gap} d'écart, il en"
            " faut {minimum}."
        ),
        "x_efficiency_heating": (
            "L'échangeur récupère la chaleur, mais le chauffage fausse la mesure."
        ),
        "x_efficiency_cooling": (
            "L'échangeur récupère la chaleur, mais le refroidissement fausse la mesure."
        ),
        "x_efficiency_preheating": (
            "L'échangeur récupère la chaleur, mais le préchauffage fausse la mesure."
        ),
        "x_frost": "Protection antigel",
        "x_frost_0": "Désactivée",
        "x_frost_1": "Par préchauffage",
        "x_frost_2": "Par bypass",
        "x_frost_2_rotary": "Par l'échangeur rotatif",
        "x_frost_3": "Par arrêt du soufflage",
        "x_preheater": "Préchauffage",
        # heating
        "h_heater": "Batterie de chauffage",
        "h_heater_1": "Électrique",
        "h_heater_2": "À eau",
        "h_cooler": "Refroidissement",
        "h_cooler_1": "Tout ou rien",
        "h_cooler_2": "Modulant 0-10 V",
        "h_power": "Puissance de chauffage",
        "h_cool_power": "Puissance de refroidissement",
        "h_valve": "Vanne d'eau",
        "h_blowing": "Post-ventilation de la batterie",
        # inputs
        "i_boost": "Interrupteur boost",
        "i_fireplace": "Interrupteur cheminée",
        "i_fire": "Contact d'alarme incendie",
        # service
        "f_state": "Filtres",
        "f_state_0": "Propres",
        "f_state_1": "Filtre d'air neuf encrassé",
        "f_state_2": "Filtre d'air extrait encrassé",
        "f_state_3": "À remplacer",
        "f_left": "Prochain remplacement",
        "f_in": "dans {}",
        "f_interval": "Intervalle de remplacement",
        "f_switch_supply": "Pressostat du filtre d'air neuf",
        "f_switch_extract": "Pressostat du filtre d'air extrait",
        "f_clogged": "Encrassé",
        "f_clean": "Propre",
        "hours": "Fonctionnement cumulé",
        "battery": "Pile de l'horloge",
        "firmware": "Micrologiciel",
        "model": "Modèle",
        "d": "j",
        "h": "h",
        "min": "min",
    },
    "en": {
        "s_alarms": "Alarms and warnings",
        "s_state": "Operation",
        "s_fans": "Fans",
        "s_temps": "Temperatures",
        "s_air": "Air quality",
        "s_exchanger": "Exchanger and bypass",
        "s_heating": "Heating and cooling",
        "s_inputs": "Inputs",
        "s_service": "Maintenance",
        "on": "On",
        "off": "Off",
        "active": "Active",
        "inactive": "Inactive",
        "running": "Running",
        "yes": "Yes",
        "no": "No",
        "threshold": "threshold {}",
        "none": "None",
        "unit": "Unit",
        "mode": "Mode",
        "mode_0": "Ventilation only",
        "mode_1": "Heating",
        "mode_2": "Cooling",
        "mode_3": "Automatic",
        "speed": "Speed",
        "speed_n": "Speed {}",
        "speed_manual": "Manual, {} %",
        "regulation": "Fan regulation",
        "regulation_0": "Percentage",
        "regulation_1": "Constant airflow",
        "regulation_2": "Constant pressure",
        "setpoint": "Temperature setpoint",
        "boost": "Boost",
        "fireplace": "Fireplace mode",
        "timer": "Timer",
        "timer_left": "{} left",
        "schedule": "Weekly schedule",
        "schedule_now": "speed {}",
        "schedule_standby": "standby",
        "supply": "Supply",
        "extract": "Extract",
        "power": "Power",
        "rpm": "Speed",
        "flow": "Airflow",
        "pressure": "Pressure",
        "preset": "Speed {} setting",
        "preset_standby": "Standby setting",
        "fan_switch": "Pressure switch",
        "u_rpm": "rpm",
        "t_outdoor": "Outdoor air",
        "t_after_pre": "Outdoor air after preheating",
        "t_before_re": "Supply air before heating",
        "t_supply": "Supply air",
        "t_extract": "Extract air",
        "t_exhaust": "Exhaust air",
        "t_panel": "Control panel",
        "t_water": "Return water",
        "t_control": "Controlled temperature",
        "t_control_0": "on the extract air",
        "t_control_1": "on the control panel",
        "t_control_2": "on the supply air",
        "t_control_supply": (
            "With the sensor on the supply air, the bypass regulates the air blown"
            " in, not the room. To cool the house at night, choose the extract air."
        ),
        "t_supply_setpoint": "Calculated supply setpoint",
        "rh": "Humidity",
        "rh_ext": "Humidity, external sensor",
        "co2": "CO₂",
        "co2_ext": "CO₂, external sensor",
        "pm25": "PM2.5",
        "pm25_ext": "PM2.5, external sensor",
        "voc": "VOC",
        "voc_ext": "VOC, external sensor",
        "analog": "0-10 V input",
        "demand": "Extra ventilation requested",
        "absent": "Sensors not installed",
        "a_humidity": "humidity",
        "a_co2": "CO₂",
        "a_pm25": "PM2.5",
        "a_voc": "VOC",
        "x_type": "Type",
        "x_type_1": "On/off bypass",
        "x_type_2": "Modulating bypass",
        "x_type_3": "On/off rotary exchanger",
        "x_type_4": "Modulating rotary exchanger",
        "x_type_5": "Three-point bypass",
        "x_position": "Bypass position",
        "x_closed": "Closed",
        "x_open": "Open",
        "x_partial": "{} % open",
        "x_rotor": "Rotary exchanger",
        "x_rotor_full": "Full speed",
        "x_rotor_stopped": "Stopped",
        "x_rotor_partial": "Slowed to {} %",
        "x_mode": "Control",
        "x_mode_0": "Forced closed",
        "x_mode_1": "Forced open",
        "x_mode_2": "Automatic",
        "x_mode_frost": (
            "Without a preheater, the bypass is what protects the exchanger from"
            " frost: switch back to automatic in winter."
        ),
        "x_side": "Bypassed air",
        "x_side_0": "Outdoor air",
        "x_side_1": "Extract air",
        "x_signal": "Command sent",
        "x_signal_moving": "The damper is travelling towards this value.",
        "x_efficiency": "Heat recovery efficiency",
        "x_efficiency_unmeasured": "Cannot be measured",
        "x_efficiency_small_difference": (
            "The exchanger is recovering heat, but indoor and outdoor air are"
            " too close to work out the efficiency: {gap} apart, {minimum}"
            " needed."
        ),
        "x_efficiency_heating": (
            "The exchanger is recovering heat, but the heater distorts the reading."
        ),
        "x_efficiency_cooling": (
            "The exchanger is recovering heat, but the cooler distorts the reading."
        ),
        "x_efficiency_preheating": (
            "The exchanger is recovering heat, but the preheater distorts the reading."
        ),
        "x_frost": "Frost protection",
        "x_frost_0": "Disabled",
        "x_frost_1": "By preheating",
        "x_frost_2": "By bypass",
        "x_frost_2_rotary": "By the rotary exchanger",
        "x_frost_3": "By stopping the supply fan",
        "x_preheater": "Preheating",
        "h_heater": "Heater",
        "h_heater_1": "Electric",
        "h_heater_2": "Water",
        "h_cooler": "Cooling",
        "h_cooler_1": "On/off",
        "h_cooler_2": "Modulating 0-10 V",
        "h_power": "Heating power",
        "h_cool_power": "Cooling power",
        "h_valve": "Water valve",
        "h_blowing": "Heater blow-down",
        "i_boost": "Boost switch",
        "i_fireplace": "Fireplace switch",
        "i_fire": "Fire alarm contact",
        "f_state": "Filters",
        "f_state_0": "Clean",
        "f_state_1": "Outdoor air filter clogged",
        "f_state_2": "Extract air filter clogged",
        "f_state_3": "Replace",
        "f_left": "Next replacement",
        "f_in": "in {}",
        "f_interval": "Replacement interval",
        "f_switch_supply": "Outdoor air filter pressure switch",
        "f_switch_extract": "Extract air filter pressure switch",
        "f_clogged": "Clogged",
        "f_clean": "Clean",
        "hours": "Total run time",
        "battery": "Clock battery",
        "firmware": "Firmware",
        "model": "Model",
        "d": "d",
        "h": "h",
        "min": "min",
    },
}

Row = dict[str, Any]


class _Builder:
    """Collect the sections of one snapshot, in one language."""

    def __init__(self, data: A21Data, language: str) -> None:
        self.data = data
        self.language = language_of(language)
        self.text = _T[self.language]
        self.sections: list[dict[str, Any]] = []

    # --- formatting ---------------------------------------------------------
    def number(self, value: float, precision: int = 0) -> str:
        text = f"{value:.{precision}f}"
        return text.replace(".", ",") if self.language == "fr" else text

    def value(self, value: float, unit: str, precision: int = 0) -> str:
        return f"{self.number(value, precision)} {unit}"

    def duration(self, seconds: int) -> str:
        days, rest = divmod(seconds, 86400)
        hours, rest = divmod(rest, 3600)
        minutes = rest // 60
        parts = []
        if days:
            parts.append(f"{days} {self.text['d']}")
        if hours:
            parts.append(f"{hours} {self.text['h']}")
        if minutes and not days:
            parts.append(f"{minutes} {self.text['min']}")
        return " ".join(parts) or f"0 {self.text['min']}"

    def choice(self, prefix: str, value: int | None) -> str | None:
        if value is None:
            return None
        return self.text.get(f"{prefix}_{value}")

    # --- structure ----------------------------------------------------------
    def section(self, key: str, rows: list[Row], **extra: Any) -> None:
        rows = [row for row in rows if row]
        if rows or extra.get("absent"):
            self.sections.append(
                {"key": key, "title": self.text[f"s_{key}"], "rows": rows, **extra}
            )

    def row(
        self,
        label: str,
        value: str | None,
        *,
        hint: str | None = None,
        level: str | None = None,
    ) -> Row:
        if value is None:
            return {}
        row: Row = {"label": self.text.get(label, label), "value": value}
        if hint:
            row["hint"] = hint
        if level:
            row["level"] = level
        return row


# Cases where heat is recovered but the efficiency cannot be worked out.
_RECOVERING_UNMEASURED = frozenset(
    {
        EFFICIENCY_SMALL_DIFFERENCE,
        EFFICIENCY_HEATING,
        EFFICIENCY_COOLING,
        EFFICIENCY_PREHEATING,
    }
)


def _present(data: A21Data, address: int, *coils: int) -> bool:
    """Return True when an optional probe is enabled or reports something."""
    return bool(data.ir(address) or any(data.coil(coil) for coil in coils))


def _alarms(b: _Builder) -> None:
    rows = [
        b.row(str(item.code), item.text, level=item.severity)
        for item in b.data.active_codes(b.language)
    ]
    b.section("alarms", rows)


def _state(b: _Builder) -> None:
    data, text = b.data, b.text
    speed = data.hr(HR_SPEED_MODE)
    if speed == SPEED_MANUAL:
        speed_text = text["speed_manual"].format(data.hr(HR_MANUAL_SPEED))
    elif speed is not None:
        speed_text = text["speed_n"].format(speed)
    else:
        speed_text = None

    timer = None
    if data.coil(CL_TIMER) is not None:
        timer = text["inactive"]
        if data.coil(CL_TIMER):
            left = data.timer_remaining
            timer = text["running"]
            if left:
                timer += ", " + text["timer_left"].format(b.duration(left))

    schedule = None
    if data.coil(CL_WEEK) is not None:
        schedule = text["inactive"]
        if data.coil(CL_WEEK):
            week_speed = data.ir(IR_WEEK_SPEED)
            now = (
                text["schedule_now"].format(week_speed)
                if week_speed
                else text["schedule_standby"]
            )
            week_temp = data.ir(IR_WEEK_TEMP)
            if week_temp:
                now += f", {week_temp} °C"
            schedule = f"{text['active']}, {now}"

    setpoint = data.hr(HR_SET_TEMP)
    rows = [
        b.row(
            "unit",
            text["on"] if data.is_on else text["off"],
            level="on" if data.is_on else None,
        ),
        b.row("mode", b.choice("mode", data.hr(HR_OPERATION_MODE))),
        b.row("speed", speed_text),
        b.row("regulation", b.choice("regulation", data.hr(HR_VENTILATION_MODE))),
        b.row("setpoint", None if setpoint is None else b.value(setpoint, "°C")),
        b.row("timer", timer),
        b.row("schedule", schedule),
    ]
    if data.coil(CL_BOOST_MODE) or data.coil(CL_BOOST_SWITCH_CTRL):
        boosting = bool(data.coil(CL_BOOST_MODE))
        rows.append(
            b.row(
                "boost",
                text["running"] if boosting else text["inactive"],
                level="on" if boosting else None,
            )
        )
    if data.coil(CL_FIREPLACE_MODE):
        rows.append(b.row("fireplace", text["running"], level="on"))
    b.section("state", rows)


def _fans(b: _Builder) -> None:
    data, text = b.data, b.text
    rows: list[Row] = []

    def pair(label: str, supply: str | None, extract: str | None) -> None:
        if supply is not None or extract is not None:
            rows.append(
                {
                    "label": text.get(label, label),
                    "values": [supply or "–", extract or "–"],
                }
            )

    def both(label: str, addresses: tuple[int, int], unit: str, show: bool) -> None:
        values = [data.ir(address) for address in addresses]
        if show and None not in values:
            pair(label, *(b.value(value, unit) for value in values))

    control = data.hr(HR_FAN_ALARM_CTRL) or 0
    regulation = data.hr(HR_VENTILATION_MODE)
    both("power", (IR_SUPPLY_FAN_PERCENT, IR_EXTRACT_FAN_PERCENT), "%", True)
    both(
        "rpm",
        (IR_SUPPLY_RPM, IR_EXTRACT_RPM),
        text["u_rpm"],
        0 < control < 255 or bool(data.ir(IR_SUPPLY_RPM) or data.ir(IR_EXTRACT_RPM)),
    )
    both(
        "flow",
        (IR_SUPPLY_FLOW, IR_EXTRACT_FLOW),
        "m³/h",
        regulation == 1 or bool(data.ir(IR_SUPPLY_FLOW) or data.ir(IR_EXTRACT_FLOW)),
    )
    both(
        "pressure",
        (IR_SUPPLY_PRESSURE, IR_EXTRACT_PRESSURE),
        "Pa",
        regulation == 2
        or bool(data.ir(IR_SUPPLY_PRESSURE) or data.ir(IR_EXTRACT_PRESSURE)),
    )

    # Percentages programmed for the speed in use.
    speed = data.hr(HR_SPEED_MODE)
    if regulation == 0 and speed is not None and 1 <= speed <= 5:
        presets = [data.hr(HR_SUPPLY_SPEED0 + 2 * speed + side) for side in (0, 1)]
        if None not in presets:
            pair(
                text["preset"].format(speed),
                *(b.value(preset, "%") for preset in presets),
            )

    # Units without a tachometer watch their fans with pressure switches.
    if control == 255:
        switches = [data.di(DI_SUPPLY_FAN_SWITCH), data.di(DI_EXTRACT_FAN_SWITCH)]
        if None not in switches:
            pair(
                "fan_switch",
                *(text["active"] if state else text["inactive"] for state in switches),
            )

    if rows:
        b.sections.append(
            {
                "key": "fans",
                "title": text["s_fans"],
                "columns": [text["supply"], text["extract"]],
                "rows": rows,
            }
        )


def _temperatures(b: _Builder) -> None:
    data = b.data

    def temp(label: str, address: int, hint: str | None = None) -> Row:
        value = data.temperature(address)
        return b.row(
            label, None if value is None else b.value(value, "°C", 1), hint=hint
        )

    rows = [
        temp("t_outdoor", IR_TEMP_OUTDOOR),
        temp("t_after_pre", IR_TEMP_AFTER_PREHEATER),
        temp("t_before_re", IR_TEMP_BEFORE_REHEATER),
        temp("t_supply", IR_TEMP_SUPPLY),
        temp("t_extract", IR_TEMP_EXTRACT),
        temp("t_exhaust", IR_TEMP_EXHAUST),
        temp("t_panel", IR_TEMP_PANEL),
        temp("t_water", IR_TEMP_WATER),
        temp(
            "t_control",
            IR_TEMP_SELECTED,
            b.choice("t_control", data.hr(HR_TEMP_SENSOR)),
        ),
    ]
    if data.hr(HR_TEMP_SENSOR) == 2 and data.hr(HR_BYPASS_TYPE):
        # Regulating on the supply air means the bypass is driven by the
        # temperature blown in, not by the room: free cooling then stops as
        # soon as the supply reaches the setpoint.
        rows[-1]["hint"] = f"{rows[-1]['hint']}. {b.text['t_control_supply']}"
    supply_setpoint = data.ir(IR_SUPPLY_SETPOINT)
    if supply_setpoint and (data.hr(HR_MAIN_HEATER_TYPE) or data.hr(HR_COOLER_TYPE)):
        rows.append(b.row("t_supply_setpoint", b.value(supply_setpoint / 10, "°C", 1)))
    b.section("temps", rows)


def _air_quality(b: _Builder) -> None:
    data, text = b.data, b.text
    rows: list[Row] = []
    absent: list[dict[str, str]] = []

    # (name, main value, main enable, external value, external enable,
    #  threshold register, "threshold exceeded" input, demand register, unit)
    probes = (
        ("rh", "humidity", IR_RH_INT, CL_INT_RH_CTRL, IR_RH_EXT, CL_EXT_RH_CTRL,
         HR_SET_RH, DI_STATUS_RH, IR_RH_DEMAND, "%"),
        ("co2", "co2", IR_CO2_INT, CL_INT_CO2_CTRL, IR_CO2_EXT, CL_EXT_CO2_CTRL,
         HR_SET_CO2, DI_STATUS_CO2, IR_CO2_DEMAND, "ppm"),
        ("pm25", "pm25", IR_PM25_INT, CL_INT_PM25_CTRL, IR_PM25_EXT, CL_EXT_PM25_CTRL,
         HR_SET_PM25, DI_STATUS_PM25, IR_PM25_DEMAND, "µg/m³"),
        ("voc", "voc", IR_VOC_INT, CL_INT_VOC_CTRL, IR_VOC_EXT, CL_EXT_VOC_CTRL,
         HR_SET_VOC, DI_STATUS_VOC, IR_VOC_DEMAND, "%"),
    )  # fmt: skip
    demand = 0
    for label, name, main, main_coil, ext, ext_coil, limit, over, pid, unit in probes:
        found = False
        threshold = data.hr(limit)
        hint = (
            None
            if threshold is None
            else text["threshold"].format(b.value(threshold, unit))
        )
        level = WARNING if data.di(over) else None
        for row_label, address, coil in (
            (label, main, main_coil),
            (f"{label}_ext", ext, ext_coil),
        ):
            if not _present(data, address, coil):
                continue
            found = True
            reading = data.ir(address)
            # Enabled but silent: the controller reports 0 and raises a warning.
            rows.append(
                b.row(
                    row_label,
                    b.value(reading, unit) if reading else "–",
                    hint=hint,
                    level=level,
                )
            )
        if found:
            demand = max(demand, data.ir(pid) or 0)
        else:
            entry = {"label": text[f"a_{name}"]}
            if name in ACCESSORIES:
                entry["url"] = ACCESSORIES[name]
            absent.append(entry)

    if _present(data, IR_10V_SENSOR, CL_10V_SENSOR_CTRL):
        rows.append(b.row("analog", b.value(data.ir(IR_10V_SENSOR) or 0, "%")))
    if demand:
        rows.append(b.row("demand", b.value(demand, "%")))

    b.section("air", rows, absent=absent, absent_label=text["absent"])


def _exchanger(b: _Builder) -> None:
    data, text = b.data, b.text
    kind = data.hr(HR_BYPASS_TYPE)
    rows: list[Row] = []
    if kind:
        rows.append(b.row("x_type", b.choice("x_type", kind)))
        position = data.ir(IR_BYPASS_STATE)
        if position is not None:
            if kind in ROTARY_TYPES:
                words = ("x_rotor_full", "x_rotor_stopped", "x_rotor_partial")
                partial = 100 - position
                label = "x_rotor"
            else:
                words = ("x_closed", "x_open", "x_partial")
                partial = position
                label = "x_position"
            if position <= 0:
                state = text[words[0]]
            elif position >= 100:
                state = text[words[1]]
            else:
                state = text[words[2]].format(partial)
            rows.append(b.row(label, state, level="on" if position > 0 else None))
        manual = data.hr(HR_BYPASS_MODE) in (0, 1)
        by_bypass = data.hr(HR_DEFROST_MODE) == 2
        rows.append(
            b.row(
                "x_mode",
                b.choice("x_mode", data.hr(HR_BYPASS_MODE)),
                hint=text["x_mode_frost"] if manual and by_bypass else None,
            )
        )
        if kind not in ROTARY_TYPES:
            rows.append(b.row("x_side", b.choice("x_side", data.hr(HR_BYPASS_SIDE))))
        signal = data.ir(IR_BYPASS_OUTPUT)
        if signal is not None:
            # The position above is where the controller believes the damper
            # is; the command is where it is sending it. They differ while a
            # three-point actuator travels (48 s or so for a full stroke).
            moving = position is not None and min(signal, 100) != position
            rows.append(
                b.row(
                    "x_signal",
                    b.value(min(signal, 100), "%"),
                    hint=text["x_signal_moving"] if moving else None,
                )
            )

    efficiency = data.efficiency
    status = data.efficiency_status
    if efficiency is not None:
        rows.append(b.row("x_efficiency", b.value(efficiency, "%")))
    elif status in _RECOVERING_UNMEASURED:
        # The exchanger works, only the figure is missing: say so, and why.
        gap = data.temperature_difference or 0.0
        hint = b.text[f"x_efficiency_{status}"].format(
            gap=b.value(gap, "°C", 1), minimum=b.value(MIN_EFFICIENCY_DELTA, "°C")
        )
        rows.append(b.row("x_efficiency", b.text["x_efficiency_unmeasured"], hint=hint))
    frost = data.hr(HR_DEFROST_MODE)
    frost_text = b.choice("x_frost", frost)
    if frost == 2 and kind in ROTARY_TYPES:
        frost_text = text["x_frost_2_rotary"]
    rows.append(b.row("x_frost", frost_text))
    preheater = data.ir(IR_PREHEATER_OUTPUT)
    if preheater is not None and (frost == 1 or preheater):
        rows.append(
            b.row(
                "x_preheater",
                b.value(min(preheater, 100), "%"),
                level="on" if preheater else None,
            )
        )
    b.section("exchanger", rows)


def _heating(b: _Builder) -> None:
    data, text = b.data, b.text
    rows: list[Row] = []
    heater = data.hr(HR_MAIN_HEATER_TYPE)
    if heater:
        running = bool(data.di(DI_STATUS_HEATER))
        rows.append(
            b.row(
                "h_heater",
                f"{b.choice('h_heater', heater) or ''}, "
                f"{(text['on'] if running else text['off']).lower()}".lstrip(", "),
                level="on" if running else None,
            )
        )
        power = data.ir(IR_REHEATER_OUTPUT)
        if power is not None:
            rows.append(b.row("h_power", b.value(min(power, 100), "%")))
        if heater == 2:
            valve = data.ir(IR_WATER_OUTPUT)
            if valve is not None:
                rows.append(b.row("h_valve", b.value(valve, "%")))
        if data.di(DI_STATUS_FAN_BLOWING):
            rows.append(b.row("h_blowing", text["running"], level="on"))
    cooler = data.hr(HR_COOLER_TYPE)
    if cooler:
        running = bool(data.di(DI_STATUS_COOLER))
        rows.append(
            b.row(
                "h_cooler",
                f"{b.choice('h_cooler', cooler) or ''}, "
                f"{(text['on'] if running else text['off']).lower()}".lstrip(", "),
                level="on" if running else None,
            )
        )
        power = data.ir(IR_COOLER_OUTPUT)
        if power is not None:
            rows.append(b.row("h_cool_power", b.value(power, "%")))
    b.section("heating", rows)


def _inputs(b: _Builder) -> None:
    data, text = b.data, b.text
    rows: list[Row] = []
    for label, enable, state, level in (
        ("i_boost", CL_BOOST_SWITCH_CTRL, DI_BOOST_SWITCH, "on"),
        ("i_fireplace", CL_FIREPLACE_SWITCH_CTRL, DI_FIREPLACE_SWITCH, "on"),
        ("i_fire", CL_FIRE_ALARM_CTRL, DI_FIRE_ALARM, ALARM),
    ):
        if data.coil(enable) and data.di(state) is not None:
            active = bool(data.di(state))
            rows.append(
                b.row(
                    label,
                    text["active"] if active else text["inactive"],
                    level=level if active else None,
                )
            )
    b.section("inputs", rows)


def _service(b: _Builder, model: Model) -> None:
    data, text = b.data, b.text
    rows: list[Row] = []
    state = data.ir(IR_FILTER_STATE)
    rows.append(
        b.row(
            "f_state",
            b.choice("f_state", state),
            level=WARNING if state else None,
        )
    )
    interval = data.hr(HR_FILTER_TIMER)
    days, hours_min = data.ir(IR_FILTER_DAYS), data.ir(IR_FILTER_HOURS_MIN)
    if interval and days is not None:
        left = days * 86400 + ((hours_min or 0) >> 8) * 3600
        rows.append(b.row("f_left", text["f_in"].format(b.duration(left))))
        rows.append(b.row("f_interval", f"{interval} {text['d']}"))
    for label, address in (
        ("f_switch_supply", DI_SUPPLY_FILTER_SWITCH),
        ("f_switch_extract", DI_EXTRACT_FILTER_SWITCH),
    ):
        # Only worth a line when a pressure switch actually reports a clogged
        # filter: most units have none and the input then stays at rest.
        if data.di(address):
            rows.append(b.row(label, text["f_clogged"], level=WARNING))
    run_time = data.operating_hours
    if run_time is not None:
        rows.append(b.row("hours", b.duration(run_time * 3600)))
    battery = data.ir(IR_RTC_BATTERY)
    if battery:
        rows.append(
            b.row(
                "battery",
                b.value(battery / 1000, "V", 2),
                level=WARNING if battery < 2000 else None,
            )
        )
    rows.append(b.row("firmware", data.firmware))
    reference = f" ({model.reference})" if model.reference else ""
    rows.append(b.row("model", f"{model.name}{reference}"))
    b.section("service", rows)


def build_details(
    data: A21Data | None, *, name: str, model: Model, language: str, available: bool
) -> dict[str, Any]:
    """Return the full, readable snapshot of one unit."""
    if data is None or not available:
        return {"name": name, "available": False, "sections": []}
    builder = _Builder(data, language)
    _alarms(builder)
    _state(builder)
    _fans(builder)
    _temperatures(builder)
    _air_quality(builder)
    _exchanger(builder)
    _heating(builder)
    _inputs(builder)
    _service(builder, model)
    codes = data.active_codes(language)
    return {
        "name": name,
        "available": True,
        "on": data.is_on,
        "level": (
            ALARM
            if any(item.severity == ALARM for item in codes)
            else WARNING
            if codes
            else None
        ),
        "sections": builder.sections,
    }
