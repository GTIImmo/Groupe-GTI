(function () {
  const $ = (sel) => document.querySelector(sel);

  const els = {
    slide: $("#slide"),
    hudAgency: $("#hudAgency"),
    hudMode: $("#hudMode"),
    hudInfo: $("#hudInfo"),

    viewSlide: $("#viewSlide"),
    viewEmpty: $("#viewEmpty"),

    emptyTitle: $("#emptyTitle"),
    emptySub: $("#emptySub"),

    slidePrice: $("#slidePrice"),
    slideTitle: $("#slideTitle"),
    slideMeta: $("#slideMeta"),
    slideStateRibbon: $("#slideStateRibbon"),

    slideImgA: $("#slideImgA"),
    slideImgB: $("#slideImgB"),
    slideVideo: $("#slideVideo"),
    slideProg: $("#slideProg"),

    slideStats: $("#slideStats"),

    contactAdvisor: $("#contactAdvisor"),
    contactAgencyPhone: $("#contactAgencyPhone"),
    contactAdvisorMobile: $("#contactAdvisorMobile"),

    dpeCard: $("#dpeCard"),
    dpeConsoImg: $("#dpeConsoImg"),
    dpeGesImg: $("#dpeGesImg"),

    // ✅ QR
    qrBlock: $("#qrBlock"),
    qrBox: $("#qrBox"),
    qrImg: $("#qrImg"),
  };

  const PLACEHOLDER_SVG =
    "data:image/svg+xml;charset=utf-8," +
    encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900">
        <defs>
          <linearGradient id="g" x1="0" x2="1">
            <stop offset="0" stop-color="#eef1f6"/>
            <stop offset="1" stop-color="#f6f7fb"/>
          </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#g)"/>
        <circle cx="420" cy="420" r="220" fill="rgba(194,24,91,.12)"/>
        <circle cx="980" cy="300" r="260" fill="rgba(15,118,110,.12)"/>
        <text x="50%" y="52%" fill="rgba(18,19,24,.82)" font-family="Inter, Arial" font-size="52" font-weight="900" text-anchor="middle">
          GTI Immobilier
        </text>
        <text x="50%" y="60%" fill="rgba(18,19,24,.55)" font-family="Inter, Arial" font-size="24" font-weight="650" text-anchor="middle">
          Visuel indisponible
        </text>
      </svg>
    `);

  // ---------------------------
  // Helpers
  // ---------------------------
  function clampInt(v, min, max, def) {
    const n = parseInt(v, 10);
    if (!Number.isFinite(n)) return def;
    return Math.max(min, Math.min(max, n));
  }
  function safeText(s) { return (s == null ? "" : String(s)).trim(); }
  function normalizeAgency(s) { return safeText(s).toUpperCase(); }
  function parseDateKey(x) { const t = Date.parse(safeText(x)); return Number.isFinite(t) ? t : 0; }
  function asNumber(v){ const n = Number(v); return Number.isFinite(n) ? n : null; }

  function formatPriceEUR(value) {
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0) return "Prix sur demande";
    try {
      return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
    } catch {
      return `${Math.round(n).toLocaleString("fr-FR")} €`;
    }
  }

  // Nettoie le titre : retire “X pièce(s)” + coupe si trop long
  function cleanTitle(raw) {
    let t = safeText(raw || "Bien immobilier");
    if (!t) return "Bien immobilier";

    t = t.replace(/\s*[-–—]?\s*\d+\s*pi[eè]ce(?:\(\s*s\s*\)|s)?\s*$/i, "");
    t = t.replace(/\b\d+\s*pi[eè]ce(?:\(\s*s\s*\)|s)\b/ig, "").replace(/\s{2,}/g, " ").trim();

    const max = 38;
    if (t.length > max) t = t.slice(0, max - 1).trim() + "…";
    return t || "Bien immobilier";
  }

  function displayNature(item) {
    return cleanTitle(item.nature || item.propertyType || item.typeLabel || item.category || item.title || "Bien immobilier");
  }

  function propertyTypeIcon(item) {
    const type = safeText(item.nature || item.propertyType || item.typeLabel || "").toLowerCase();
    if (type.includes("appartement") || type.includes("studio") || type.includes("duplex") || type.includes("triplex")) {
      return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 20V6l7-3 7 3v14" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M9 9h1M9 13h1M14 9h1M14 13h1M11 20v-4h2v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`;
    }
    if (type.includes("maison") || type.includes("villa") || type.includes("chalet") || type.includes("ferme") || type.includes("demeure") || type.includes("mas") || type.includes("propriété")) {
      return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 10.5 12 4l8 6.5V20H4v-9.5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M10 20v-5h4v5" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>`;
    }
    if (type.includes("bureau") || type.includes("local") || type.includes("commerce") || type.includes("boutique")) {
      return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 20V7h16v13" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M2 20h20M8 11h8M8 15h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`;
    }
    if (type.includes("terrain")) {
      return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 19 10 7l3 5 7-4-4 11H4Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M4 19h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`;
    }
    if (type.includes("garage") || type.includes("parking")) {
      return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 11 12 4l9 7v9H3v-9Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M8 20v-5h8v5M8 11h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`;
    }
    return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 20V6l7-3 7 3v14" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M9 9h1M9 13h1M14 9h1M14 13h1M11 20v-4h2v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`;
  }

  function displayCityOnly(item) {
    const city = safeText(item.city || "");
    const postal = safeText(item.postalCode || "");
    if (!city) return "";
    if (!postal) return city;
    return city.replace(new RegExp(`\\s*${postal}\\s*$`), "").trim() || city;
  }

  function propertyTypeTone(item) {
    const type = safeText(item.nature || item.propertyType || item.typeLabel || "").toLowerCase();
    if (type.includes("appartement") || type.includes("studio") || type.includes("duplex") || type.includes("triplex")) return "appartement";
    if (type.includes("maison") || type.includes("villa") || type.includes("chalet") || type.includes("ferme") || type.includes("demeure") || type.includes("mas") || type.includes("propri")) return "maison";
    if (type.includes("bureau") || type.includes("local") || type.includes("commerce") || type.includes("boutique")) return "pro";
    if (type.includes("terrain")) return "terrain";
    if (type.includes("garage") || type.includes("parking")) return "parking";
    return "default";
  }

  function normalizePhotos(photos, max = 10) {
    if (!Array.isArray(photos)) return [];
    const out = [];
    const seen = new Set();
    for (const u of photos) {
      const url = (u || "").toString().trim();
      if (!url) continue;
      if (seen.has(url)) continue;
      seen.add(url);
      out.push(url);
      if (out.length >= max) break;
    }
    return out;
  }

  // salles de bain : support large
  function readBathrooms(item) {
    const candidates = [
      item.bathrooms, item.bathroom, item.bathroomCount,
      item.nbBathrooms, item.sdb, item.nbSdb, item.nb_sdb, item.bains
    ];
    for (const c of candidates) {
      const n = asNumber(c);
      if (n != null && n > 0) return Math.round(n);
    }
    return null;
  }
  function readWC(item){
    const candidates = [item.wc, item.WC, item.nbWc, item.nb_wc];
    for (const c of candidates){
      const n = asNumber(c);
      if (n != null && n >= 0) return Math.round(n);
    }
    return null;
  }
  function readLevels(item){
    const candidates = [item.levels, item.level, item.nbLevels, item.niveaux, item.etages];
    for (const c of candidates){
      const n = asNumber(c);
      if (n != null && n > 0) return Math.round(n);
    }
    return null;
  }
  function readTerrain(item){
    const candidates = [item.terrain, item.land, item.landSurface, item.surfterrain, item.surfaceTerrain];
    for (const c of candidates){
      const n = asNumber(c);
      if (n != null && n > 0) return Math.round(n);
    }
    return null;
  }
  function readCellar(item){
    const v = item.cellar ?? item.cave ?? item.hasCellar;
    if (typeof v === "boolean") return v;
    const s = safeText(v).toUpperCase();
    if (!s) return null;
    if (["OUI","YES","TRUE","1"].includes(s)) return true;
    if (["NON","NO","FALSE","0"].includes(s)) return false;
    return null;
  }

  // ✅ parking / terrasse : support large (0 si absent)
  function readParkingInt(item){
    const candidates = [item.parkingInterieur, item.parkingInterior, item.parking_int, item.nbParkingInterieur, item.nbParkingInt];
    for (const c of candidates){
      const n = asNumber(c);
      if (n != null && n >= 0) return Math.round(n);
    }
    return 0;
  }
  function readParkingExt(item){
    const candidates = [item.parkingExterieur, item.parkingExterior, item.parking_ext, item.nbParkingExterieur, item.nbParkingExt];
    for (const c of candidates){
      const n = asNumber(c);
      if (n != null && n >= 0) return Math.round(n);
    }
    return 0;
  }
  function readTerrace(item){
    const candidates = [item.terrasse, item.terrace, item.surfaceTerrasse, item.terrasseSurface, item.terraceSurface];
    for (const c of candidates){
      const n = asNumber(c);
      if (n != null && n >= 0) return Math.round(n);
    }
    return 0;
  }

  function normalizeItem(item) {
    const it = { ...item };
    it.photos = normalizePhotos(it.photos, 10);

    const s = asNumber(it.surface);
    if (s != null) it.surface = s;

    const r = asNumber(it.rooms);
    if (r != null) it.rooms = Math.round(r);

    const b = asNumber(it.bedrooms);
    if (b != null) it.bedrooms = Math.round(b);

    const ba = readBathrooms(it);
    if (ba != null) it.bathrooms = ba;

    const wc = readWC(it);
    if (wc != null) it.wc = wc;

    const lv = readLevels(it);
    if (lv != null) it.levels = lv;

    const terr = readTerrain(it);
    if (terr != null) it.terrain = terr;

    const cel = readCellar(it);
    if (cel != null) it.cellar = cel;

    // ✅ parking/terrasse normalisés
    it.parkingInterieur = readParkingInt(it);
    it.parkingExterieur = readParkingExt(it);
    it.terrasse = readTerrace(it);

    return it;
  }

  function getPhoto(item, idx) {
    const arr = Array.isArray(item.photos) ? item.photos : [];
    if (!arr.length) return PLACEHOLDER_SVG;
    const i = ((idx % arr.length) + arr.length) % arr.length;
    return arr[i] || PLACEHOLDER_SVG;
  }

  function sortItems(items) {
    return items.slice().sort((a, b) => {
      const da = parseDateKey(a.updatedAt);
      const db = parseDateKey(b.updatedAt);
      if (db !== da) return db - da;
      const wa = Number(a.weight || 0);
      const wb = Number(b.weight || 0);
      return wb - wa;
    });
  }

  function splitAcrossScreens(items, screen, screens, seed) {
    if (screens <= 1) return items;
    return items.filter((_, index) => ((index + seed) % screens) === (screen - 1));
  }

  // ---------------------------
  // Contact parsing (agence string)
  // ---------------------------
  function digitsOnly(s) { return safeText(s).replace(/[^\d]/g, ""); }
  function formatFR10(d10) { return d10.replace(/(\d{2})(?=\d)/g, "$1 ").trim(); }
  function isLikelyFRPhone(d) { return d.length === 10 && d.startsWith("0"); }

  function extractContactFromAgence(agenceStr) {
    const s = safeText(agenceStr);
    const out = { agencyName: "", agencyPhone: "", advisorName: "", advisorMobile: "" };
    if (!s) return out;

    const mName = s.match(/^(.+?)\s*T[ÉE]L\s*:/i);
    if (mName) out.agencyName = safeText(mName[1]);

    const mAgencyPhone = s.match(/T[ÉE]L\s*:\s*([0-9 .-]{8,})/i);
    if (mAgencyPhone) {
      const d = digitsOnly(mAgencyPhone[1]);
      if (isLikelyFRPhone(d)) out.agencyPhone = formatFR10(d);
    }

    const mAdvisor = s.match(/N[ÉE]GOCIATEUR\s+EN\s+CHARGE\s+DU\s+BIEN\s*:\s*([^:]+?)\s*T[ÉE]L\s*:/i);
    if (mAdvisor) out.advisorName = safeText(mAdvisor[1]);

    const mAdvisorMobile = s.match(/N[ÉE]GOCIATEUR\s+EN\s+CHARGE\s+DU\s+BIEN\s*:\s*.+?\s*T[ÉE]L\s*:\s*([0-9 .-]{8,})/i);
    if (mAdvisorMobile) {
      const d = digitsOnly(mAdvisorMobile[1]);
      if (isLikelyFRPhone(d)) out.advisorMobile = formatFR10(d);
    }

    return out;
  }

  function pickAdvisorMobile(item, extracted) {
    if (extracted && extracted.advisorMobile) return extracted.advisorMobile;
    const d = digitsOnly(item.phone);
    if (isLikelyFRPhone(d)) return formatFR10(d);
    return "—";
  }

  function normalizeStateLabel(value) {
    return safeText(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
  }

  function stateRibbonConfig(item) {
    const state = normalizeStateLabel(item && item.state);
    if (!state || state === "ACTIF") return null;
    if (state.includes("OFFRE")) return { label: "Sous offre", cls: "stateRibbon--offer" };
    if (state.includes("COMPROMIS")) return { label: "Sous compromis", cls: "stateRibbon--compromis" };
    if (state.includes("VENDU") || state.includes("VENTE")) return { label: "VENDU", cls: "stateRibbon--sold" };
    return null;
  }

  function setStateRibbon(item) {
    if (!els.slideStateRibbon) return;
    const config = stateRibbonConfig(item);
    if (!config) {
      els.slideStateRibbon.textContent = "";
      els.slideStateRibbon.className = "stateRibbon hidden";
      return;
    }
    els.slideStateRibbon.textContent = config.label;
    els.slideStateRibbon.className = `stateRibbon ${config.cls}`;
  }

  // ---------------------------
  // SVG icons (modern)
  // ---------------------------
  function iconSVG(name) {
    switch (name) {
      case "surface":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 9V4h5M20 15v5h-5M20 9V4h-5M4 15v5h5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>`;
      case "ref":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="4" y="5" width="16" height="14" rx="3" stroke="currentColor" stroke-width="2"/>
          <path d="M8 10h8M8 14h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      case "rooms":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 10.5V20h16v-9.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M3 10.5 12 4l9 6.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M10 20v-6h4v6" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`;
      case "bedrooms":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M3 18v-7a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M3 18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M7 8V6a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      case "bathrooms":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M5 12h14v3a5 5 0 0 1-5 5H10a5 5 0 0 1-5-5v-3Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          <path d="M7 12V7a3 3 0 0 1 3-3h2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M16 8h2M18 6v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      case "wc":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M7 7a5 5 0 0 1 10 0v6a5 5 0 0 1-10 0V7Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          <path d="M7 11h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M9 20h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      case "levels":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M7 20V10l5-4 5 4v10" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          <path d="M10 20v-5h4v5" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`;
      case "cellar":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 10l8-5 8 5v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          <path d="M9 21v-6a3 3 0 0 1 6 0v6" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`;
      case "terrain":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 19l7-14 2 4 7-3-6 13H4Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          <path d="M6 19h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      case "parkingInterieur":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M7 20V4h7a5 5 0 0 1 0 10H7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M7 14h7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      case "parkingExterieur":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M7 20V4h7a5 5 0 0 1 0 10H7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M12 22s6-3.8 6-10a6 6 0 1 0-12 0c0 6.2 6 10 6 10Z" stroke="currentColor" stroke-width="2"/>
        </svg>`;
      case "terrasse":
        return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 18h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M6 18V9h12v9" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          <path d="M8 9V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      default:
        return "";
    }
  }

  function plural(n, one, many) { return n > 1 ? many : one; }

  // ---------------------------
  // 1 LIGNE MAX sous la photo (auto-fit)
  // ---------------------------
  function limitStatsToOneLine(container) {
    if (!container) return;
    const chips = Array.from(container.querySelectorAll(".statChip"));
    if (!chips.length) return;

    chips.forEach(ch => { ch.style.display = ""; });

    const maxW = container.clientWidth;
    if (!maxW) return;

    let safety = 80;
    while (container.scrollWidth > maxW && safety-- > 0) {
      const last = [...container.querySelectorAll(".statChip")].reverse().find(x => x.style.display !== "none");
      if (!last) break;
      last.style.display = "none";
    }
  }

  let __statsResizeRaf = 0;
  function scheduleFitStats() {
    if (!els.slideStats) return;
    cancelAnimationFrame(__statsResizeRaf);
    __statsResizeRaf = requestAnimationFrame(() => limitStatsToOneLine(els.slideStats));
  }
  window.addEventListener("resize", scheduleFitStats, { passive: true });

  function renderStats(item) {
    if (!els.slideStats) return;

    const stats = [];
    const ref = safeText(item.ref);

    const surface = (item.surface != null && Number(item.surface) > 0) ? Math.round(Number(item.surface)) : null;
    const rooms = (item.rooms != null && Number(item.rooms) > 0) ? Math.round(Number(item.rooms)) : null;
    const bedrooms = (item.bedrooms != null && Number(item.bedrooms) > 0) ? Math.round(Number(item.bedrooms)) : null;
    const baths = (item.bathrooms != null && Number(item.bathrooms) > 0) ? Math.round(Number(item.bathrooms)) : null;

    const wc = (item.wc != null && Number(item.wc) > 0) ? Math.round(Number(item.wc)) : null;
    const levels = (item.levels != null && Number(item.levels) > 0) ? Math.round(Number(item.levels)) : null;
    const terrain = (item.terrain != null && Number(item.terrain) > 0) ? Math.round(Number(item.terrain)) : null;
    const cellar = (typeof item.cellar === "boolean") ? item.cellar : null;

    // ✅ nouveaux champs
    const pInt = (item.parkingInterieur != null && Number(item.parkingInterieur) > 0) ? Math.round(Number(item.parkingInterieur)) : 0;
    const pExt = (item.parkingExterieur != null && Number(item.parkingExterieur) > 0) ? Math.round(Number(item.parkingExterieur)) : 0;
    const terr = (item.terrasse != null && Number(item.terrasse) > 0) ? Math.round(Number(item.terrasse)) : 0;

    // Base
    if (ref) stats.push({ pr: 110, key:"ref", value:ref, label:"Référence", cls:"is-priority" });
    if (surface != null) stats.push({ pr: 100, key:"surface", value:`${surface} m²`, label:"Surface" });
    if (rooms != null) stats.push({ pr: 90, key:"rooms", value:`${rooms}`, label: plural(rooms, "Pièce", "Pièces") });
    if (bedrooms != null) stats.push({ pr: 80, key:"bedrooms", value:`${bedrooms}`, label: plural(bedrooms, "Chambre", "Chambres") });
    if (baths != null) stats.push({ pr: 70, key:"bathrooms", value:`${baths}`, label: plural(baths, "Salle de bain", "Salles de bain") });

    // ✅ PRIORITAIRES : parking/terrasse
    if (pInt > 0) stats.push({ pr: 69, key:"parkingInterieur", value:`${pInt}`, label: plural(pInt, "Parking int.", "Parkings int."), cls:"is-priority" });
    if (pExt > 0) stats.push({ pr: 68, key:"parkingExterieur", value:`${pExt}`, label: plural(pExt, "Parking ext.", "Parkings ext."), cls:"is-priority" });
    if (terr > 0) stats.push({ pr: 67, key:"terrasse", value:`${terr} m²`, label:"Terrasse", cls:"is-priority" });

    // autres
    if (terrain != null) stats.push({ pr: 65, key:"terrain", value:`${terrain} m²`, label:"Terrain" });
    if (wc != null) stats.push({ pr: 60, key:"wc", value:`${wc}`, label:"WC" });

    // secondaires
    if (levels != null) stats.push({ pr: 55, key:"levels", value:`${levels}`, label: plural(levels, "Niveau", "Niveaux"), cls:"is-secondary" });
    if (cellar != null) stats.push({ pr: 50, key:"cellar", value: cellar ? "Oui" : "Non", label:"Cave", cls:"is-secondary" });

    stats.sort((a,b)=>b.pr-a.pr);

    const preList = stats.slice(0, 10);

    if (!preList.length) {
      els.slideStats.innerHTML = "";
      els.slideStats.classList.add("hidden");
      return;
    }

    els.slideStats.classList.remove("hidden");
    els.slideStats.innerHTML = preList.map(s => `
      <div class="statChip ${s.cls ? s.cls : ""}" data-stat="${s.key}">
        <div class="statIcon" aria-hidden="true">${iconSVG(s.key)}</div>
        <div class="statText">
          <div class="statValue">${s.value}</div>
          <div class="statLabel">${s.label}</div>
        </div>
      </div>
    `).join("");

    scheduleFitStats();
  }

  // ---------------------------
  // DPE
  // ---------------------------
  function setDpe(item) {
    const conso = item && item.dpe ? safeText(item.dpe.conso) : "";
    const ges = item && item.dpe ? safeText(item.dpe.ges) : "";

    const hasAny = !!(conso || ges);
    if (!els.dpeCard) return;

    els.dpeCard.classList.toggle("hidden", !hasAny);

    if (els.dpeConsoImg) {
      if (conso) { els.dpeConsoImg.src = conso; els.dpeConsoImg.classList.remove("hidden"); }
      else { els.dpeConsoImg.removeAttribute("src"); els.dpeConsoImg.classList.add("hidden"); }
    }
    if (els.dpeGesImg) {
      if (ges) { els.dpeGesImg.src = ges; els.dpeGesImg.classList.remove("hidden"); }
      else { els.dpeGesImg.removeAttribute("src"); els.dpeGesImg.classList.add("hidden"); }
    }
  }

  // ---------------------------
  // QR
  // ---------------------------
  function pickQrUrl(item, params) {
    const fromParams = safeText(params && params.qr);
    if (fromParams) return fromParams;

    const candidates = [
      item && item.qr,
      item && item.qrUrl,
      item && item.qr_url,
      item && item.qrcode,
      item && item.qrCode,
      item && item.qr_code,
      item && item.qr_code_url
    ];
    for (const c of candidates) {
      const u = safeText(c);
      if (u) return u;
    }
    return "";
  }

  function setQr(item, params) {
    if (!els.qrBlock || !els.qrBox || !els.qrImg) return;

    const qrUrl = pickQrUrl(item, params);
    if (!qrUrl) {
      els.qrImg.removeAttribute("src");
      els.qrBox.classList.add("is-empty");
      els.qrBlock.classList.remove("hidden");
      return;
    }

    els.qrImg.src = qrUrl;
    els.qrBox.classList.remove("is-empty");
    els.qrBlock.classList.remove("hidden");
  }

  // ---------------------------
  // Params / fetch
  // ---------------------------
  function getParams() {
    const u = new URL(window.location.href);
    const p = u.searchParams;
    return {
      agence: (p.get("agence") || "").trim(),
      screen: clampInt(p.get("screen"), 1, 999, 1),
      screens: clampInt(p.get("screens"), 1, 999, 1),
      seed: clampInt(p.get("seed"), 0, 999999, 0),

      rotate: clampInt(p.get("rotate"), 3, 3600, 12),
      photoRotate: clampInt(p.get("photoRotate"), 2, 120, 4),
      refresh: clampInt(p.get("refresh"), 10, 3600, 120),

      // ✅ NEW : limite photo par bien (par défaut 5)
      maxPhotos: clampInt(p.get("maxPhotos"), 1, 20, 5),

      src: (p.get("src") || "exports/catalogue_vitrine.json").trim(),
      debug: p.get("debug") === "1",

      qr: (p.get("qr") || "").trim(),
      promo: p.get("promo") !== "0",
      promoEvery: clampInt(p.get("promoEvery"), 1, 999, 6),
      promoDuration: clampInt(p.get("promoDuration"), 0, 300, 0),
      promoOffset: clampInt(p.get("promoOffset"), -1, 999, -1),
      promoVideo: (p.get("promoVideo") || "assets/promo-gti.mp4.mp4").trim(),
    };
  }

  async function fetchCatalogue(src) {
    const url = new URL(src, window.location.href);
    url.searchParams.set("ts", String(Date.now()));
    const res = await fetch(url.toString(), { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (!data || !Array.isArray(data.items)) throw new Error("JSON invalide (attendu: {generatedAt, items[]})");
    return data;
  }

  function showView(name) {
    $("#viewSlide").classList.toggle("hidden", name !== "slide");
    $("#viewEmpty").classList.toggle("hidden", name !== "empty");
  }

  function showEmpty(title, sub) {
    $("#emptyTitle").textContent = title;
    $("#emptySub").textContent = sub;
    showView("empty");
  }

  function setHud(params, count, generatedAt) {
    if (!params.debug) return;
    document.body.classList.add("debug");
    if (els.hudAgency) els.hudAgency.textContent = params.agence ? params.agence.toUpperCase() : "TOUTES AGENCES";
    if (els.hudMode) els.hudMode.textContent = "SLIDE";
    if (els.hudInfo) els.hudInfo.textContent = `Écran ${params.screen}/${params.screens} • ${count} annonces • ${generatedAt || "…"}`;
  }

  // ---------------------------
  // Preload queue
  // ---------------------------
  const preloadCache = new Map();
  function preload(url) {
    if (!url) return Promise.resolve(false);
    if (preloadCache.has(url)) return preloadCache.get(url);

    const pr = new Promise((resolve) => {
      const img = new Image();
      img.decoding = "async";
      img.loading = "eager";
      img.onload = () => resolve(true);
      img.onerror = () => resolve(false);
      img.src = url;
    });

    preloadCache.set(url, pr);
    if (preloadCache.size > 200) {
      const firstKey = preloadCache.keys().next().value;
      preloadCache.delete(firstKey);
    }
    return pr;
  }

  async function warmupItem(item, startIdx, count) {
    const arr = Array.isArray(item.photos) ? item.photos : [];
    if (!arr.length) return;
    const n = Math.min(count, arr.length);
    for (let k = 0; k < n; k++) {
      await preload(getPhoto(item, startIdx + k));
    }
  }

  function isPromoEntry(entry) {
    return !!(entry && entry.kind === "promo");
  }

  function resolvePromoOffset(params) {
    const every = Math.max(1, params.promoEvery || 1);
    if (params.promoOffset >= 0) return params.promoOffset % every;
    return ((params.screen || 1) - 1) % every;
  }

  function buildPlaylist(items, params) {
    const listings = items.map(item => ({ kind: "listing", id: item.id, item }));
    if (!params.promo || !params.promoVideo || !listings.length) return listings;

    const every = Math.max(1, params.promoEvery || 1);
    const offset = resolvePromoOffset(params);
    const out = [];
    let seenListings = 0;

    for (const entry of listings) {
      out.push(entry);
      seenListings += 1;
      if (((seenListings + offset) % every) === 0) {
        out.push({
          kind: "promo",
          id: `PROMO_${params.screen}_${seenListings}`,
          videoUrl: params.promoVideo,
          durationSec: params.promoDuration,
        });
      }
    }

    return out;
  }

  // ---------------------------
  // Slide engine
  // ---------------------------
  const state = {
    items: [],
    itemIndex: 0,
    photoIndex: 0,
    usingA: true,
    photoTimer: null,
    tickTimer: null,
    progTimer: null,
    promoTimer: null,
    nextItemAt: 0,
    itemDurationMs: 0,
    isTransitioning: false
  };

  function clearTimers() {
    if (state.photoTimer) clearInterval(state.photoTimer);
    if (state.tickTimer) clearInterval(state.tickTimer);
    if (state.progTimer) clearInterval(state.progTimer);
    if (state.promoTimer) clearTimeout(state.promoTimer);
    state.photoTimer = null;
    state.tickTimer = null;
    state.progTimer = null;
    state.promoTimer = null;
    if (els.slideVideo) {
      els.slideVideo.pause();
      try { els.slideVideo.currentTime = 0; } catch (_) {}
    }
  }

  // ✅ durée calculée SANS reboucler les photos
  function computeItemDurationSec(item, rotateMinSec, photoRotateSec, maxPhotos) {
    const count = Array.isArray(item.photos) ? item.photos.length : 0;
    const photosToShow = Math.max(1, Math.min(maxPhotos || 999, count || 1));
    const fullPhotosDuration = photosToShow * photoRotateSec;
    // si rotateMinSec est plus long, on garde la dernière photo (pas de boucle)
    return Math.max(rotateMinSec, fullPhotosDuration);
  }

  function updateProgress() {
    if (!els.slideProg || !state.itemDurationMs) return;
    const now = Date.now();
    const elapsed = Math.max(0, state.itemDurationMs - Math.max(0, state.nextItemAt - now));
    const pct = Math.max(0, Math.min(1, elapsed / state.itemDurationMs));
    els.slideProg.style.width = `${(pct * 100).toFixed(1)}%`;
  }

  function setPromoVisibility(isPromo) {
    if (els.slide) els.slide.classList.toggle("slide--promo", !!isPromo);
    if (els.slidePrice) els.slidePrice.classList.toggle("hidden", !!isPromo);
    if (els.slideStats) els.slideStats.classList.toggle("hidden", !!isPromo);
    if (els.qrBlock) els.qrBlock.classList.toggle("hidden", !!isPromo);
    if (els.dpeCard) els.dpeCard.classList.toggle("hidden", !!isPromo);
    if (els.slideStateRibbon) els.slideStateRibbon.classList.toggle("hidden", !!isPromo);

    const contactCard = document.getElementById("contactCard");
    if (contactCard) contactCard.classList.toggle("hidden", !!isPromo);
  }

  function stopPromoVideo() {
    if (!els.slideVideo) return;
    if (state.promoTimer) {
      clearTimeout(state.promoTimer);
      state.promoTimer = null;
    }
    els.slideVideo.onended = null;
    els.slideVideo.onerror = null;
    els.slideVideo.onloadedmetadata = null;
    els.slideVideo.pause();
    try { els.slideVideo.currentTime = 0; } catch (_) {}
    els.slideVideo.classList.add("hidden");
  }

  function startPromoVideo(entry) {
    if (!els.slideVideo) return;
    const url = entry.videoUrl;
    const absUrl = new URL(url, window.location.href).toString();
    if (els.slideVideo.src !== absUrl) {
      els.slideVideo.src = absUrl;
      els.slideVideo.load();
    }
    els.slideVideo.classList.remove("hidden");
    els.slideVideo.muted = true;
    els.slideVideo.loop = false;
    els.slideVideo.playsInline = true;
    els.slideVideo.autoplay = true;
    els.slideVideo.onended = () => { state.nextItemAt = Date.now(); };
    els.slideVideo.onerror = () => { state.nextItemAt = Date.now(); };
    els.slideVideo.onloadedmetadata = () => {
      const hasFixedDuration = Number(entry.durationSec) > 0;
      const durationMs = hasFixedDuration
        ? entry.durationSec * 1000
        : Math.max(1000, Math.round((els.slideVideo.duration || 0) * 1000));
      state.itemDurationMs = durationMs;
      state.nextItemAt = Date.now() + durationMs;
      if (state.promoTimer) clearTimeout(state.promoTimer);
      if (hasFixedDuration) {
        state.promoTimer = setTimeout(() => { state.nextItemAt = Date.now(); }, durationMs);
      }
    };
    const playPromise = els.slideVideo.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(() => {});
    }
  }

  function setPromoEntry(entry) {
    setPromoVisibility(true);
    stopPromoVideo();

    els.slideImgA.classList.remove("is-visible");
    els.slideImgB.classList.remove("is-visible");
    els.slideImgA.classList.add("hidden");
    els.slideImgB.classList.add("hidden");

    startPromoVideo(entry);

    state.itemDurationMs = Number(entry.durationSec) > 0 ? entry.durationSec * 1000 : 60000;
    state.nextItemAt = Date.now() + state.itemDurationMs;
    if (els.slideProg) els.slideProg.style.width = "0%";

    if (state.photoTimer) {
      clearInterval(state.photoTimer);
      state.photoTimer = null;
    }
  }

  function setSlideItem(item, rotateMinSec, photoRotateSec, params) {
    setPromoVisibility(false);
    stopPromoVideo();

    els.slidePrice.textContent = formatPriceEUR(item.price);
    const nature = displayNature(item);
    const tone = propertyTypeTone(item);
    els.slideTitle.innerHTML = `<span class="slide__titleMain slide__titleMain--${tone}">${nature}</span>`;

    const cityLine = displayCityOnly(item);
    els.slideMeta.textContent = cityLine || "—";

    renderStats(item);
    setDpe(item);
    setQr(item, params);
    setStateRibbon(item);

    const extracted = extractContactFromAgence(item.agence);
    els.contactAdvisor.textContent = extracted.advisorName || "Conseiller GTI";
    els.contactAgencyPhone.textContent = extracted.agencyPhone || "—";
    els.contactAdvisorMobile.textContent = pickAdvisorMobile(item, extracted);

    state.photoIndex = 0;
    state.usingA = true;

    const p0 = getPhoto(item, 0);
    const p1 = getPhoto(item, 1);

    els.slideImgA.classList.remove("hidden");
    els.slideImgB.classList.remove("hidden");
    els.slideImgA.src = p0;
    els.slideImgB.src = p1;
    els.slideImgA.classList.add("is-visible");
    els.slideImgB.classList.remove("is-visible");

    const durSec = computeItemDurationSec(item, rotateMinSec, photoRotateSec, params.maxPhotos);
    state.itemDurationMs = durSec * 1000;
    state.nextItemAt = Date.now() + state.itemDurationMs;
    if (els.slideProg) els.slideProg.style.width = "0%";

    warmupItem(item, 1, 3).catch(()=>{});
    const nextItem = state.items[(state.itemIndex + 1) % state.items.length];
    if (nextItem && !isPromoEntry(nextItem)) preload(getPhoto(nextItem.item, 0)).catch(()=>{});

    // ✅ reset phase rotation photo pour ce bien (photo 1 = 4s plein)
    restartPhotoTimer(photoRotateSec, params.maxPhotos);
  }

  function setSlideEntry(entry, rotateMinSec, photoRotateSec, params) {
    if (isPromoEntry(entry)) {
      setPromoEntry(entry);
      return;
    }
    setSlideItem(entry.item, rotateMinSec, photoRotateSec, params);
  }

  function restartInfoAnimation(slideEl) {
    if (!slideEl) return;
    slideEl.classList.remove("is-info-animating");
    void slideEl.offsetWidth;
    slideEl.classList.add("is-info-animating");
    window.setTimeout(() => {
      slideEl.classList.remove("is-info-animating");
    }, 1350);
  }

  // ✅ Transition "book" très visible (sans texte)
  function transitionToItem(item, rotateMinSec, photoRotateSec, params) {
    const slideEl = document.getElementById("slide");
    if (!slideEl) {
      setSlideEntry(item, rotateMinSec, photoRotateSec, params);
      return;
    }

    state.isTransitioning = true;

    slideEl.classList.add("is-changing");
    slideEl.classList.remove("is-active");
    slideEl.classList.add("is-exit");

    setTimeout(() => {
      slideEl.classList.remove("is-exit");
      slideEl.classList.add("is-enter");

      setSlideEntry(item, rotateMinSec, photoRotateSec, params);
      restartInfoAnimation(slideEl);

      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          slideEl.classList.remove("is-enter");
          slideEl.classList.add("is-active");
        });
      });
    }, 520);

    setTimeout(() => {
      slideEl.classList.remove("is-changing");
      state.isTransitioning = false;
    }, 1250);
  }

  function restartPhotoTimer(photoRotateSec, maxPhotos) {
    // ✅ Important : redémarrer le timer photo à CHAQUE changement de bien
    // => la 1ère photo reste toujours photoRotateSec (pas 1s “par hasard”)
    if (state.photoTimer) clearInterval(state.photoTimer);
    state.photoTimer = setInterval(() => {
      const item = state.items[state.itemIndex];
      if (!item || isPromoEntry(item)) return;
      swapPhoto(item.item, maxPhotos).catch(()=>{});
    }, photoRotateSec * 1000);
  }

  async function swapPhoto(item, maxPhotos) {
    // ✅ ne change pas de photo pendant un changement de bien
    if (state.isTransitioning) return;

    const photos = Array.isArray(item.photos) ? item.photos : [];
    if (photos.length <= 1) return;

    const maxShow = Math.max(1, Math.min(maxPhotos || 999, photos.length));
    // ✅ pas de boucle : arrivé à la dernière photo autorisée, on stoppe.
    if (state.photoIndex >= maxShow - 1) return;

    state.photoIndex++;
    const nextUrl = getPhoto(item, state.photoIndex);

    const show = state.usingA ? els.slideImgB : els.slideImgA;
    const hide = state.usingA ? els.slideImgA : els.slideImgB;

    await preload(nextUrl);
    show.src = nextUrl;

    requestAnimationFrame(() => {
      hide.classList.remove("is-visible");
      show.classList.add("is-visible");
    });

    state.usingA = !state.usingA;

    warmupItem(item, state.photoIndex + 1, 2).catch(()=>{});
  }

  function startSlide(items, rotateMinSec, photoRotateSec, params) {
    clearTimers();
    state.items = items;
    state.itemIndex = 0;

    const slideEl = document.getElementById("slide");
    if (slideEl) {
      slideEl.classList.remove("is-exit","is-enter","is-changing");
      slideEl.classList.add("is-active");
    }

    const first = items[0];
    setSlideEntry(first, rotateMinSec, photoRotateSec, params);
    restartInfoAnimation(slideEl);

    state.tickTimer = setInterval(() => {
      if (Date.now() < state.nextItemAt) return;
      if (state.isTransitioning) return;

      state.itemIndex = (state.itemIndex + 1) % state.items.length;
      const item = state.items[state.itemIndex];

      transitionToItem(item, rotateMinSec, photoRotateSec, params);
    }, 250);

    state.progTimer = setInterval(updateProgress, 120);

    showView("slide");
  }

  // ---------------------------
  // Refresh loop
  // ---------------------------
  let refreshTimer = null;
  let lastFingerprint = "";

  function fingerprint(items) {
    return items.map(i => `${i.id}|${i.updatedAt}|${(i.photos && i.photos.length) || 0}|${i.dpe ? "dpe" : ""}|${i.parkingInterieur||0}|${i.parkingExterieur||0}|${i.terrasse||0}`).join(";;");
  }

  async function runOnce() {
    const params = getParams();
    document.body.classList.toggle("debug", !!params.debug);

    try {
      const data = await fetchCatalogue(params.src);

      let items = Array.isArray(data.items) ? data.items : [];
      items = items.map(normalizeItem);

      if (params.agence) {
        const target = normalizeAgency(params.agence);
        items = items.filter(x => normalizeAgency(x.agence).includes(target));
      }

      items = sortItems(items);
      items = splitAcrossScreens(items, params.screen, params.screens, params.seed);

      setHud(params, items.length, data.generatedAt);

      if (!items.length) {
        clearTimers();
        showEmpty("Aucune annonce à afficher", "Vérifie agence/screen/screens et src=exports/catalogue_vitrine.json");
        return;
      }

      const playlist = buildPlaylist(items, params);
      const fp = `${fingerprint(items)}|promo=${params.promo ? 1 : 0}|every=${params.promoEvery}|duration=${params.promoDuration}|offset=${resolvePromoOffset(params)}|video=${params.promoVideo}`;
      if (fp !== lastFingerprint) {
        lastFingerprint = fp;
        preload(getPhoto(items[0], 0)).catch(()=>{});
        startSlide(playlist, params.rotate, params.photoRotate, params);
      } else {
        showView("slide");
        scheduleFitStats();
      }
    } catch (e) {
      clearTimers();
      showEmpty("Erreur de chargement", `Impossible de charger le catalogue (${safeText(e.message || e)}).`);
    }
  }

  function startRefreshLoop() {
    if (refreshTimer) clearInterval(refreshTimer);
    const params = getParams();
    refreshTimer = setInterval(runOnce, params.refresh * 1000);
  }

  runOnce();
  startRefreshLoop();
})();
