/*
 * Dashboard cards for heat recovery ventilation units with the A21 controller
 * (ECONOPRIME Connect range, VENTS A21):
 *   - vents-a21-card: the unit at a glance, for everyday use;
 *   - vents-a21-details-card: every value the controller reports.
 *
 * Shipped with the vents_a21 integration, which loads it in every dashboard:
 * there is no resource to declare. Plain JavaScript, no build step.
 *
 * The four air streams are coloured from their measured temperature, so the
 * drawing shows what the heat exchanger is doing right now.
 */

const DOMAIN = "vents_a21";
const CARD = "vents-a21-card";
const DETAILS_CARD = "vents-a21-details-card";
const UTM = "?utm_source=home-assistant&utm_medium=card&utm_campaign=vents_a21";
const SHOP = "https://www.econology.fr/";

// Replacement filters per model. Keep in sync with MODELS in const.py
// (tests/test_frontend.py checks it).
const FILTERS = {
  "Zephyr 240 S Connect": "filtre-f7-vmc-double-flux-zephyr-240-fzeph240f7-econoprime.html",
  "Zephyr 270 V Connect R": "filtre-f7-zephyr-270-12300001-econoprime.html",
  "Zephyr 550 V PH Connect R": "vmc-double-flux-zephyr-550-v-ph-connect-r-econoprime-114800003.html",
  "DF 180 Flat Connect": "filtre-vmc-double-flux-df-180-econoprime.html",
  "DF 270 Connect": "filtre-vmc-double-flux-df-270-econoprime.html",
  "DF 350 Connect": "filtre-vmc-double-flux-df-350-econoprime.html",
};

// Alarm codes that only say "change the filters": the filter notice covers them.
const FILTER_CODES = new Set([24, 29, 40]);
// Warnings "bypass / rotary exchanger in manual mode": expected, and so not
// shown, when the owner drives the bypass from this card.
const MANUAL_BYPASS_CODES = new Set([38, 39]);
// Outdoor temperature (°C) under which a hand-driven bypass on a unit whose
// frost protection relies on the bypass gets a reminder.
const FROST_WARNING_BELOW = 5;

// Days before the filter deadline from which the reminder is shown, unless
// the card options say otherwise (0: only once the deadline is reached).
const FILTER_SOON_DAYS = 21;
const FILTER_SOON_MAX = 120;

const TEXT = {
  fr: {
    outdoor: "Air neuf",
    supply: "Air soufflé",
    extract: "Air extrait",
    exhaust: "Air rejeté",
    outside: "Extérieur",
    inside: "Intérieur",
    recovered: "récupérés",
    exchangerOn: "Actif",
    gapBelow: (n) => `écart < ${n} °C`,
    whyHeating: "chauffage",
    whyCooling: "refroidit",
    whyPreheating: "antigel",
    recovery: "Récupération",
    recoveryGap: (gap) => `active, rendement non mesurable (${gap} °C d'écart)`,
    recoveryHeating: "active, rendement non mesurable (chauffage)",
    recoveryCooling: "active, rendement non mesurable (refroidissement)",
    recoveryPreheating: "active, rendement non mesurable (préchauffage antigel)",
    bypassControl: "Commande du bypass",
    frostByBypass:
      "Bypass en manuel : sans préchauffage, c'est le bypass qui protège l'échangeur du gel. En hiver, repassez en automatique.",
    bypassAuto: "Auto",
    bypassOpened: "Ouvert",
    bypassShut: "Fermé",
    bypass: "Bypass",
    bypassOpen: "ouvert",
    bypassClosed: "fermé",
    bypassOpening: (p) => `s'ouvre (${p} %)`,
    bypassClosing: (p) => `se ferme (${p} %)`,
    rotor: "Rotor",
    rotorFact: "Échangeur rotatif",
    rotorStopped: "à l'arrêt",
    rotorFull: "pleine vitesse",
    code: (n) => `code ${n}`,
    running: "En marche",
    withAlarm: "alarme en cours",
    withWarning: "avertissement en cours",
    notInstalled: "Sondes non installées",
    off: "À l'arrêt",
    unavailable: "Machine injoignable",
    speed: (n) => `Vitesse ${n}`,
    manual: "Manuelle",
    manualAt: (p) => `Vitesse manuelle ${p} %`,
    manualSlider: "Vitesse manuelle",
    setpoint: "Consigne",
    noSetpoint: "pas de régulation",
    boost: "boost en cours",
    timer: "minuterie en cours",
    schedule: "programmation hebdomadaire",
    heating: "chauffage en marche",
    cooling: "refroidissement en marche",
    turnOn: "Mettre en marche",
    turnOff: "Arrêter",
    speeds: "Vitesse de ventilation",
    humidity: "Humidité",
    co2: "CO₂",
    fans: "Ventilateurs",
    filters: "Filtres",
    days: (n) => `${n} j`,
    filtersDue: "Filtres à remplacer",
    filtersSoon: (n) => `Filtres à remplacer dans ${n} jour${n > 1 ? "s" : ""}`,
    orderFilters: "Commander les filtres",
    alarm: "Alarme",
    warning: "Avertissement",
    brand: "Filtres et accessoires sur econology.fr",
    noDevice: "Aucune machine trouvée. Ajoutez d'abord l'intégration dans Paramètres, Appareils et services.",
    pickDevice: "Machine",
    name: "Nom affiché (facultatif)",
    filterLink: "Afficher le lien pour commander les filtres quand ils sont à remplacer",
    filterDays: "Rappel des filtres : nombre de jours avant l'échéance (0 : à l'échéance seulement)",
    bypassOption: "Afficher la commande manuelle du bypass (automatique, ouvert, fermé)",
    cardName: "VMC double flux ECONOPRIME / VENTS A21",
    cardDescription: "Vue de la machine : températures des quatre flux d'air, rendement, bypass, vitesses, filtres.",
    detailsName: "VMC double flux ECONOPRIME / VENTS A21 : toutes les mesures",
    detailsDescription: "Vue technique : ventilateurs (puissance, régime, débit, pression), toutes les sondes, échangeur, batteries, entretien, alarmes en clair.",
  },
  en: {
    outdoor: "Outdoor air",
    supply: "Supply air",
    extract: "Extract air",
    exhaust: "Exhaust air",
    outside: "Outside",
    inside: "Inside",
    recovered: "recovered",
    exchangerOn: "Active",
    gapBelow: (n) => `gap < ${n} °C`,
    whyHeating: "heating",
    whyCooling: "cooling",
    whyPreheating: "frost guard",
    recovery: "Heat recovery",
    recoveryGap: (gap) => `active, efficiency not measurable (${gap} °C apart)`,
    recoveryHeating: "active, efficiency not measurable (heating)",
    recoveryCooling: "active, efficiency not measurable (cooling)",
    recoveryPreheating: "active, efficiency not measurable (preheating)",
    bypassControl: "Bypass control",
    frostByBypass:
      "Bypass in manual mode: without a preheater, the bypass is what protects the exchanger from frost. Switch back to automatic in winter.",
    bypassAuto: "Auto",
    bypassOpened: "Open",
    bypassShut: "Closed",
    bypass: "Bypass",
    bypassOpen: "open",
    bypassClosed: "closed",
    bypassOpening: (p) => `opening (${p} %)`,
    bypassClosing: (p) => `closing (${p} %)`,
    rotor: "Rotor",
    rotorFact: "Rotary exchanger",
    rotorStopped: "stopped",
    rotorFull: "full speed",
    code: (n) => `code ${n}`,
    running: "Running",
    withAlarm: "alarm active",
    withWarning: "warning active",
    notInstalled: "Sensors not installed",
    off: "Off",
    unavailable: "Unit unreachable",
    speed: (n) => `Speed ${n}`,
    manual: "Manual",
    manualAt: (p) => `Manual speed ${p} %`,
    manualSlider: "Manual speed",
    setpoint: "Setpoint",
    noSetpoint: "no regulation",
    boost: "boost running",
    timer: "timer running",
    schedule: "weekly schedule",
    heating: "heating",
    cooling: "cooling",
    turnOn: "Turn on",
    turnOff: "Turn off",
    speeds: "Ventilation speed",
    humidity: "Humidity",
    co2: "CO₂",
    fans: "Fans",
    filters: "Filters",
    days: (n) => `${n} d`,
    filtersDue: "Filters need replacing",
    filtersSoon: (n) => `Filters need replacing in ${n} day${n > 1 ? "s" : ""}`,
    orderFilters: "Order filters",
    alarm: "Alarm",
    warning: "Warning",
    brand: "Filters and accessories on econology.fr",
    noDevice: "No unit found. Add the integration first in Settings, Devices & services.",
    pickDevice: "Unit",
    name: "Displayed name (optional)",
    filterLink: "Show the link to order filters when they need replacing",
    filterDays: "Filter reminder: days before the deadline (0: only at the deadline)",
    bypassOption: "Show the manual bypass control (automatic, open, closed)",
    cardName: "ECONOPRIME / VENTS A21 ventilation unit",
    cardDescription: "View of the unit: temperature of the four air streams, efficiency, bypass, speeds, filters.",
    detailsName: "ECONOPRIME / VENTS A21 ventilation unit: every measurement",
    detailsDescription: "Technical view: fans (power, speed, airflow, pressure), every probe, exchanger, heaters, maintenance, alarms in plain words.",
  },
};

const COLD = [47, 134, 214];
const WARM = [240, 138, 36];
const IDLE = "var(--disabled-text-color, #9e9e9e)";

const STYLE = `
  :host { --a21-green: #52ae32; display: block; }
  ha-card { display: block; padding: 16px 16px 10px; overflow: hidden; }
  button { font: inherit; color: inherit; background: none; border: 0; padding: 0; cursor: pointer; }
  button:focus-visible, a:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; border-radius: 6px; }

  .head { display: flex; align-items: center; gap: 12px; }
  .title { flex: 1; min-width: 0; text-align: left; }
  .name { font-size: 1.25rem; font-weight: 500; line-height: 1.3; color: var(--primary-text-color);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .status { font-size: .875rem; line-height: 1.4; color: var(--secondary-text-color); }
  .power { flex: none; width: 44px; height: 44px; border-radius: 50%;
           border: 1.5px solid var(--divider-color); color: var(--secondary-text-color);
           display: grid; place-items: center; transition: background-color .2s, color .2s, border-color .2s; }
  .power svg { width: 22px; height: 22px; }
  .power[aria-pressed="true"] { background: var(--a21-green); border-color: var(--a21-green); color: #fff; }

  .notice { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 4px 12px; margin-top: 12px;
            padding: 10px 12px; border-radius: 10px; font-size: .875rem; line-height: 1.35;
            color: var(--primary-text-color); background: color-mix(in srgb, var(--a21-tone) 14%, transparent); }
  .notice::before { content: ""; flex: none; width: 8px; height: 8px; margin-top: 6px; border-radius: 50%; background: var(--a21-tone); }
  .notice small { font-size: .75rem; color: var(--secondary-text-color); white-space: nowrap; }
  .notice span { flex: 1; min-width: 12ch; }
  .notice a { color: var(--primary-text-color); font-weight: 500; text-underline-offset: 3px; }
  .notice.alarm { --a21-tone: var(--error-color, #db4437); }
  .notice.warning, .notice.filter, .notice.frost { --a21-tone: var(--warning-color, #ffa600); }

  .unit { display: block; width: 100%; height: auto; margin: 14px 0 6px; }
  .unit text { fill: var(--primary-text-color); font-family: inherit; }
  .unit .side { fill: var(--secondary-text-color); font-size: 11px; }
  .unit .label { fill: var(--secondary-text-color); font-size: 12px; }
  .unit .temp { font-size: 24px; font-weight: 500; font-variant-numeric: tabular-nums; }
  .unit .setpoint { font-size: 12px; text-anchor: middle; fill: var(--secondary-text-color); }
  .unit .setpoint tspan.v { font-size: 14px; font-weight: 500; fill: var(--primary-text-color); font-variant-numeric: tabular-nums; }
  .unit .casing { fill: var(--secondary-background-color, rgba(127,127,127,.12)); stroke: var(--divider-color); }
  .unit .core { fill: var(--card-background-color, #fff); stroke: var(--divider-color); stroke-width: 1.5; }
  .unit .eff { font-size: 19px; font-weight: 500; text-anchor: middle; font-variant-numeric: tabular-nums; }
  .unit .eff.word { font-size: 14px; }
  .unit .effLabel { font-size: 10px; text-anchor: middle; fill: var(--secondary-text-color); }
  .unit .stream { fill: none; stroke-width: 9; stroke-linecap: round; stroke-linejoin: round; }
  .unit .gap { fill: none; stroke: var(--secondary-background-color, #eee); stroke-width: 16; stroke-linejoin: round; }
  .unit .motion { fill: none; stroke: rgba(255,255,255,.75); stroke-width: 2.5; stroke-linecap: round;
                  stroke-dasharray: 1 17; animation: a21-flow var(--a21-period, 2s) linear infinite; }
  .unit .hit { fill: transparent; cursor: pointer; }
  .unit.stopped .motion { display: none; }
  .unit.stopped .stream, .unit.stopped .head-arrow { opacity: .55; }
  @keyframes a21-flow { to { stroke-dashoffset: -18; } }
  @media (prefers-reduced-motion: reduce) { .unit .motion { animation: none; } }

  .speeds { display: flex; gap: 6px; margin-top: 6px; }
  .speeds button { flex: 1 1 0; min-width: 0; height: 40px; border-radius: 10px; font-size: .9375rem;
                   white-space: nowrap;
                   border: 1.5px solid var(--divider-color); color: var(--primary-text-color);
                   transition: background-color .15s, border-color .15s, color .15s; }
  .speeds button[aria-pressed="true"] { background: var(--a21-green); border-color: var(--a21-green); color: #fff; font-weight: 500; }
  .speeds button[data-mode="manual"] { flex: 0 0 auto; padding: 0 12px; }
  .speeds button:disabled { opacity: .45; cursor: default; }

  .manual { display: flex; align-items: center; gap: 10px; margin-top: 8px; font-size: .875rem; color: var(--secondary-text-color); }
  .manual input { flex: 1 1 0; min-width: 0; accent-color: var(--a21-green); cursor: pointer; }
  .manual output { flex: none; min-width: 4ch; text-align: right; font-weight: 500; color: var(--primary-text-color);
                   font-variant-numeric: tabular-nums; }
  .bypassctl { display: flex; align-items: center; gap: 6px; margin-top: 8px; }
  .bypassctl > span { flex: 1 1 0; min-width: 0; font-size: .875rem; color: var(--secondary-text-color); }
  .bypassctl button { flex: 0 0 auto; height: 34px; padding: 0 14px; border-radius: 10px; font-size: .875rem;
                      white-space: nowrap;
                      border: 1.5px solid var(--divider-color); color: var(--primary-text-color);
                      transition: background-color .15s, border-color .15s, color .15s; }
  .bypassctl button[aria-pressed="true"] { background: var(--a21-green); border-color: var(--a21-green); color: #fff; font-weight: 500; }
  .bypassctl button:disabled { opacity: .45; cursor: default; }

  .facts { display: flex; flex-wrap: wrap; gap: 4px 18px; margin-top: 12px; }
  .facts button { font-size: .875rem; line-height: 1.6; color: var(--secondary-text-color); text-align: left; }
  .facts b { font-weight: 500; color: var(--primary-text-color); font-variant-numeric: tabular-nums; }
  .facts .due b { color: var(--warning-color, #ffa600); }

  .brand { display: flex; justify-content: flex-end; margin-top: 8px; }
  .brand a { display: inline-flex; align-items: center; gap: 6px; font-size: .6875rem; letter-spacing: .04em;
             text-decoration: none; color: var(--secondary-text-color); opacity: .6; transition: opacity .15s, color .15s; }
  .brand svg { width: 11px; height: 12px; fill: currentColor; }
  .brand a:hover, .brand a:focus-visible { opacity: 1; color: var(--a21-green); }

  .empty { color: var(--secondary-text-color); font-size: .875rem; line-height: 1.5; }
  [hidden] { display: none !important; }
`;

// The two air streams. "through" crosses the exchanger, where the stream
// changes temperature; "around" is the same stream going past it when the
// bypass is open, and "gap" the part of that detour drawn over the other
// stream.
const STREAMS = {
  fresh: {
    through: "M12 62 H150 L250 138 H380",
    around: "M12 62 H146 L134 100 L200 164 L250 138 H380",
    gap: "M146 62 L134 100 L200 164 L250 138",
  },
  stale: {
    through: "M388 62 H250 L150 138 H20",
    around: "M388 62 H254 L266 100 L200 164 L150 138 H20",
    gap: "M254 62 L266 100 L200 164 L150 138",
  },
};

const TEMPLATE = `
  <ha-card>
    <div class="body">
      <div class="head">
        <button class="title" data-more="climate">
          <div class="name"></div>
          <div class="status"></div>
        </button>
        <button class="power" aria-pressed="false">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <path d="M12 3v9"/><path d="M6.4 6.8a8 8 0 1 0 11.2 0"/>
          </svg>
        </button>
      </div>

      <div class="notice alarm" hidden><span></span></div>
      <div class="notice warning" hidden><span></span></div>
      <div class="notice frost" hidden><span></span></div>
      <div class="notice filter" hidden><span></span><a target="_blank" rel="noopener"></a></div>

      <svg class="unit" viewBox="0 0 400 200" role="img">
        <defs>
          <linearGradient id="g-fresh" gradientUnits="userSpaceOnUse" x1="12" x2="388" y1="0" y2="0">
            <stop offset=".42" data-stop="outdoor"/><stop offset=".58" data-stop="supply"/>
          </linearGradient>
          <linearGradient id="g-stale" gradientUnits="userSpaceOnUse" x1="388" x2="12" y1="0" y2="0">
            <stop offset=".42" data-stop="extract"/><stop offset=".58" data-stop="exhaust"/>
          </linearGradient>
        </defs>

        <text class="setpoint" x="200" y="15"></text>
        <rect class="casing" x="128" y="24" width="144" height="152" rx="16"/>
        <text class="side" x="12" y="104" data-text="outside"></text>
        <text class="side" x="388" y="104" text-anchor="end" data-text="inside"></text>

        <g class="streams">
          <g data-stream="stale">
            <path class="gap"/>
            <path class="stream" d="${STREAMS.stale.through}" stroke="url(#g-stale)"/>
            <path class="motion" d="${STREAMS.stale.through}"/>
          </g>
          <g data-stream="fresh">
            <path class="gap"/>
            <path class="stream" d="${STREAMS.fresh.through}" stroke="url(#g-fresh)"/>
            <path class="motion" d="${STREAMS.fresh.through}"/>
          </g>
        </g>
        <path class="head-arrow" data-arrow="supply" d="M378 127 L394 138 L378 149 Z"/>
        <path class="head-arrow" data-arrow="exhaust" d="M22 127 L6 138 L22 149 Z"/>

        <path class="core" d="M200 54 L246 100 L200 146 L154 100 Z"/>
        <text class="eff" x="200" y="104"></text>
        <text class="effLabel" x="200" y="118"></text>

        <text class="label" x="12" y="24" data-text="outdoor"></text>
        <text class="temp" x="12" y="50" data-temp="outdoor"></text>
        <text class="label" x="388" y="24" text-anchor="end" data-text="extract"></text>
        <text class="temp" x="388" y="50" text-anchor="end" data-temp="extract"></text>
        <text class="temp" x="12" y="174" data-temp="exhaust"></text>
        <text class="label" x="12" y="192" data-text="exhaust"></text>
        <text class="temp" x="388" y="174" text-anchor="end" data-temp="supply"></text>
        <text class="label" x="388" y="192" text-anchor="end" data-text="supply"></text>

        <rect class="hit" x="0" y="0" width="126" height="100" data-more="outdoor"/>
        <rect class="hit" x="274" y="0" width="126" height="100" data-more="extract"/>
        <rect class="hit" x="0" y="100" width="126" height="100" data-more="exhaust"/>
        <rect class="hit" x="274" y="100" width="126" height="100" data-more="supply"/>
        <rect class="hit" x="154" y="54" width="92" height="92" data-more="efficiency"/>
        <rect class="hit" x="128" y="0" width="144" height="22" data-more="climate"/>
      </svg>

      <div class="speeds" role="group"></div>
      <div class="manual" hidden><span></span><input type="range"><output></output></div>
      <div class="bypassctl" role="group" hidden><span></span></div>
      <div class="facts"></div>
    </div>
    <div class="empty" hidden></div>
    <div class="brand">
      <a target="_blank" rel="noopener" href="${SHOP}${UTM}">
        <svg viewBox="0 0 51.54 57.64" aria-hidden="true">
          <rect x=".84" y="44.97" width="49.79" height="11.67"/>
          <polygon points="50.64 7.03 50.64 18.6 28.51 13.06 12.46 16.15 12.46 24.04 .84 24.04 .84 7.03 28.57 1.48 50.64 7.03"/>
          <polygon points=".84 26.02 50.63 26.02 50.63 37.69 12.46 37.69 12.46 42.98 .84 42.98 .84 26.02"/>
        </svg>
        econology.fr
      </a>
    </div>
  </ha-card>
`;

// What the card reads, as "<entity domain>.<translation key>" of the integration.
const SOURCES = {
  climate: "climate.ventilation",
  outdoor: "sensor.outdoor_temperature",
  supply: "sensor.supply_temperature",
  extract: "sensor.extract_temperature",
  exhaust: "sensor.exhaust_temperature",
  efficiency: "sensor.heat_recovery_efficiency",
  humidity: "sensor.humidity",
  co2: "sensor.co2",
  supplyFan: "sensor.supply_fan_speed",
  extractFan: "sensor.extract_fan_speed",
  bypass: "sensor.bypass_position",
  bypassMode: "select.bypass_mode",
  filterDays: "sensor.filter_days_remaining",
  filterAlert: "binary_sensor.filter",
  alarmState: "sensor.alarm_state",
  alarms: "sensor.active_alarms",
  boost: "binary_sensor.boost",
  heating: "binary_sensor.heating",
  cooling: "binary_sensor.cooling",
  timer: "switch.timer",
  schedule: "switch.weekly_schedule",
  manualSpeed: "number.manual_speed",
};

function devicesOf(hass) {
  const ids = new Set();
  for (const entity of Object.values(hass.entities || {})) {
    if (entity.platform === DOMAIN && entity.device_id) ids.add(entity.device_id);
  }
  return [...ids];
}

function number(stateObj) {
  if (!stateObj) return null;
  const value = Number.parseFloat(stateObj.state);
  return Number.isFinite(value) ? value : null;
}

function mix(ratio) {
  const t = Math.min(Math.max(ratio, 0), 1);
  const channel = (i) => Math.round(COLD[i] + (WARM[i] - COLD[i]) * t);
  return `rgb(${channel(0)}, ${channel(1)}, ${channel(2)})`;
}

const FORM_LABELS = {
  device_id: "pickDevice",
  name: "name",
  filter_link: "filterLink",
  filter_reminder_days: "filterDays",
  bypass_control: "bypassOption",
};

/** Options shown by the visual editor of both cards, plus their own extras. */
function configForm(extra = []) {
  return {
    schema: [
      { name: "device_id", required: true, selector: { device: { integration: DOMAIN } } },
      { name: "name", selector: { text: {} } },
      ...extra,
    ],
    computeLabel: (field, hass) => {
      const text = TEXT[(hass?.language || "en").startsWith("fr") ? "fr" : "en"];
      return text[FORM_LABELS[field.name]];
    },
  };
}

class VentsA21Card extends HTMLElement {
  static getStubConfig(hass) {
    return { device_id: devicesOf(hass)[0] || "" };
  }

  static getConfigForm() {
    return configForm([
      {
        name: "filter_reminder_days",
        default: FILTER_SOON_DAYS,
        selector: { number: { min: 0, max: FILTER_SOON_MAX, step: 1, mode: "box" } },
      },
      { name: "filter_link", selector: { boolean: {} } },
      { name: "bypass_control", selector: { boolean: {} } },
    ]);
  }

  setConfig(config) {
    this._config = config || {};
    this._signature = null;
    if (this._hass) this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  getCardSize() {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 9, min_rows: 5 };
  }

  _build() {
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>${TEMPLATE}`;
    const root = this.shadowRoot;
    this._el = {
      body: root.querySelector(".body"),
      empty: root.querySelector(".empty"),
      name: root.querySelector(".name"),
      status: root.querySelector(".status"),
      power: root.querySelector(".power"),
      alarm: root.querySelector(".notice.alarm"),
      warning: root.querySelector(".notice.warning"),
      frost: root.querySelector(".notice.frost"),
      streams: root.querySelector(".streams"),
      filter: root.querySelector(".notice.filter"),
      unit: root.querySelector(".unit"),
      eff: root.querySelector(".eff"),
      setpoint: root.querySelector(".setpoint"),
      effLabel: root.querySelector(".effLabel"),
      speeds: root.querySelector(".speeds"),
      bypassControl: root.querySelector(".bypassctl"),
      manual: root.querySelector(".manual"),
      facts: root.querySelector(".facts"),
      brand: root.querySelector(".brand a"),
    };

    this._el.power.addEventListener("click", () => this._togglePower());
    this._el.speeds.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-mode]");
      if (button) this._setSpeed(button.dataset.mode);
    });
    const slider = this._el.manual.querySelector("input");
    slider.addEventListener("input", () => {
      this._el.manual.querySelector("output").textContent = `${slider.value} %`;
    });
    slider.addEventListener("change", () => this._setManualSpeed(Number(slider.value)));
    this._el.bypassControl.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-option]");
      if (button) this._setBypass(button.dataset.option);
    });
    root.addEventListener("click", (event) => {
      const target = event.target.closest("[data-more]");
      if (target) this._moreInfo(target.dataset.more);
    });
  }

  _text() {
    return TEXT[(this._hass.language || "en").startsWith("fr") ? "fr" : "en"];
  }

  /** Map each source to the entity id of the configured unit. */
  _resolve() {
    const hass = this._hass;
    const deviceId = this._config.device_id || devicesOf(hass)[0];
    const wanted = new Map(Object.entries(SOURCES).map(([key, source]) => [source, key]));
    const ids = {};
    for (const [entityId, entity] of Object.entries(hass.entities || {})) {
      if (entity.platform !== DOMAIN || entity.device_id !== deviceId) continue;
      const key = wanted.get(`${entityId.split(".")[0]}.${entity.translation_key}`);
      if (key) ids[key] = entityId;
    }
    return { deviceId, ids };
  }

  _update() {
    if (!this._hass || !this._config) return;
    if (!this.shadowRoot) this._build();

    const hass = this._hass;
    const text = this._text();
    const { deviceId, ids } = this._resolve();
    this._ids = ids;
    const state = (key) => (ids[key] ? hass.states[ids[key]] : undefined);
    const climate = state("climate");

    this._el.brand.title = text.brand;
    if (!climate) {
      this._el.body.hidden = true;
      this._el.empty.hidden = false;
      this._el.empty.textContent = text.noDevice;
      return;
    }
    this._el.body.hidden = false;
    this._el.empty.hidden = true;

    // Skip the DOM work when nothing the card shows has changed.
    const signature = JSON.stringify([
      hass.language,
      this._config.name,
      hass.devices?.[deviceId]?.name_by_user,
      Object.values(ids).map((id) => {
        const s = hass.states[id];
        const a = s?.attributes;
        return (
          s && [
            s.state,
            a.fan_mode,
            a.fan_modes,
            a.temperature,
            a.codes,
            a.exchanger,
            a.bypassed_air,
            a.status,
            a.temperature_difference,
            a.options,
            a.frost_protection,
            a.command,
          ]
        );
      }),
    ]);
    if (signature === this._signature) return;
    this._signature = signature;

    const device = hass.devices?.[deviceId] || {};
    const unavailable = climate.state === "unavailable";
    const on = !unavailable && climate.state !== "off";
    const is = (key) => state(key)?.state === "on";

    // --- header -------------------------------------------------------------
    this._el.name.textContent =
      this._config.name || device.name_by_user || device.name || climate.attributes.friendly_name;
    const fanMode = climate.attributes.fan_mode;
    let status;
    if (unavailable) status = text.unavailable;
    else if (!on) status = text.off;
    else {
      const manual = number(state("manualSpeed"));
      const parts = [
        fanMode === "manual"
          ? manual === null ? text.manual : text.manualAt(manual)
          : text.speed(fanMode),
      ];
      if (is("boost")) parts.push(text.boost);
      else if (is("timer")) parts.push(text.timer);
      else if (is("schedule")) parts.push(text.schedule);
      if (is("heating")) parts.push(text.heating);
      if (is("cooling")) parts.push(text.cooling);
      status = parts.join(", ");
    }
    this._el.status.textContent = status;
    this._el.power.setAttribute("aria-pressed", String(on));
    this._el.power.setAttribute("aria-label", on ? text.turnOff : text.turnOn);
    this._el.power.title = on ? text.turnOff : text.turnOn;
    this._el.power.disabled = unavailable;

    // --- notices ------------------------------------------------------------
    // Alarms stop the unit until reset; warnings clear by themselves. The
    // filter codes are left to the filter notice below.
    const alarmState = state("alarmState")?.state;
    let active = state("alarms")?.attributes.active;
    if (!active) {
      active = alarmState === "alarm" || alarmState === "warning" ? [{ type: alarmState }] : [];
    }
    active = active.filter((item) => !FILTER_CODES.has(item.code));
    if (this._config.bypass_control) {
      active = active.filter((item) => !MANUAL_BYPASS_CODES.has(item.code));
    }
    for (const [type, element, label] of [
      ["alarm", this._el.alarm, text.alarm],
      ["warning", this._el.warning, text.warning],
    ]) {
      const items = active.filter((item) => item.type === type);
      element.hidden = items.length === 0;
      element.querySelector("span").replaceChildren(
        ...items.map((item) => {
          const line = document.createElement("div");
          line.textContent = item.text || label;
          // A code the manual does not document is already shown as "Code 50".
          if (item.code !== undefined && item.text !== `Code ${item.code}`) {
            const code = document.createElement("small");
            code.textContent = ` ${text.code(item.code)}`;
            line.append(code);
          }
          return line;
        }),
      );
    }

    // Frost: when the exchanger is protected by the bypass (no preheater), a
    // bypass driven by hand leaves it unprotected. Said whatever the options,
    // once the outdoor air gets cold.
    const bypassStateObj = state("bypass");
    const bypassModeObj = state("bypassMode");
    const outdoorNow = number(state("outdoor"));
    const frostRisk =
      on &&
      bypassStateObj?.attributes.frost_protection === "bypass" &&
      bypassModeObj !== undefined &&
      ["open", "closed"].includes(bypassModeObj.state) &&
      (outdoorNow === null || outdoorNow < FROST_WARNING_BELOW);
    this._el.frost.hidden = !frostRisk;
    if (frostRisk) this._el.frost.querySelector("span").textContent = text.frostByBypass;

    const days = number(state("filterDays"));
    // Due when the unit says so, or when its countdown has run out.
    const filterDue = is("filterAlert") || (days !== null && days <= 0);
    const configured = Number(this._config.filter_reminder_days);
    const soonDays =
      this._config.filter_reminder_days == null || !Number.isFinite(configured)
        ? FILTER_SOON_DAYS
        : Math.min(Math.max(Math.round(configured), 0), FILTER_SOON_MAX);
    const filterSoon = !filterDue && days !== null && days <= soonDays;
    this._el.filter.hidden = !(filterDue || filterSoon);
    if (filterDue || filterSoon) {
      this._el.filter.querySelector("span").textContent =
        filterDue ? text.filtersDue : text.filtersSoon(days);
      // The shop link is opt-in: the reminder alone is shown unless the owner
      // of the dashboard turned "filter_link" on in the card options.
      const link = this._el.filter.querySelector("a");
      link.hidden = !this._config.filter_link;
      if (this._config.filter_link) {
        const page = FILTERS[device.model];
        link.textContent = text.orderFilters;
        link.href = `${SHOP}${page || ""}${UTM}`;
      } else {
        link.textContent = "";
        link.removeAttribute("href");
      }
    }

    // --- drawing ------------------------------------------------------------
    const temps = {};
    for (const key of ["outdoor", "supply", "extract", "exhaust"]) temps[key] = number(state(key));
    const known = Object.values(temps).filter((value) => value !== null);
    const low = Math.min(...known);
    const span = Math.max(...known) - low;
    const formatter = new Intl.NumberFormat(hass.locale?.language || hass.language, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    const root = this.shadowRoot;
    for (const [key, value] of Object.entries(temps)) {
      root.querySelector(`[data-temp="${key}"]`).textContent =
        value === null ? "–" : `${formatter.format(value)}°`;
      // Colour = where this temperature sits between the coldest and the
      // warmest of the four streams.
      const colour =
        !on || value === null ? IDLE : mix(span < 0.5 ? 0.5 : (value - low) / span);
      root.querySelector(`[data-stop="${key}"]`).setAttribute("stop-color", colour);
      root.querySelector(`[data-arrow="${key}"]`)?.setAttribute("fill", colour);
    }
    for (const node of root.querySelectorAll("[data-text]")) node.textContent = text[node.dataset.text];

    const fan = Math.max(number(state("supplyFan")) ?? 60, number(state("extractFan")) ?? 60);
    this._el.unit.classList.toggle("stopped", !on || fan <= 0);
    // 30 % → one dash step every 1.5 s, 100 % → every 0.45 s.
    this._el.unit.style.setProperty("--a21-period", `${(45 / Math.max(fan, 30)).toFixed(2)}s`);

    // Bypass: 0 closed, 100 open. With a rotary exchanger the same value is
    // how much the wheel is slowed down, and no air goes around anything.
    const bypassState = state("bypass");
    const bypass = number(bypassState);
    const rotary = bypassState?.attributes.exchanger === "rotary";
    const bypassedStream = bypassState?.attributes.bypassed_air === "extract" ? "stale" : "fresh";
    const around = on && !rotary && bypass !== null && bypass >= 50;
    for (const [name, paths] of Object.entries(STREAMS)) {
      const group = root.querySelector(`[data-stream="${name}"]`);
      const detour = around && name === bypassedStream;
      const d = detour ? paths.around : paths.through;
      group.querySelector(".stream").setAttribute("d", d);
      group.querySelector(".motion").setAttribute("d", d);
      group.querySelector(".gap").setAttribute("d", detour ? paths.gap : "");
      // The detour is drawn last, over the stream it crosses.
      if (detour) this._el.streams.append(group);
    }

    const efficiencyState = state("efficiency");
    const efficiency = number(efficiencyState);
    const diverted = on && efficiency === null && bypass > 0;
    // Heat is recovered but cannot be put into a figure: the heater, cooler
    // or preheater changes the supply temperature too, or indoor and outdoor
    // air are too close. Say that the exchanger works, never leave a blank.
    const why = on && efficiency === null && !diverted ? efficiencyState?.attributes.status : null;
    const unmeasured = {
      small_difference: [
        text.gapBelow(efficiencyState?.attributes.minimum_difference ?? 4),
        text.recoveryGap(formatter.format(efficiencyState?.attributes.temperature_difference ?? 0)),
      ],
      heating: [text.whyHeating, text.recoveryHeating],
      cooling: [text.whyCooling, text.recoveryCooling],
      preheating: [text.whyPreheating, text.recoveryPreheating],
    }[why];
    this._el.eff.classList.toggle("word", diverted || Boolean(unmeasured));
    if (on && efficiency !== null) {
      this._el.eff.textContent = `${Math.round(efficiency)} %`;
      this._el.effLabel.textContent = text.recovered;
    } else if (unmeasured) {
      this._el.eff.textContent = text.exchangerOn;
      this._el.effLabel.textContent = unmeasured[0];
    } else if (diverted && rotary) {
      this._el.eff.textContent = text.rotor;
      this._el.effLabel.textContent = bypass >= 100 ? text.rotorStopped : `${100 - bypass} %`;
    } else if (diverted) {
      this._el.eff.textContent = text.bypass;
      this._el.effLabel.textContent = bypass >= 100 ? text.bypassOpen : `${bypass} %`;
    } else {
      this._el.eff.textContent = "";
      this._el.effLabel.textContent = "";
    }
    this._el.unit.setAttribute(
      "aria-label",
      ["outdoor", "supply", "extract", "exhaust"]
        .map((key) => `${text[key]} ${root.querySelector(`[data-temp="${key}"]`).textContent}`)
        .join(", "),
    );

    // --- setpoint, above the exchanger ---------------------------------------
    const target = Number.parseFloat(climate.attributes.temperature);
    this._el.setpoint.replaceChildren();
    if (on && Number.isFinite(target)) {
      const label = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      label.textContent = `${text.setpoint} `;
      const value = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      value.setAttribute("class", "v");
      // The unit's setpoint is a whole number of degrees.
      const degrees = `${Math.round(target)} °C`;
      value.textContent = climate.state === "fan_only" ? `${degrees} · ${text.noSetpoint}` : degrees;
      this._el.setpoint.append(label, value);
    }

    // --- speeds -------------------------------------------------------------
    const modes = climate.attributes.fan_modes || [];
    this._el.speeds.setAttribute("aria-label", text.speeds);
    this._el.speeds.replaceChildren(
      ...modes.map((mode) => {
        const button = document.createElement("button");
        button.dataset.mode = mode;
        button.textContent = mode === "manual" ? text.manual : mode;
        button.title = mode === "manual" ? text.manual : text.speed(mode);
        button.setAttribute("aria-label", button.title);
        button.setAttribute("aria-pressed", String(on && mode === fanMode));
        button.disabled = unavailable;
        return button;
      }),
    );

    // --- manual speed: a slider while the manual speed is selected ----------
    const manualState = state("manualSpeed");
    const showManual = on && fanMode === "manual" && number(manualState) !== null;
    this._el.manual.hidden = !showManual;
    if (showManual) {
      const slider = this._el.manual.querySelector("input");
      const a = manualState.attributes;
      this._el.manual.querySelector("span").textContent = text.manualSlider;
      slider.min = a.min ?? 0;
      slider.max = a.max ?? 100;
      slider.step = a.step ?? 1;
      slider.setAttribute("aria-label", text.manualSlider);
      // Leave the thumb alone while the finger is on it.
      if (!slider.matches(":active")) slider.value = number(manualState);
      this._el.manual.querySelector("output").textContent = `${slider.value} %`;
      slider.disabled = unavailable;
    }

    // --- bypass control (opt-in) --------------------------------------------
    const bypassMode = state("bypassMode");
    const showBypass = Boolean(this._config.bypass_control) && Boolean(bypassMode) && !rotary;
    this._el.bypassControl.hidden = !showBypass;
    if (showBypass) {
      const labels = { auto: text.bypassAuto, open: text.bypassOpened, closed: text.bypassShut };
      const offered = bypassMode.attributes.options || [];
      const label = this._el.bypassControl.querySelector("span");
      label.textContent = text.bypass;
      this._el.bypassControl.setAttribute("aria-label", text.bypassControl);
      this._el.bypassControl.replaceChildren(
        label,
        ...["auto", "open", "closed"]
          .filter((option) => offered.includes(option))
          .map((option) => {
            const button = document.createElement("button");
            button.dataset.option = option;
            button.textContent = labels[option];
            button.setAttribute("aria-pressed", String(bypassMode.state === option));
            button.disabled = unavailable || bypassMode.state === "unavailable";
            return button;
          }),
      );
    }

    // --- facts --------------------------------------------------------------
    const facts = [];
    const fact = (key, label, value, cls) => facts.push({ key, label, value, cls });
    if (unmeasured) fact("efficiency", text.recovery, unmeasured[1]);
    const humidity = number(state("humidity"));
    if (humidity !== null) fact("humidity", text.humidity, `${Math.round(humidity)} %`);
    const co2 = number(state("co2"));
    if (co2 !== null) fact("co2", text.co2, `${Math.round(co2)} ppm`);
    const supplyFan = number(state("supplyFan"));
    const extractFan = number(state("extractFan"));
    if (supplyFan !== null && extractFan !== null) {
      fact(
        "supplyFan",
        text.fans,
        supplyFan === extractFan ? `${supplyFan} %` : `${supplyFan} / ${extractFan} %`,
      );
    }
    if (bypass !== null && rotary) {
      const wheel = bypass <= 0 ? text.rotorFull : bypass >= 100 ? text.rotorStopped : `${100 - bypass} %`;
      fact("bypass", text.rotorFact, wheel);
    } else if (bypass !== null) {
      // While a three-point actuator travels, the command runs ahead of the
      // position the controller reports: say so instead of "open".
      const command = Number(bypassState?.attributes.command);
      let damper = bypass <= 0 ? text.bypassClosed : bypass >= 100 ? text.bypassOpen : `${bypass} %`;
      if (Number.isFinite(command) && command !== bypass) {
        damper = command > bypass ? text.bypassOpening(bypass) : text.bypassClosing(bypass);
      }
      fact("bypass", text.bypass, damper);
    }
    if (days !== null) fact("filterDays", text.filters, text.days(days), filterDue || filterSoon ? "due" : "");
    this._el.facts.replaceChildren(
      ...facts.map(({ key, label, value, cls }) => {
        const button = document.createElement("button");
        button.dataset.more = key;
        if (cls) button.className = cls;
        const strong = document.createElement("b");
        strong.textContent = value;
        button.append(`${label} `, strong);
        return button;
      }),
    );
  }

  _togglePower() {
    const entityId = this._ids?.climate;
    if (!entityId) return;
    const on = this._hass.states[entityId].state !== "off";
    this._hass.callService("climate", on ? "turn_off" : "turn_on", { entity_id: entityId });
  }

  _setSpeed(mode) {
    const entityId = this._ids?.climate;
    if (!entityId) return;
    const climate = this._hass.states[entityId];
    // Picking a speed on a stopped unit starts it: that is what the tap means.
    if (climate.state === "off") {
      this._hass.callService("climate", "turn_on", { entity_id: entityId });
    }
    this._hass.callService("climate", "set_fan_mode", { entity_id: entityId, fan_mode: mode });
  }

  _setManualSpeed(value) {
    const entityId = this._ids?.manualSpeed;
    if (!entityId) return;
    this._hass.callService("number", "set_value", { entity_id: entityId, value });
  }

  _setBypass(option) {
    const entityId = this._ids?.bypassMode;
    if (!entityId) return;
    this._hass.callService("select", "select_option", { entity_id: entityId, option });
  }

  _moreInfo(key) {
    const entityId = this._ids?.[key];
    if (!entityId) return;
    this.dispatchEvent(
      new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }),
    );
  }
}

// ---------------------------------------------------------------------------
// Details card
// ---------------------------------------------------------------------------

const DETAILS_STYLE = `
  :host { --a21-green: #52ae32; display: block; }
  ha-card { display: block; padding: 16px 16px 10px; overflow: hidden; }
  /* In the card picker, each preview is centred in a row as tall as the
     tallest card: a full-length details card would push the other preview
     out of sight. Keep the preview short there. */
  :host([in-picker]) ha-card { max-height: 360px; position: relative; }
  :host([in-picker]) ha-card::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 90px;
    background: linear-gradient(to bottom, transparent, var(--card-background-color, #fff)); pointer-events: none; }
  a:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; border-radius: 4px; }

  .head { display: flex; align-items: baseline; gap: 12px; margin-bottom: 14px; }
  .name { flex: 1; min-width: 0; font-size: 1.25rem; font-weight: 500; line-height: 1.3; color: var(--primary-text-color);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .status { flex: none; font-size: .875rem; color: var(--secondary-text-color); }
  .status::before { content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 7px; border-radius: 50%;
                    background: var(--a21-dot, var(--disabled-text-color, #9e9e9e)); }
  .status.on { --a21-dot: var(--a21-green); }
  .status.warning { --a21-dot: var(--warning-color, #ffa600); }
  .status.alarm { --a21-dot: var(--error-color, #db4437); }

  /* Sections flow in as many columns as the card is wide. */
  .sections { columns: 250px; column-gap: 32px; }
  section { break-inside: avoid; margin: 0 0 18px; }
  h3 { margin: 0 0 6px; padding-bottom: 5px; font-size: .8125rem; font-weight: 500; letter-spacing: .01em;
       color: var(--secondary-text-color); border-bottom: 1px solid var(--divider-color); }

  .row, .cols { display: grid; gap: 2px 12px; align-items: baseline; padding: 3px 0; font-size: .875rem; line-height: 1.45; }
  .row { grid-template-columns: minmax(34%, auto) minmax(0, 1fr); }
  .cols { grid-template-columns: minmax(0, 1fr) repeat(2, minmax(64px, auto)); }
  .label { color: var(--secondary-text-color); }
  .label small { display: block; font-size: .75rem; opacity: .85; }
  .value { color: var(--primary-text-color); font-weight: 500; text-align: right; font-variant-numeric: tabular-nums; }
  .cols.heading .value { font-weight: 400; font-size: .75rem; color: var(--secondary-text-color); }
  .value.dot::before { content: ""; display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%;
                       background: var(--a21-dot); vertical-align: 1px; }
  .on { --a21-dot: var(--a21-green); }
  .warning { --a21-dot: var(--warning-color, #ffa600); }
  .alarm { --a21-dot: var(--error-color, #db4437); }

  /* An alarm reads as a sentence, its code after it. */
  .event { display: flex; gap: 9px; align-items: baseline; padding: 4px 0; font-size: .875rem; line-height: 1.4;
           color: var(--primary-text-color); }
  .event::before { content: ""; flex: none; width: 8px; height: 8px; border-radius: 50%; background: var(--a21-dot);
                   transform: translateY(-1px); }
  .event small { margin-left: 6px; font-size: .75rem; color: var(--secondary-text-color); white-space: nowrap; }

  .absent { margin: 6px 0 0; font-size: .75rem; line-height: 1.5; color: var(--secondary-text-color); }
  .absent a { color: inherit; text-underline-offset: 2px; }
  .absent a:hover { color: var(--a21-green); }

  .brand { display: flex; justify-content: flex-end; margin-top: 2px; }
  .brand a { display: inline-flex; align-items: center; gap: 6px; font-size: .6875rem; letter-spacing: .04em;
             text-decoration: none; color: var(--secondary-text-color); opacity: .6; transition: opacity .15s, color .15s; }
  .brand svg { width: 11px; height: 12px; fill: currentColor; }
  .brand a:hover, .brand a:focus-visible { opacity: 1; color: var(--a21-green); }

  .empty { color: var(--secondary-text-color); font-size: .875rem; line-height: 1.5; margin-bottom: 8px; }
  [hidden] { display: none !important; }
`;

const DETAILS_TEMPLATE = `
  <ha-card>
    <div class="head">
      <div class="name"></div>
      <div class="status"></div>
    </div>
    <div class="sections"></div>
    <div class="empty" hidden></div>
    <div class="brand">
      <a target="_blank" rel="noopener" href="${SHOP}${UTM}">
        <svg viewBox="0 0 51.54 57.64" aria-hidden="true">
          <rect x=".84" y="44.97" width="49.79" height="11.67"/>
          <polygon points="50.64 7.03 50.64 18.6 28.51 13.06 12.46 16.15 12.46 24.04 .84 24.04 .84 7.03 28.57 1.48 50.64 7.03"/>
          <polygon points=".84 26.02 50.63 26.02 50.63 37.69 12.46 37.69 12.46 42.98 .84 42.98 .84 26.02"/>
        </svg>
        econology.fr
      </a>
    </div>
  </ha-card>
`;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/**
 * Every value the controller reports, grouped by subject.
 *
 * The integration sends the content, already worded and filtered: a value is
 * only listed when the unit has the matching hardware. This card just lays
 * it out, and follows the unit through a WebSocket subscription.
 */
/** True when the element sits inside the dashboard's "add card" picker. */
function inCardPicker(element) {
  let node = element;
  for (let depth = 0; node && depth < 40; depth += 1) {
    if (node.tagName === "HUI-CARD-PICKER") return true;
    node = node.parentElement || (node.getRootNode && node.getRootNode().host) || null;
  }
  return false;
}

class VentsA21DetailsCard extends HTMLElement {
  static getStubConfig(hass) {
    return { device_id: devicesOf(hass)[0] || "" };
  }

  static getConfigForm() {
    return configForm();
  }

  setConfig(config) {
    this._config = config || {};
    this._subscribe();
  }

  set hass(hass) {
    this._hass = hass;
    this._subscribe();
  }

  connectedCallback() {
    this.toggleAttribute("in-picker", inCardPicker(this));
    this._subscribe();
  }

  disconnectedCallback() {
    this._unsubscribe();
  }

  getCardSize() {
    return 10;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, min_rows: 6 };
  }

  _text() {
    return TEXT[(this._hass?.language || "en").startsWith("fr") ? "fr" : "en"];
  }

  _build() {
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${DETAILS_STYLE}</style>${DETAILS_TEMPLATE}`;
    const root = this.shadowRoot;
    this._el = {
      name: root.querySelector(".name"),
      status: root.querySelector(".status"),
      sections: root.querySelector(".sections"),
      empty: root.querySelector(".empty"),
      brand: root.querySelector(".brand a"),
    };
  }

  /** Follow the configured unit; subscribe again when unit or language change. */
  _subscribe() {
    if (!this._hass || !this._config || !this.isConnected) return;
    if (!this.shadowRoot) this._build();
    this._el.brand.title = this._text().brand;

    const deviceId = this._config.device_id || null;
    const key = `${deviceId}|${this._hass.language}`;
    if (this._subscription && key === this._key) return;
    this._unsubscribe();
    this._key = key;
    const subscription = this._hass.connection.subscribeMessage(
      (event) => {
        if (this._subscription !== subscription) return;
        if (event.reload) {
          // The unit is being reloaded: wait for it to come back.
          this._unsubscribe();
          this._retry(3000);
        } else {
          this._render(event);
        }
      },
      { type: `${DOMAIN}/subscribe_details`, device_id: deviceId, language: this._hass.language },
    );
    this._subscription = subscription;
    subscription.catch(() => {
      if (this._subscription !== subscription) return;
      // No unit yet (integration not set up, or still starting).
      this._subscription = null;
      this._render(null);
      this._retry(10000);
    });
  }

  _retry(delay) {
    clearTimeout(this._timer);
    this._timer = setTimeout(() => this._subscribe(), delay);
  }

  _unsubscribe() {
    clearTimeout(this._timer);
    const subscription = this._subscription;
    this._subscription = null;
    if (subscription) subscription.then((stop) => stop()).catch(() => {});
  }

  _render(payload) {
    const text = this._text();
    const { name, status, sections, empty } = this._el;
    if (!payload) {
      name.textContent = this._config.name || "";
      status.hidden = true;
      sections.replaceChildren();
      empty.hidden = false;
      empty.textContent = text.noDevice;
      return;
    }
    empty.hidden = true;
    status.hidden = false;
    name.textContent = this._config.name || payload.name;

    let label = text.unavailable;
    let level = "";
    if (payload.available) {
      label = payload.on ? text.running : text.off;
      level = payload.level || (payload.on ? "on" : "");
      if (payload.level === "alarm") label += `, ${text.withAlarm}`;
      else if (payload.level === "warning") label += `, ${text.withWarning}`;
    }
    status.textContent = label;
    status.className = `status ${level}`;

    sections.replaceChildren(...payload.sections.map((section) => this._section(section)));
  }

  _section(section) {
    const node = element("section");
    node.append(element("h3", "", section.title));

    if (section.key === "alarms") {
      for (const row of section.rows) {
        const line = element("div", `event ${row.level || ""}`, row.value);
        // A code the manual does not document is already shown as "Code 50".
        if (row.value !== `Code ${row.label}`) {
          line.append(element("small", "", this._text().code(row.label)));
        }
        node.append(line);
      }
      return node;
    }

    if (section.columns) {
      const heading = element("div", "cols heading");
      heading.append(element("span"), ...section.columns.map((column) => element("span", "value", column)));
      node.append(heading);
    }
    for (const row of section.rows) {
      const line = element("div", section.columns ? "cols" : "row");
      const label = element("span", "label", row.label);
      if (row.hint) label.append(element("small", "", row.hint));
      line.append(label);
      if (row.values) {
        line.append(...row.values.map((value) => element("span", "value", value)));
      } else {
        line.append(element("span", `value ${row.level ? `dot ${row.level}` : ""}`, row.value));
      }
      node.append(line);
    }

    if (section.absent?.length) {
      const colon = this._hass.language.startsWith("fr") ? " : " : ": ";
      const note = element("p", "absent", `${section.absent_label}${colon}`);
      section.absent.forEach((item, index) => {
        if (index) note.append(", ");
        if (item.url) {
          const link = element("a", "", item.label);
          link.href = item.url;
          link.target = "_blank";
          link.rel = "noopener";
          note.append(link);
        } else {
          note.append(item.label);
        }
      });
      node.append(note);
    }
    return node;
  }
}

// Home Assistant swaps window.customElements for a scoped registry while it
// starts. This file is loaded before that happens (it is an "extra module"
// of the integration, not a dashboard resource), and an element defined on
// the old registry is invisible to dashboards: the cards would show
// "configuration error" on most page loads. So define them only once the
// application element exists, which is after the swap.
const CARDS = [
  [CARD, VentsA21Card, "cardName", "cardDescription"],
  [DETAILS_CARD, VentsA21DetailsCard, "detailsName", "detailsDescription"],
];

function register() {
  for (const [tag, cls] of CARDS) {
    if (!window.customElements.get(tag)) window.customElements.define(tag, cls);
  }
}

Promise.race([
  customElements.whenDefined("home-assistant"),
  new Promise((resolve) => setTimeout(resolve, 10000)),
]).then(register);

{
  // The card picker is filled before any hass object exists: use the language
  // chosen in the Home Assistant profile (kept by the frontend in local
  // storage), then the browser's. The other language's name is appended to
  // the description so a search in either language finds the cards.
  let chosen = "";
  try {
    chosen = JSON.parse(localStorage.getItem("selectedLanguage") || '""') || "";
  } catch {
    chosen = "";
  }
  const lang = String(chosen || navigator.language || "").startsWith("fr") ? "fr" : "en";
  const text = TEXT[lang];
  const other = TEXT[lang === "fr" ? "en" : "fr"];
  window.customCards = window.customCards || [];
  for (const [tag, , name, description] of CARDS) {
    if (window.customCards.some((card) => card.type === tag)) continue;
    window.customCards.push({
      type: tag,
      name: text[name],
      description: `${text[description]} (${other[name]})`,
      preview: true,
      documentationURL: "https://github.com/floecono/ha-vents-A21",
    });
  }
}
