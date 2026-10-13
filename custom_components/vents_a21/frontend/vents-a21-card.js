/*
 * vents-a21-card — dashboard card for heat recovery ventilation units with
 * the A21 controller (ECONOPRIME Connect range, VENTS A21).
 *
 * Shipped with the vents_a21 integration, which loads it in every dashboard:
 * there is no resource to declare. Plain JavaScript, no build step.
 *
 * The four air streams are coloured from their measured temperature, so the
 * drawing shows what the heat exchanger is doing right now.
 */

const DOMAIN = "vents_a21";
const CARD = "vents-a21-card";
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

// Days before the filter deadline from which ordering is suggested.
const FILTER_SOON_DAYS = 21;

const TEXT = {
  fr: {
    outdoor: "Air neuf",
    supply: "Air soufflé",
    extract: "Air extrait",
    exhaust: "Air rejeté",
    outside: "Extérieur",
    inside: "Intérieur",
    recovered: "récupérés",
    bypass: "Bypass",
    bypassOpen: "ouvert",
    off: "À l'arrêt",
    unavailable: "Machine injoignable",
    speed: (n) => `Vitesse ${n}`,
    manual: "Manuelle",
    manualAt: (p) => `Vitesse manuelle ${p} %`,
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
    filtersSoon: (n) => `Filtres à remplacer dans ${n} jours`,
    orderFilters: "Commander les filtres",
    alarm: "Alarme",
    warning: "Avertissement",
    codes: (c) => (c.length > 1 ? `codes ${c.join(", ")}` : `code ${c[0]}`),
    brand: "Filtres et accessoires sur econology.fr",
    noDevice: "Aucune machine trouvée. Ajoutez d'abord l'intégration dans Paramètres, Appareils et services.",
    pickDevice: "Machine",
    name: "Nom affiché (facultatif)",
    cardName: "VMC double flux ECONOPRIME / VENTS A21",
    cardDescription: "Vue de la machine : températures des quatre flux d'air, rendement, vitesses, filtres.",
  },
  en: {
    outdoor: "Outdoor air",
    supply: "Supply air",
    extract: "Extract air",
    exhaust: "Exhaust air",
    outside: "Outside",
    inside: "Inside",
    recovered: "recovered",
    bypass: "Bypass",
    bypassOpen: "open",
    off: "Off",
    unavailable: "Unit unreachable",
    speed: (n) => `Speed ${n}`,
    manual: "Manual",
    manualAt: (p) => `Manual speed ${p} %`,
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
    filtersSoon: (n) => `Filters need replacing in ${n} days`,
    orderFilters: "Order filters",
    alarm: "Alarm",
    warning: "Warning",
    codes: (c) => (c.length > 1 ? `codes ${c.join(", ")}` : `code ${c[0]}`),
    brand: "Filters and accessories on econology.fr",
    noDevice: "No unit found. Add the integration first in Settings, Devices & services.",
    pickDevice: "Unit",
    name: "Displayed name (optional)",
    cardName: "ECONOPRIME / VENTS A21 ventilation unit",
    cardDescription: "View of the unit: temperature of the four air streams, efficiency, speeds, filters.",
  },
};

const COLD = [47, 134, 214];
const WARM = [240, 138, 36];
const IDLE = "var(--disabled-text-color, #9e9e9e)";

const STYLE = `
  :host { --a21-green: #52ae32; display: block; }
  ha-card { padding: 16px 16px 10px; overflow: hidden; }
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

  .notice { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; margin-top: 12px;
            padding: 10px 12px; border-radius: 10px; font-size: .875rem; line-height: 1.35;
            color: var(--primary-text-color); background: color-mix(in srgb, var(--a21-tone) 14%, transparent); }
  .notice::before { content: ""; flex: none; width: 8px; height: 8px; border-radius: 50%; background: var(--a21-tone); }
  .notice span { flex: 1; min-width: 12ch; }
  .notice a { color: var(--primary-text-color); font-weight: 500; text-underline-offset: 3px; }
  .notice.alarm { --a21-tone: var(--error-color, #db4437); }
  .notice.filter { --a21-tone: var(--warning-color, #ffa600); }

  .unit { display: block; width: 100%; height: auto; margin: 14px 0 6px; }
  .unit text { fill: var(--primary-text-color); font-family: inherit; }
  .unit .side { fill: var(--secondary-text-color); font-size: 11px; }
  .unit .label { fill: var(--secondary-text-color); font-size: 12px; }
  .unit .temp { font-size: 24px; font-weight: 500; font-variant-numeric: tabular-nums; }
  .unit .casing { fill: var(--secondary-background-color, rgba(127,127,127,.12)); stroke: var(--divider-color); }
  .unit .core { fill: var(--card-background-color, #fff); stroke: var(--divider-color); stroke-width: 1.5; }
  .unit .eff { font-size: 19px; font-weight: 500; text-anchor: middle; font-variant-numeric: tabular-nums; }
  .unit .eff.word { font-size: 14px; }
  .unit .effLabel { font-size: 10px; text-anchor: middle; fill: var(--secondary-text-color); }
  .unit .stream { fill: none; stroke-width: 9; stroke-linecap: round; stroke-linejoin: round; }
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

  .facts { display: flex; flex-wrap: wrap; gap: 4px 18px; margin-top: 12px; }
  .facts button { font-size: .875rem; line-height: 1.6; color: var(--secondary-text-color); }
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

// Streams: [id, path, gradient from → to]. The two paths cross inside the
// exchanger, where each one changes temperature.
const STREAMS = {
  fresh: "M12 62 H150 L250 138 H380",
  stale: "M388 62 H250 L150 138 H20",
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

        <rect class="casing" x="128" y="24" width="144" height="152" rx="16"/>
        <text class="side" x="12" y="104" data-text="outside"></text>
        <text class="side" x="388" y="104" text-anchor="end" data-text="inside"></text>

        <path class="stream" d="${STREAMS.stale}" stroke="url(#g-stale)"/>
        <path class="stream" d="${STREAMS.fresh}" stroke="url(#g-fresh)"/>
        <path class="motion" d="${STREAMS.stale}"/>
        <path class="motion" d="${STREAMS.fresh}"/>
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
      </svg>

      <div class="speeds" role="group"></div>
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

class VentsA21Card extends HTMLElement {
  static getStubConfig(hass) {
    return { device_id: devicesOf(hass)[0] || "" };
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "device_id", required: true, selector: { device: { integration: DOMAIN } } },
        { name: "name", selector: { text: {} } },
      ],
      computeLabel: (field, hass) => {
        const text = TEXT[(hass?.language || "en").startsWith("fr") ? "fr" : "en"];
        return field.name === "device_id" ? text.pickDevice : text.name;
      },
    };
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
      filter: root.querySelector(".notice.filter"),
      unit: root.querySelector(".unit"),
      eff: root.querySelector(".eff"),
      effLabel: root.querySelector(".effLabel"),
      speeds: root.querySelector(".speeds"),
      facts: root.querySelector(".facts"),
      brand: root.querySelector(".brand a"),
    };

    this._el.power.addEventListener("click", () => this._togglePower());
    this._el.speeds.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-mode]");
      if (button) this._setSpeed(button.dataset.mode);
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
        return s && [s.state, s.attributes.fan_mode, s.attributes.fan_modes, s.attributes.codes];
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
    const alarmState = state("alarmState")?.state;
    const hasAlarm = alarmState === "alarm" || alarmState === "warning";
    this._el.alarm.hidden = !hasAlarm;
    if (hasAlarm) {
      const codes = state("alarms")?.attributes.codes || [];
      const label = alarmState === "alarm" ? text.alarm : text.warning;
      this._el.alarm.querySelector("span").textContent =
        codes.length ? `${label}, ${text.codes(codes)}` : label;
    }

    const days = number(state("filterDays"));
    const filterDue = is("filterAlert");
    const filterSoon = !filterDue && days !== null && days <= FILTER_SOON_DAYS;
    this._el.filter.hidden = !(filterDue || filterSoon);
    if (filterDue || filterSoon) {
      this._el.filter.querySelector("span").textContent =
        filterDue ? text.filtersDue : text.filtersSoon(days);
      const link = this._el.filter.querySelector("a");
      const page = FILTERS[device.model];
      link.textContent = text.orderFilters;
      link.href = `${SHOP}${page || ""}${UTM}`;
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

    const efficiency = number(state("efficiency"));
    const bypass = number(state("bypass"));
    const bypassed = on && efficiency === null && bypass > 0;
    this._el.eff.classList.toggle("word", bypassed);
    if (on && efficiency !== null) {
      this._el.eff.textContent = `${Math.round(efficiency)} %`;
      this._el.effLabel.textContent = text.recovered;
    } else {
      this._el.eff.textContent = bypassed ? text.bypass : "";
      this._el.effLabel.textContent = bypassed ? text.bypassOpen : "";
    }
    this._el.unit.setAttribute(
      "aria-label",
      ["outdoor", "supply", "extract", "exhaust"]
        .map((key) => `${text[key]} ${root.querySelector(`[data-temp="${key}"]`).textContent}`)
        .join(", "),
    );

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

    // --- facts --------------------------------------------------------------
    const facts = [];
    const fact = (key, label, value, cls) => facts.push({ key, label, value, cls });
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

  _moreInfo(key) {
    const entityId = this._ids?.[key];
    if (!entityId) return;
    this.dispatchEvent(
      new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }),
    );
  }
}

// Home Assistant swaps window.customElements for a scoped registry while it
// starts. This file is loaded before that happens (it is an "extra module"
// of the integration, not a dashboard resource), and an element defined on
// the old registry is invisible to dashboards: the card would show
// "configuration error" on most page loads. So define the card only once the
// application element exists, which is after the swap.
function register() {
  if (!window.customElements.get(CARD)) window.customElements.define(CARD, VentsA21Card);
}

Promise.race([
  customElements.whenDefined("home-assistant"),
  new Promise((resolve) => setTimeout(resolve, 10000)),
]).then(register);

if (!(window.customCards || []).some((card) => card.type === CARD)) {
  const french = (navigator.language || "").startsWith("fr");
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: CARD,
    name: TEXT[french ? "fr" : "en"].cardName,
    description: TEXT[french ? "fr" : "en"].cardDescription,
    preview: true,
    documentationURL: "https://github.com/floecono/ha-vents-A21",
  });
}
