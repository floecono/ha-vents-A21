"""Meaning of the alarm codes of the A21 controller.

The Modbus table only numbers the codes (discrete inputs 19 to 71 are codes
0 to 52). Their meaning comes from the installer manual of the unit
(DF Connect application manual, section "Codes d'alarmes et
d'avertissements"), which documents codes 0 to 45.

An alarm stops the unit and must be reset by hand. A warning leaves the unit
running and clears by itself once its cause is gone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

ALARM: Final = "alarm"
WARNING: Final = "warning"

# code: (severity, French, English)
CODES: Final[dict[int, tuple[str, str, str]]] = {
    0: (ALARM, "Défaut du ventilateur de soufflage", "Supply fan fault"),
    1: (ALARM, "Défaut du ventilateur d'extraction", "Extract fan fault"),
    2: (ALARM, "Sonde d'air neuf absente", "Outdoor air sensor missing"),
    3: (ALARM, "Sonde d'air neuf en court-circuit", "Outdoor air sensor shorted"),
    4: (ALARM, "Sonde d'air soufflé absente", "Supply air sensor missing"),
    5: (ALARM, "Sonde d'air soufflé en court-circuit", "Supply air sensor shorted"),
    6: (ALARM, "Sonde d'air extrait absente", "Extract air sensor missing"),
    7: (ALARM, "Sonde d'air extrait en court-circuit", "Extract air sensor shorted"),
    8: (ALARM, "Sonde d'air rejeté absente", "Exhaust air sensor missing"),
    9: (ALARM, "Sonde d'air rejeté en court-circuit", "Exhaust air sensor shorted"),
    10: (
        ALARM,
        "Thermostat de sécurité du préchauffage déclenché",
        "Preheater safety thermostat tripped",
    ),
    11: (
        ALARM,
        "Thermostat de sécurité de la batterie de chauffage déclenché",
        "Heater safety thermostat tripped",
    ),
    12: (
        ALARM,
        "Le préchauffage ne suffit plus à protéger l'échangeur du gel",
        "Preheating can no longer protect the exchanger from frost",
    ),
    13: (WARNING, "Sonde d'humidité non détectée", "Humidity sensor not detected"),
    14: (WARNING, "Sonde de CO₂ non détectée", "CO₂ sensor not detected"),
    15: (WARNING, "Sonde de PM2.5 non détectée", "PM2.5 sensor not detected"),
    16: (WARNING, "Sonde de COV non détectée", "VOC sensor not detected"),
    17: (
        WARNING,
        "Sonde d'humidité externe non détectée",
        "External humidity sensor not detected",
    ),
    18: (
        WARNING,
        "Sonde de CO₂ externe non détectée",
        "External CO₂ sensor not detected",
    ),
    19: (
        WARNING,
        "Sonde de PM2.5 externe non détectée",
        "External PM2.5 sensor not detected",
    ),
    20: (
        WARNING,
        "Sonde de COV externe non détectée",
        "External VOC sensor not detected",
    ),
    21: (
        WARNING,
        "Température ambiante non reçue du boîtier de commande",
        "No room temperature from the control panel",
    ),
    22: (WARNING, "Risque de gel de l'échangeur", "Exchanger frost risk"),
    23: (WARNING, "Pile de l'horloge faible", "Clock battery low"),
    24: (WARNING, "Filtre d'air neuf encrassé", "Outdoor air filter clogged"),
    25: (ALARM, "Alarme incendie", "Fire alarm"),
    26: (ALARM, "Air soufflé trop froid", "Supply air too cold"),
    27: (ALARM, "Sonde de retour d'eau absente", "Return water sensor missing"),
    28: (
        ALARM,
        "Sonde de retour d'eau en court-circuit",
        "Return water sensor shorted",
    ),
    29: (WARNING, "Filtre d'air extrait encrassé", "Extract air filter clogged"),
    30: (ALARM, "Pas de pression d'eau", "No water pressure"),
    31: (ALARM, "Pas de débit d'eau", "No water flow"),
    32: (ALARM, "Retour d'eau trop froid", "Return water too cold"),
    33: (
        ALARM,
        "L'arrêt du soufflage ne suffit plus à protéger l'échangeur du gel",
        "Stopping the supply fan can no longer protect the exchanger from frost",
    ),
    34: (
        ALARM,
        "Le bypass ne suffit plus à protéger l'échangeur du gel",
        "The bypass can no longer protect the exchanger from frost",
    ),
    35: (WARNING, "Protection antigel désactivée", "Frost protection disabled"),
    36: (
        WARNING,
        "Batterie de chauffage en mode manuel",
        "Heater in manual mode",
    ),
    37: (WARNING, "Refroidissement en mode manuel", "Cooler in manual mode"),
    38: (WARNING, "Bypass en mode manuel", "Bypass in manual mode"),
    39: (
        WARNING,
        "Échangeur rotatif en mode manuel",
        "Rotary exchanger in manual mode",
    ),
    40: (WARNING, "Échéance des filtres atteinte", "Filter timer expired"),
    41: (WARNING, "Défaut de l'échangeur rotatif", "Rotary exchanger malfunction"),
    42: (WARNING, "Préchauffage en mode manuel", "Preheater in manual mode"),
    43: (
        ALARM,
        "Retour d'eau trop froid pour démarrer",
        "Return water too cold to start",
    ),
    44: (
        WARNING,
        "Antigel par bypass remplacé par l'arrêt du soufflage",
        "Bypass frost protection replaced by supply fan protection",
    ),
    45: (
        WARNING,
        "Mode cheminée bloqué par la protection antigel",
        "Fireplace mode locked by the frost protection",
    ),
}

# Codes that only say "change the filters": the filter entities and the
# filter notice of the card already cover them.
FILTER_CODES: Final = frozenset({24, 29, 40})


@dataclass(frozen=True, slots=True)
class ActiveCode:
    """One active alarm or warning."""

    code: int
    severity: str
    text: str

    @property
    def label(self) -> str:
        """Return the text with its code, e.g. '0 – Supply fan fault'."""
        return f"{self.code} – {self.text}"

    def as_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly form for state attributes."""
        return {"code": self.code, "type": self.severity, "text": self.text}


def language_of(language: str | None) -> str:
    """Return 'fr' or 'en' for a Home Assistant language tag."""
    return "fr" if (language or "").lower().startswith("fr") else "en"


def describe(code: int, language: str | None, fallback_severity: str) -> ActiveCode:
    """Describe one code.

    A code the manual does not document (46 to 52, newer firmware) keeps its
    number and takes the overall severity reported by the controller.
    """
    known = CODES.get(code)
    if known is None:
        text = f"Code {code}"
        return ActiveCode(code, fallback_severity, text)
    severity, french, english = known
    return ActiveCode(
        code, severity, french if language_of(language) == "fr" else english
    )
