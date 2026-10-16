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
const CARD_EDITOR = "vents-a21-card-editor";
const UTM = "?utm_source=home-assistant&utm_medium=card&utm_campaign=vents_a21";
const SHOP = "https://www.econology.fr/";

// Where "order filters" puts the chosen filters in the shop's cart (POST
// only; the shop then opens the cart). The reference tells the shop the
// cart came from Home Assistant, from which model, and from which unit:
// the identifier of its Wi-Fi module (the number the app shows) when the
// integration could ask for it, else the identifier Home Assistant gave
// the unit when it was added.
const CART = `${SHOP}veqai/cart`;
const CART_REF = "home_assistant";

// Replacement filters per model: the shop page that presents them, and
// (class, shop SKU) of each one. Keep in sync with MODELS in const.py
// (tests/test_frontend.py checks it).
const FILTERS = {
  "Zephyr 240 S Connect": {
    page: "filtre-f7-vmc-double-flux-zephyr-240-fzeph240f7-econoprime.html",
    items: [["G4", "REF128848"], ["F7", "REF128847"]],
  },
  "Zephyr 270 V Connect R": {
    page: "filtre-f7-zephyr-270-12300001-econoprime.html",
    items: [["G4", "REF135207"], ["F7", "REF135206"]],
  },
  "Zephyr 550 V PH Connect R": {
    page: "filtres-panneau-596x164x60-econoprime-filtres-de-rechange-pour-centrale-double-flux-596-x-164-x-60-mm.html",
    items: [["G4", "REF142162"], ["F7", "REF142163"]],
  },
  "DF 180 Flat Connect": {
    page: "filtre-vmc-double-flux-df-180-econoprime.html",
    items: [["G4", "REF102165"], ["F7", "REF102166"]],
  },
  "DF 270 Connect": {
    page: "filtre-vmc-double-flux-df-270-econoprime.html",
    items: [["G4", "REF102170"], ["F8", "REF102171"]],
  },
  "DF 350 Connect": {
    page: "filtre-vmc-double-flux-df-350-econoprime.html",
    items: [["G4", "REF102185"], ["F7", "REF102186"]],
  },
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
    orderTitle: "Commander les filtres",
    orderWhich: "Quels filtres ajouter au panier econology.fr ?",
    orderHint: (changes, interval) =>
      `Proposé : un an de filtres, soit ${changes} changement${changes > 1 ? "s" : ""} (intervalle de ${interval} jours), moins ce qui est en stock.`,
    filterClass: { G4: "Filtre G4 – grossier, protège la machine", F7: "Filtre F7 – fin, air neuf", F8: "Filtre F8 – fin, air neuf" },
    addToCart: "Ajouter au panier",
    cancel: "Annuler",
    seeFilters: "Voir la fiche des filtres",
    inStock: (list) => `en stock : ${list}`,
    noSpares: "Plus de filtres de rechange en réserve",
    onOrder: (list) => `Commande en cours : ${list}`,
    received: "Reçus",
    alarm: "Alarme",
    warning: "Avertissement",
    brand: "Filtres et accessoires sur econology.fr",
    noDevice: "Aucune machine trouvée. Ajoutez d'abord l'intégration dans Paramètres, Appareils et services.",
    pickDevice: "Machine",
    name: "Nom affiché (facultatif)",
    filterLink: "Afficher le lien pour commander les filtres quand ils sont à remplacer",
    bypassOption: "Afficher la commande manuelle du bypass (automatique, ouvert, fermé)",
    unitSettings: "Réglages de la machine",
    unitSettingsHint: "Enregistrés dans la machine (page de l'appareil), partagés par toutes ses tuiles.",
    reminderDays: "Rappel des filtres : jours avant l'échéance (0 : à l'échéance seulement)",
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
    orderTitle: "Order filters",
    orderWhich: "Which filters go into the econology.fr cart?",
    orderHint: (changes, interval) =>
      `Suggested: a year of filters, ${changes} change${changes > 1 ? "s" : ""} (${interval}-day interval), less what is in stock.`,
    filterClass: { G4: "G4 filter – coarse, protects the unit", F7: "F7 filter – fine, fresh air", F8: "F8 filter – fine, fresh air" },
    addToCart: "Add to cart",
    cancel: "Cancel",
    seeFilters: "See the filters page",
    inStock: (list) => `in stock: ${list}`,
    noSpares: "No spare filters left",
    onOrder: (list) => `On order: ${list}`,
    received: "Received",
    alarm: "Alarm",
    warning: "Warning",
    brand: "Filters and accessories on econology.fr",
    noDevice: "No unit found. Add the integration first in Settings, Devices & services.",
    pickDevice: "Unit",
    name: "Displayed name (optional)",
    filterLink: "Show the link to order filters when they need replacing",
    bypassOption: "Show the manual bypass control (automatic, open, closed)",
    unitSettings: "Unit settings",
    unitSettingsHint: "Stored in the unit (device page) and shared by all of its cards.",
    reminderDays: "Filter reminder: days before the deadline (0: only at the deadline)",
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
  .notice a, .notice button.order { color: var(--primary-text-color); font-weight: 500; text-underline-offset: 3px; }
  .notice button.order, .notice button.received { background: none; border: 0; padding: 0; font: inherit; font-weight: 500;
                  color: var(--primary-text-color); text-decoration: underline; text-underline-offset: 3px; cursor: pointer; }
  .notice span small { display: block; font-size: .8125rem; color: var(--secondary-text-color); white-space: normal; }
  dialog.cart { border: 0; border-radius: 12px; padding: 20px 22px; max-width: 340px; width: calc(100% - 32px);
                color: var(--primary-text-color); background: var(--card-background-color, #fff);
                box-shadow: 0 8px 32px rgba(0,0,0,.3); }
  dialog.cart::backdrop { background: rgba(0,0,0,.35); }
  dialog.cart h3 { margin: 0 0 6px; font-size: 1.125rem; font-weight: 500; }
  dialog.cart p { margin: 0 0 12px; color: var(--secondary-text-color); font-size: .9375rem; }
  dialog.cart label { display: flex; align-items: center; gap: 10px; padding: 8px 0; cursor: pointer; }
  dialog.cart label span { flex: 1; }
  dialog.cart .qty { display: inline-flex; flex: none; align-items: center; border: 1px solid var(--divider-color, #ccc); border-radius: 8px; }
  dialog.cart .qty button { width: 30px; height: 30px; border: 0; background: none; color: var(--primary-text-color); font: inherit; font-size: 1.125rem; cursor: pointer; }
  dialog.cart .qty output { min-width: 2ch; text-align: center; font-variant-numeric: tabular-nums; }
  dialog.cart label:has(input:not(:checked)) .qty { opacity: .35; pointer-events: none; }
  dialog.cart .hint { margin: 6px 0 0; font-size: .8125rem; }
  dialog.cart input[type=checkbox] { width: 20px; height: 20px; accent-color: var(--a21-green); margin: 0; }
  dialog.cart .actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px; }
  dialog.cart .actions button { height: 40px; padding: 0 16px; border-radius: 10px; font: inherit; font-size: .9375rem; cursor: pointer;
                                border: 1px solid var(--divider-color, #ccc); background: none; color: var(--primary-text-color); }
  dialog.cart .actions .add { background: var(--a21-green); border-color: var(--a21-green); color: #fff; font-weight: 500; }
  dialog.cart .actions .add:disabled { opacity: .45; cursor: default; }
  dialog.cart a { display: inline-block; margin-top: 12px; font-size: .8125rem; color: var(--secondary-text-color); }
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
  .unit .core { fill: var(--card-background-color, #fff); fill-opacity: .82; stroke: var(--divider-color); stroke-width: 1.5; }
  .unit .eff { font-size: 19px; font-weight: 500; text-anchor: middle; font-variant-numeric: tabular-nums; }
  .unit .eff.word { font-size: 14px; }
  .unit .effLabel { font-size: 10px; text-anchor: middle; fill: var(--secondary-text-color); }
  .unit .stream { fill: none; stroke-width: 9; stroke-linecap: round; stroke-linejoin: round; }
  .unit .gap { fill: none; stroke: var(--secondary-background-color, #eee); stroke-width: 16; stroke-linejoin: round; }
  .unit .motion { fill: none; stroke: rgba(255,255,255,.75); stroke-width: 2.5; stroke-linecap: round;
                  stroke-dasharray: 1 17; animation: a21-flow .5625s linear infinite; }
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

// The two air streams, in four pieces each: the trunk in, the branch that
// crosses the exchanger (where the stream changes temperature), the branch
// that goes around it when the bypass is open, and the trunk out. The two
// branches share the junctions, so their widths can follow the position of
// the bypass damper: a damper at 40 % draws a thin stream around the
// exchanger and a thicker one through it.
// How long after a change of speed the card shows the target percentages
// rather than the measured ones (fans ramp, then the next poll reads them).
const FAN_SETTLE_MS = 60000;

const STREAM_RADIUS = 14; // of the rounded corners, in viewBox units

/** Path of a polyline whose corners are rounded with quadratic curves. */
function roundedPath(points, radius = STREAM_RADIUS) {
  const parts = [`M${points[0][0]} ${points[0][1]}`];
  for (let i = 1; i < points.length - 1; i++) {
    const [px, py] = points[i - 1];
    const [x, y] = points[i];
    const [nx, ny] = points[i + 1];
    const before = Math.hypot(x - px, y - py);
    const after = Math.hypot(nx - x, ny - y);
    const r = Math.min(radius, before / 2, after / 2);
    const a = [x + ((px - x) / before) * r, y + ((py - y) / before) * r];
    const b = [x + ((nx - x) / after) * r, y + ((ny - y) / after) * r];
    parts.push(`L${a[0].toFixed(1)} ${a[1].toFixed(1)}`, `Q${x} ${y} ${b[0].toFixed(1)} ${b[1].toFixed(1)}`);
  }
  const [lx, ly] = points[points.length - 1];
  parts.push(`L${lx} ${ly}`);
  return parts.join(" ");
}

// The exchanger branch dips from the trunk into the middle of an upper
// slanted face of the exchanger, crosses the block in a straight line
// through its centre, against the other stream (the core is slightly
// translucent, so this shows through), and leaves by the middle of the
// opposite lower face, as on the manufacturers' airflow diagrams; the detour leaves the
// end of the trunk and follows the outline of the core at a constant
// 14 units (its tip, then its lower faces, then up to the trunk). Both
// branches share the width of the stream.
const R = STREAM_RADIUS;
const STREAMS = {
  fresh: {
    in: "M12 62 H148",
    through: roundedPath([[148, 62], [159, 78], [241, 122], [250, 138]]),
    around: roundedPath([[148, 62], [127, 100], [167, 158], [233, 158], [250, 138], [250 + R, 138]]),
    out: "M250 138 H380",
  },
  stale: {
    in: "M388 62 H252",
    through: roundedPath([[252, 62], [241, 78], [159, 122], [150, 138]]),
    around: roundedPath([[252, 62], [273, 100], [233, 158], [167, 158], [150, 138], [150 - R, 138]]),
    out: "M150 138 H20",
  },
};
const STREAM_PIECES = ["through", "around", "in", "out"];
const STREAM_WIDTH = 9; // of a full stream, matching .unit .stream
const MOTION_WIDTH = 2.5;
const GAP_EXTRA = 7; // the mask under the detour is this much wider

function streamMarkup(name) {
  const paths = STREAMS[name];
  return `<g data-stream="${name}">
    <path class="gap" d="${paths.around}"/>
    ${STREAM_PIECES.map(
      (piece) =>
        `<path class="stream" data-piece="${piece}" d="${paths[piece]}" stroke="url(#g-${name}${piece === "through" ? "-x" : ""})"/>`,
    ).join("")}
    ${STREAM_PIECES.map((piece) => `<path class="motion" data-piece="${piece}" d="${paths[piece]}"/>`).join("")}
  </g>`;
}

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
      <div class="notice filter" hidden><span></span><button type="button" class="order" hidden></button><button type="button" class="received" hidden></button></div>
      <dialog class="cart">
        <form method="dialog">
          <h3></h3>
          <p></p>
          <div class="choices"></div>
          <p class="hint"></p>
          <div class="actions"><button type="button" class="cancel"></button><button type="submit" class="add"></button></div>
          <a target="_blank" rel="noopener"></a>
        </form>
      </dialog>

      <svg class="unit" viewBox="0 0 400 200" role="img">
        <defs>
          <linearGradient id="g-fresh" gradientUnits="userSpaceOnUse" x1="12" x2="388" y1="0" y2="0">
            <stop offset=".42" data-stop="outdoor"/><stop offset=".58" data-stop="supply"/>
          </linearGradient>
          <linearGradient id="g-stale" gradientUnits="userSpaceOnUse" x1="388" x2="12" y1="0" y2="0">
            <stop offset=".42" data-stop="extract"/><stop offset=".58" data-stop="exhaust"/>
          </linearGradient>
          <!-- The branch through the exchanger ends at the temperature the
               exchanger delivers, which differs from the measured outlet
               when part of the air went around it and was mixed back in. -->
          <linearGradient id="g-fresh-x" gradientUnits="userSpaceOnUse" x1="12" x2="388" y1="0" y2="0">
            <stop offset=".42" data-xstop="fresh-in"/><stop offset=".58" data-xstop="fresh-out"/>
          </linearGradient>
          <linearGradient id="g-stale-x" gradientUnits="userSpaceOnUse" x1="388" x2="12" y1="0" y2="0">
            <stop offset=".42" data-xstop="stale-in"/><stop offset=".58" data-xstop="stale-out"/>
          </linearGradient>
        </defs>

        <text class="setpoint" x="200" y="15"></text>
        <rect class="casing" x="112" y="24" width="176" height="152" rx="16"/>
        <text class="side" x="12" y="104" data-text="outside"></text>
        <text class="side" x="388" y="104" text-anchor="end" data-text="inside"></text>

        <g class="streams">
          ${streamMarkup("stale")}
          ${streamMarkup("fresh")}
        </g>
        <path class="head-arrow" data-arrow="supply" d="M378 127 L394 138 L378 149 Z"/>
        <path class="head-arrow" data-arrow="exhaust" d="M22 127 L6 138 L22 149 Z"/>

        <!-- A counter-flow plate exchanger: a hexagonal block lying on its
             side. Each stream enters through an upper slanted face, runs
             along the block against the other stream, and leaves through
             the opposite lower face. -->
        <path class="core" d="M144 100 L174 56 L226 56 L256 100 L226 144 L174 144 Z"/>
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
  stockCoarse: "number.filters_coarse_stock",
  stockFine: "number.filters_fine_stock",
  reminderDays: "number.filters_reminder_days",
  filterSupply: "select.filters_supply",
  filterInterval: "number.filter_interval",
};

function devicesOf(hass) {
  const ids = new Set();
  for (const entity of Object.values(hass.entities || {})) {
    if (entity.platform === DOMAIN && entity.device_id) ids.add(entity.device_id);
  }
  return [...ids];
}

/** True when the integration says what a replacement uses (stock entities present). */
function coarseOrFineKnown(spares) {
  return spares.perChange.some((n) => n > 0);
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
  bypass_control: "bypassOption",
};

/**
 * Language of the Home Assistant interface, for the places where no hass
 * object is available (card picker, visual editor): the language chosen in
 * the user's profile (kept by the frontend in local storage), then the
 * browser's.
 */
function uiLanguage() {
  let chosen = "";
  try {
    chosen = JSON.parse(localStorage.getItem("selectedLanguage") || '""') || "";
  } catch {
    chosen = "";
  }
  return String(chosen || navigator.language || "").startsWith("fr") ? "fr" : "en";
}

/** Options shown by the visual editor of both cards, plus their own extras. */
function configForm(extra = []) {
  return {
    schema: [
      { name: "device_id", required: true, selector: { device: { integration: DOMAIN } } },
      { name: "name", selector: { text: {} } },
      ...extra,
    ],
    // The editor passes (field, localize), not the hass object: the language
    // comes from the interface itself (profile setting, then the browser).
    computeLabel: (field) => TEXT[uiLanguage()][FORM_LABELS[field.name]],
  };
}

class VentsA21Card extends HTMLElement {
  static getStubConfig(hass) {
    return { device_id: devicesOf(hass)[0] || "" };
  }

  static getConfigForm() {
    return configForm([
      { name: "filter_link", selector: { boolean: {} } },
      { name: "bypass_control", selector: { boolean: {} } },
    ]);
  }

  // The editor is the form above plus the settings of the unit that a
  // dashboard owner expects to find here (see VentsA21CardEditor).
  static getConfigElement() {
    return document.createElement(CARD_EDITOR);
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
      cart: root.querySelector("dialog.cart"),
    };

    this._el.power.addEventListener("click", () => this._togglePower());
    this._el.filter.querySelector("button.order").addEventListener("click", () => this._openCart());
    this._el.filter.querySelector("button.received").addEventListener("click", () => this._filtersReceived());
    const cart = this._el.cart;
    cart.querySelector(".cancel").addEventListener("click", () => cart.close());
    cart.querySelector(".choices").addEventListener("change", () => {
      cart.querySelector(".add").disabled = !cart.querySelector("input:checked");
    });
    cart.querySelector(".choices").addEventListener("click", (event) => {
      const step = event.target.closest("button[data-step]");
      if (!step) return;
      event.preventDefault();
      const output = step.parentElement.querySelector("output");
      output.value = String(Math.min(99, Math.max(1, Number(output.value) + Number(step.dataset.step))));
    });
    cart.querySelector("form").addEventListener("submit", (event) => {
      event.preventDefault();
      this._orderFilters();
      cart.close();
    });
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
            a.fan_targets,
            a.ordered,
            a.per_change,
            a.tracking,
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
    const fans = this._fanPercentages(climate, on, fanMode, state);
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
    // The reminder lead time is a setting of the unit (number entity kept
    // with the spare-filter stock). The former card option is only read
    // when that entity is missing, i.e. with an older integration.
    const fromUnit = number(state("reminderDays"));
    const configured = Number(this._config.filter_reminder_days);
    const soonDays =
      fromUnit !== null
        ? Math.min(Math.max(Math.round(fromUnit), 0), FILTER_SOON_MAX)
        : this._config.filter_reminder_days == null || !Number.isFinite(configured)
          ? FILTER_SOON_DAYS
          : Math.min(Math.max(Math.round(configured), 0), FILTER_SOON_MAX);
    const filterSoon = !filterDue && days !== null && days <= soonDays;
    // Spare filters at home (kept by the integration): what is in stock,
    // what one replacement uses, what is on order.
    const spares = this._spares(state);
    this._filtersModel = device.model;
    const lowStock = spares.tracking && !spares.enough;
    const onOrder = spares.ordered.some((n) => n > 0);
    const showFilter = filterDue || filterSoon || onOrder || (lowStock && this._config.filter_link);
    this._el.filter.hidden = !showFilter;
    if (showFilter) {
      const span = this._el.filter.querySelector("span");
      const line = filterDue ? text.filtersDue : filterSoon ? text.filtersSoon(days) : lowStock ? text.noSpares : "";
      span.replaceChildren(line);
      const list = (counts) => spares.names.map((name, i) => `${counts[i]} ${name}`).filter((_, i) => counts[i] > 0).join(" + ");
      const details = [];
      if ((filterDue || filterSoon) && spares.tracking && spares.enough) details.push(text.inStock(list(spares.stock)));
      else if ((filterDue || filterSoon) && lowStock) details.push(text.noSpares);
      if (onOrder) details.push(text.onOrder(list(spares.ordered)));
      if (details.length) {
        const small = document.createElement("small");
        small.textContent = details.join(" · ");
        span.append(small);
      }
      // The shop link is opt-in: the reminder alone is shown unless the owner
      // of the dashboard turned "filter_link" on in the card options. With
      // enough spares at home there is nothing to order.
      const order = this._el.filter.querySelector("button.order");
      const showOrder = Boolean(this._config.filter_link) && !(spares.tracking && spares.enough) && !onOrder;
      order.hidden = !showOrder;
      order.textContent = showOrder ? text.orderFilters : "";
      const received = this._el.filter.querySelector("button.received");
      received.hidden = !onOrder;
      received.textContent = onOrder ? text.received : "";
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
    const colours = {};
    for (const [key, value] of Object.entries(temps)) {
      root.querySelector(`[data-temp="${key}"]`).textContent =
        value === null ? "–" : `${formatter.format(value)}°`;
      // Colour = where this temperature sits between the coldest and the
      // warmest of the four streams.
      const colour =
        !on || value === null ? IDLE : mix(span < 0.5 ? 0.5 : (value - low) / span);
      colours[key] = colour;
      root.querySelector(`[data-stop="${key}"]`).setAttribute("stop-color", colour);
      root.querySelector(`[data-arrow="${key}"]`)?.setAttribute("fill", colour);
    }
    // No exchange along the detour: it keeps the colour of the air that
    // enters it, up to the point where it joins the trunk again.
    root.querySelector('[data-stream="fresh"] .stream[data-piece="around"]').setAttribute("stroke", colours.outdoor);
    root.querySelector('[data-stream="stale"] .stream[data-piece="around"]').setAttribute("stroke", colours.extract);
    for (const node of root.querySelectorAll("[data-text]")) node.textContent = text[node.dataset.text];

    const anyFan = Math.max(fans.fresh ?? 0, fans.stale ?? 0);
    this._el.unit.classList.toggle("stopped", !on || anyFan <= 0);

    // Bypass: 0 closed, 100 open. With a rotary exchanger the same value is
    // how much the wheel is slowed down, and no air goes around anything.
    const bypassState = state("bypass");
    const bypass = number(bypassState);
    const rotary = bypassState?.attributes.exchanger === "rotary";
    const bypassedStream = bypassState?.attributes.bypassed_air === "extract" ? "stale" : "fresh";
    // Share of the bypassed stream drawn around the exchanger: the position
    // of the damper. The rest keeps crossing the exchanger.
    const share = on && !rotary && bypass !== null ? Math.min(Math.max(bypass, 0), 100) / 100 : 0;
    for (const name of Object.keys(STREAMS)) {
      const group = root.querySelector(`[data-stream="${name}"]`);
      const aroundShare = name === bypassedStream ? share : 0;
      const widths = { around: aroundShare, through: 1 - aroundShare };
      for (const piece of ["around", "through"]) {
        const shown = widths[piece] >= 0.05;
        for (const kind of ["stream", "motion"]) {
          const node = group.querySelector(`.${kind}[data-piece="${piece}"]`);
          node.toggleAttribute("hidden", !shown); // SVG elements have no .hidden
          node.style.strokeWidth = `${((kind === "stream" ? STREAM_WIDTH : MOTION_WIDTH) * widths[piece]).toFixed(2)}px`;
        }
      }
      const gap = group.querySelector(".gap");
      gap.toggleAttribute("hidden", widths.around < 0.05);
      gap.style.strokeWidth = `${(STREAM_WIDTH * widths.around + GAP_EXTRA).toFixed(2)}px`;
      // The detour is drawn last, over the stream it crosses.
      if (aroundShare > 0) this._el.streams.append(group);

      // Colour at the exit of the exchanger: the measured outlet is the mix
      // of what went through and what went around, so what went through
      // was further from the inlet than the outlet shows.
      const [inlet, outlet] = name === "fresh" ? ["outdoor", "supply"] : ["extract", "exhaust"];
      let exchanged = colours[outlet];
      if (aroundShare > 0 && aroundShare < 0.95 && temps[inlet] !== null && temps[outlet] !== null) {
        const value = (temps[outlet] - aroundShare * temps[inlet]) / (1 - aroundShare);
        const clamped = Math.min(Math.max(value, low), low + span);
        exchanged = mix(span < 0.5 ? 0.5 : (clamped - low) / span);
      }
      root.querySelector(`[data-xstop="${name}-in"]`).setAttribute("stop-color", colours[inlet]);
      root.querySelector(`[data-xstop="${name}-out"]`).setAttribute("stop-color", exchanged);
    }
    this._fanRates = {};
    for (const name of Object.keys(STREAMS)) {
      this._fanRates[name] = (fans[name] ?? fans[name === "fresh" ? "stale" : "fresh"] ?? 80) / 80;
    }
    this._paceDots();

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
    if (fans.fresh !== null && fans.stale !== null) {
      fact(
        "supplyFan",
        text.fans,
        fans.fresh === fans.stale ? `${fans.fresh} %` : `${fans.fresh} / ${fans.stale} %`,
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

  /**
   * Fan percentages to show: fresh (supply fan) and stale (extract fan).
   *
   * The measured values follow a change of speed only once the fans have
   * got there and the next poll has read them, so for a while after a tap
   * the card would look as if nothing happened. During that window the
   * percentages the chosen speed stands for are shown instead, until the
   * measurement agrees with them or a minute has passed.
   */
  _fanPercentages(climate, on, fanMode, state) {
    const measured = { fresh: number(state("supplyFan")), stale: number(state("extractFan")) };
    const targets = climate.attributes.fan_targets || {};
    const target = !on ? (climate.state === "off" ? [0, 0] : null) : targets[fanMode] || null;
    const key = `${climate.state}|${fanMode}|${target ? target.join("/") : ""}`;
    const now = Date.now();
    if (this._fanKey === undefined) {
      this._fanKey = key; // first render: trust the measurement
    } else if (key !== this._fanKey) {
      this._fanKey = key;
      this._fanChangedAt = now;
      clearTimeout(this._fanTimer);
      this._fanTimer = setTimeout(() => {
        this._signature = null; // the measurement takes over: redraw
        this._update();
      }, FAN_SETTLE_MS + 50);
    }
    const settling = target && this._fanChangedAt !== undefined && now - this._fanChangedAt < FAN_SETTLE_MS;
    if (!settling) return measured;
    const close = (a, b) => a !== null && Math.abs(a - b) <= 2;
    if (close(measured.fresh, target[0]) && close(measured.stale, target[1])) return measured;
    return { fresh: target[0], stale: target[1] };
  }

  /**
   * Make the dots travel at the speed of the fan that moves that air: the
   * fresh stream follows the supply fan, the stale one the extract fan.
   * The CSS period is the pace at 80 %; the playback rate scales it
   * linearly, so 40 % runs half as fast and a change of speed glides
   * rather than jumps. The card is first drawn before it is in the page,
   * when no animation exists yet, so this also runs once connected.
   */
  _paceDots() {
    const rates = this._fanRates;
    if (!rates || !this.shadowRoot || typeof Element.prototype.getAnimations !== "function") return;
    for (const [name, rate] of Object.entries(rates)) {
      const group = this.shadowRoot.querySelector(`[data-stream="${name}"]`);
      if (!group) continue;
      for (const node of group.querySelectorAll(".motion")) {
        for (const animation of node.getAnimations()) {
          if (animation.playbackRate === rate) continue;
          if (typeof animation.updatePlaybackRate === "function") animation.updatePlaybackRate(rate);
          else animation.playbackRate = rate;
        }
      }
    }
  }

  connectedCallback() {
    // Drawn before being put in the page: the animations exist only now.
    requestAnimationFrame(() => this._paceDots());
  }

  disconnectedCallback() {
    clearTimeout(this._fanTimer);
  }

  /** Ask which filters to order, both ticked, then put them in the cart. */
  /**
   * The spare filters of the unit, from the two stock numbers: coarse
   * (extract side) first, fine second. Without them (older integration),
   * nothing is tracked and the card behaves as before.
   */
  _spares(state) {
    const coarse = state("stockCoarse");
    const fine = state("stockFine");
    const entities = [coarse, fine];
    const stock = entities.map((e) => number(e) ?? 0);
    const perChange = entities.map((e) => Number(e?.attributes.per_change ?? 0));
    const names = entities.map((e, i) => e?.attributes.filter_class || ["G4", "F7"][i]);
    return {
      tracking: Boolean(coarse?.attributes.tracking),
      stock,
      perChange,
      names,
      ordered: entities.map((e) => Number(e?.attributes.ordered ?? 0)),
      enough: stock.every((n, i) => n >= perChange[i]),
      interval: number(state("filterInterval")),
    };
  }

  _openCart() {
    const text = this._text();
    const filters = FILTERS[this._filtersModel];
    const cart = this._el.cart;
    const link = cart.querySelector("a");
    link.textContent = text.seeFilters;
    link.href = `${SHOP}${filters?.page || ""}${UTM}`;
    if (!filters) {
      // Unknown model: the shop page is all the card can offer.
      window.open(link.href, "_blank", "noopener");
      return;
    }
    const ids = this._ids;
    const state = (key) => (ids[key] ? this._hass.states[ids[key]] : undefined);
    const spares = this._spares(state);
    // A year of filters, less what is already at home, is a sensible lot:
    // one delivery for the year. Each class defaults to what the supply
    // setting says a replacement uses.
    const interval = spares.interval && spares.interval > 0 ? spares.interval : 90;
    const changes = Math.max(1, Math.round(365 / interval));
    cart.querySelector("h3").textContent = text.orderTitle;
    cart.querySelector("p").textContent = text.orderWhich;
    cart.querySelector(".hint").textContent = text.orderHint(changes, interval);
    cart.querySelector(".cancel").textContent = text.cancel;
    cart.querySelector(".add").textContent = text.addToCart;
    cart.querySelector(".add").disabled = false;
    cart.querySelector(".choices").replaceChildren(
      ...filters.items.map(([cls, sku], i) => {
        const perChange = spares.perChange[i] || (i === 0 ? 1 : 0);
        const wanted = Math.max(1, perChange * changes - spares.stock[i]);
        const label = document.createElement("label");
        const box = document.createElement("input");
        box.type = "checkbox";
        box.checked = perChange > 0 || !coarseOrFineKnown(spares);
        box.value = sku;
        box.dataset.cls = cls;
        box.dataset.index = String(i);
        const name = document.createElement("span");
        name.textContent = text.filterClass[cls] || cls;
        const qty = document.createElement("span");
        qty.className = "qty";
        const minus = document.createElement("button");
        minus.type = "button";
        minus.dataset.step = "-1";
        minus.textContent = "−";
        const output = document.createElement("output");
        output.value = String(wanted);
        const plus = document.createElement("button");
        plus.type = "button";
        plus.dataset.step = "1";
        plus.textContent = "+";
        qty.append(minus, output, plus);
        label.append(box, name, qty);
        return label;
      }),
    );
    cart.showModal();
  }

  /** The order arrived: move it into the stock. */
  _filtersReceived() {
    const deviceId = this._config.device_id || devicesOf(this._hass)[0];
    if (!deviceId) return;
    this._hass.callService(DOMAIN, "filters_received", { device_id: deviceId });
  }

  /** home_assistant_<model>_<unit>, e.g. home_assistant_df-350-connect_0020003A3032510E. */
  _cartReference() {
    const deviceId = this._config.device_id || devicesOf(this._hass)[0];
    const device = this._hass.devices?.[deviceId];
    const model = (device?.model || this._filtersModel || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    const unit = device?.serial_number
      ? String(device.serial_number)
      : String(device?.primary_config_entry || device?.config_entries?.[0] || deviceId || "").slice(0, 12);
    return [CART_REF, model, unit].filter(Boolean).join("_");
  }

  /** POST the ticked filters to the shop, which opens its cart in a new tab. */
  _orderFilters() {
    const picked = [...this._el.cart.querySelectorAll("input:checked")].map((box) => ({
      sku: box.value,
      index: Number(box.dataset.index),
      qty: Math.max(1, Number(box.closest("label").querySelector("output").value) || 1),
    }));
    if (!picked.length) return;
    const form = document.createElement("form");
    form.method = "post";
    form.action = CART;
    form.target = "_blank";
    form.rel = "noopener";
    const field = (name, value) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = value;
      form.append(input);
    };
    field("veqai_ref", this._cartReference());
    picked.forEach(({ sku, qty }, i) => {
      field(`items[${i}][sku]`, sku);
      field(`items[${i}][qty]`, String(qty));
    });
    this.shadowRoot.append(form);
    form.submit();
    form.remove();
    // Remember the order until it is received, so the stock follows.
    const deviceId = this._config.device_id || devicesOf(this._hass)[0];
    if (deviceId && this._ids.stockCoarse) {
      const counts = { coarse: 0, fine: 0 };
      for (const { index, qty } of picked) counts[index === 0 ? "coarse" : "fine"] += qty;
      this._hass.callService(DOMAIN, "filters_ordered", { device_id: deviceId, ...counts });
    }
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

/**
 * Editor of the main card: the declarative form (device, name, options of
 * the card) followed by the settings of the unit that belong next to it.
 * Those are not stored in the card: the field reads the number entity of
 * the unit and writes it back with number.set_value, so the owner adjusts
 * the filter reminder while placing the card, without digging into the
 * device page, and every card of that unit follows.
 */
class VentsA21CardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _build() {
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        .unit { margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--divider-color); }
        .unit h4 { margin: 0 0 4px; font-size: 14px; font-weight: 500; }
        .unit p { margin: 0 0 12px; font-size: 12px; color: var(--secondary-text-color); }
        .unit label { display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 14px; }
        .unit input { width: 6em; padding: 6px 8px; font: inherit; color: var(--primary-text-color);
          background: var(--card-background-color); border: 1px solid var(--divider-color); border-radius: 4px; }
      </style>
      <ha-form></ha-form>
      <div class="unit" hidden>
        <h4></h4><p></p>
        <label><span></span><input type="number" min="0" max="${FILTER_SOON_MAX}" step="1"></label>
      </div>`;
    this._form = this.shadowRoot.querySelector("ha-form");
    this._form.addEventListener("value-changed", (ev) => {
      ev.stopPropagation();
      this._config = ev.detail.value;
      this.dispatchEvent(
        new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true })
      );
    });
    this._unit = this.shadowRoot.querySelector(".unit");
    this._input = this._unit.querySelector("input");
    this._input.addEventListener("change", () => this._setReminder());
  }

  /** The reminder entity of the configured unit, if the integration has it. */
  _reminderEntity() {
    const hass = this._hass;
    const deviceId = this._config.device_id || devicesOf(hass)[0];
    for (const [entityId, entity] of Object.entries(hass.entities || {})) {
      if (
        entity.platform === DOMAIN &&
        entity.device_id === deviceId &&
        entityId.startsWith("number.") &&
        entity.translation_key === "filters_reminder_days"
      )
        return entityId;
    }
    return null;
  }

  _setReminder() {
    const entityId = this._reminderEntity();
    const value = Number(this._input.value);
    if (!entityId || !Number.isFinite(value)) return;
    const days = Math.min(Math.max(Math.round(value), 0), FILTER_SOON_MAX);
    this._input.value = String(days);
    this._hass.callService("number", "set_value", { entity_id: entityId, value: days });
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this.shadowRoot) this._build();
    const form = VentsA21Card.getConfigForm();
    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = form.schema;
    this._form.computeLabel = form.computeLabel;

    const text = TEXT[(this._hass.language || "en").startsWith("fr") ? "fr" : "en"];
    const entityId = this._reminderEntity();
    const stateObj = entityId ? this._hass.states[entityId] : undefined;
    this._unit.hidden = !stateObj;
    if (!stateObj) return;
    this._unit.querySelector("h4").textContent = text.unitSettings;
    this._unit.querySelector("p").textContent = text.unitSettingsHint;
    this._unit.querySelector("span").textContent = text.reminderDays;
    // Do not overwrite what the owner is typing.
    if (this.shadowRoot.activeElement !== this._input) {
      this._input.value = stateObj.state;
    }
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
  for (const [tag, cls] of [...CARDS, [CARD_EDITOR, VentsA21CardEditor]]) {
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
  const lang = uiLanguage();
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
