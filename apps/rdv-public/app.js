(function () {
  const $ = (id) => document.getElementById(id);
  const body = document.body;
  const pageType = (body && body.dataset && body.dataset.page) || "listing";
  const state = {
    ref: null,
    agency: null,
    context: null,
    slots: [],
    selectedSlot: null,
    selectedDayKey: null,
    selectedMonthKey: null,
    mode: pageType,
  };
  const WEEKDAY_SHORT = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

  const els = {
    loadingPanel: $("loadingPanel"),
    errorPanel: $("errorPanel"),
    errorMessage: $("errorMessage"),
    homePanel: $("homePanel"),
    contentPanel: $("contentPanel"),
    heroImage: $("heroImage"),
    heroSplash: $("heroSplash"),
    heroSplashTitle: $("heroSplashTitle"),
    heroSplashCopy: $("heroSplashCopy"),
    heroContact: $("heroContact"),
    heroCallCta: $("heroCallCta"),
    homeCallAction: $("homeCallAction"),
    homeMailAction: $("homeMailAction"),
    homeSaveContactButton: $("homeSaveContactButton"),
    visitActionMeta: $("visitActionMeta"),
    commercialName: $("commercialName"),
    commercialNameCard: $("commercialNameCard"),
    commercialPhoneInline: $("commercialPhoneInline"),
    commercialPhone: $("commercialPhone"),
    commercialEmail: $("commercialEmail"),
    agencyName: $("agencyName"),
    agencyPhone: $("agencyPhone"),
    agencyEmail: $("agencyEmail"),
    callNowButton: $("callNowButton"),
    saveContactButton: $("saveContactButton"),
    visitAction: $("visitAction"),
    downloadAction: $("downloadAction"),
    contactAction: $("contactAction"),
    estimateAction: $("estimateAction"),
    visitSection: $("visitSection"),
    contactSection: $("contactSection"),
    slotRuleLabel: $("slotRuleLabel"),
    monthPrevButton: $("monthPrevButton"),
    monthNextButton: $("monthNextButton"),
    monthLabel: $("monthLabel"),
    dayList: $("dayList"),
    slotList: $("slotList"),
    selectedDayLabel: $("selectedDayLabel"),
    selectedSlotLabel: $("selectedSlotLabel"),
    appointmentForm: $("appointmentForm"),
    submitButton: $("submitButton"),
    successPanel: $("successPanel"),
    clientName: $("clientName"),
    clientPhone: $("clientPhone"),
    clientEmail: $("clientEmail"),
    clientMessage: $("clientMessage"),
    estimateAppointmentForm: $("estimateAppointmentForm"),
    estimatePropertyAddress: $("estimatePropertyAddress"),
    estimateClientName: $("estimateClientName"),
    estimateClientPhone: $("estimateClientPhone"),
    estimateClientEmail: $("estimateClientEmail"),
    estimateClientMessage: $("estimateClientMessage"),
    estimateSubmitButton: $("estimateSubmitButton"),
    estimateSuccessPanel: $("estimateSuccessPanel"),
  };

  function addListener(element, eventName, handler) {
    if (element) element.addEventListener(eventName, handler);
  }

  function setHidden(element, hidden) {
    if (!element) return;
    element.classList.toggle("hidden", hidden);
  }

  function getApiBase() {
    const bodyBase = body.getAttribute("data-api-base") || "";
    if (bodyBase.trim()) return bodyBase.trim().replace(/\/+$/, "");
    return `${window.location.origin.replace(/\/+$/, "")}/api`;
  }

  function parseRefFromLocation() {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = (params.get("ref") || "").trim();
    if (fromQuery) return fromQuery;
    const parts = window.location.pathname.split("/").filter(Boolean);
    const rdvIndex = parts.indexOf("rdv");
    if (rdvIndex >= 0 && parts[rdvIndex + 1] === "annonce" && parts[rdvIndex + 2]) {
      return decodeURIComponent(parts[rdvIndex + 2]);
    }
    return "";
  }

  function parseAgencyFromLocation() {
    const params = new URLSearchParams(window.location.search);
    return (params.get("agency") || "")
      .trim()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  function buildQueryRef() {
    const params = new URLSearchParams();
    if (state.ref) params.set("ref", state.ref);
    if (state.agency) params.set("agency", state.agency);
    const query = params.toString();
    return query ? `?${query}` : "";
  }

  function buildListingSheetUrl(annonceId) {
    const id = String(annonceId || "").trim();
    if (!id) return "";
    return `https://gti-immobilier.fr/admin/pdf.php?lang=fr&idann=${encodeURIComponent(id)}&fiche_type=visite&pdf_orientation=P&pdf_template=1`;
  }

  function formatCurrency(value) {
    return typeof value === "number"
      ? new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value)
      : "Prix sur demande";
  }

  function setView(view) {
    body.dataset.view = view;
    setHidden(els.loadingPanel, true);
    setHidden(els.errorPanel, true);
    setHidden(els.homePanel, view !== "home");
    setHidden(els.contentPanel, view !== "content");
  }

  function showError(message) {
    setView("error");
    setHidden(els.errorPanel, false);
    if (els.errorMessage) els.errorMessage.textContent = message || "Erreur inattendue.";
  }

  function setLoading(isLoading) {
    setHidden(els.loadingPanel, !isLoading);
    if (isLoading) {
      setHidden(els.homePanel, true);
      setHidden(els.contentPanel, true);
      setHidden(els.errorPanel, true);
    }
  }

  function renderContactLink(element, value, prefix) {
    if (!element) return;
    const text = String(value || "").trim();
    if (!text) {
      element.textContent = "";
      element.removeAttribute("href");
      element.classList.add("hidden");
      return;
    }
    const isEmail = text.includes("@");
    element.textContent = `${prefix}${text}`;
    element.href = isEmail ? `mailto:${text}` : `tel:${text.replace(/\s+/g, "")}`;
    element.classList.remove("hidden");
  }

  function renderActionLink(element, value, hrefPrefix) {
    if (!element) return;
    const text = String(value || "").trim();
    if (!text) {
      element.classList.add("hidden");
      element.removeAttribute("href");
      return;
    }
    const isEmail = text.includes("@");
    element.href = `${isEmail ? "mailto:" : hrefPrefix}${isEmail ? text : text.replace(/\s+/g, "")}`;
    element.classList.remove("hidden");
  }

  function renderImage(element, url, alt) {
    if (!element) return;
    const safeUrl = String(url || "").trim();
    if (!safeUrl) {
      element.removeAttribute("src");
      element.classList.add("hidden");
      return;
    }
    element.src = safeUrl;
    element.alt = alt;
    element.classList.remove("hidden");
  }

  function configureDownloadAction(context) {
    if (!els.downloadAction) return;
    const href = buildListingSheetUrl(context && context.hektorAnnonceId);
    els.downloadAction.setAttribute("href", href || "#");
    els.downloadAction.classList.toggle("is-disabled", !href);
    els.downloadAction.setAttribute("aria-disabled", href ? "false" : "true");
  }

  function configureEstimateAction() {
    if (!els.estimateAction) return;
    els.estimateAction.setAttribute("href", `./estimation.html${buildQueryRef()}`);
  }

  function buildHeroTitle(context) {
    if (state.mode === "estimation") return context.pageTitle || "Faire estimer mon bien";
    if (state.ref) return "Prendre rendez-vous pour ce bien";
    return "Vos rendez-vous immobiliers";
  }

  function buildHeroCopy(context) {
    if (state.mode === "estimation") {
      return context.pageIntro || "Choisissez un rendez-vous pour parler estimation avec GTI Immobilier.";
    }
    if (state.ref) {
      return "Choisissez un creneau, contactez le conseiller ou ouvrez la fiche du bien.";
    }
    return "Prenez contact avec GTI Immobilier et lancez votre prochaine action en quelques secondes.";
  }

  function renderSharedContext(context) {
    const safeContext = context || {};
    const title = safeContext.title || "GTI Immobilier";
    const phone = safeContext.negociateurMobile || safeContext.negociateurPhone || safeContext.agencePhone || "";
    state.context = safeContext;

    if (els.heroSplashTitle) els.heroSplashTitle.textContent = buildHeroTitle(safeContext);
    if (els.heroSplashCopy) els.heroSplashCopy.textContent = buildHeroCopy(safeContext);
    if (els.commercialName) els.commercialName.textContent = safeContext.commercialName || "Un conseiller GTI Immobilier";
    if (els.commercialNameCard) els.commercialNameCard.textContent = safeContext.commercialName || "Un conseiller GTI Immobilier";
    if (els.agencyName) els.agencyName.textContent = safeContext.agenceNom || "GTI Immobilier";
    if (els.visitActionMeta && state.mode === "listing") {
      const refLabel = safeContext.hektorAnnonceId ? `Ref ${safeContext.hektorAnnonceId}` : "Ref";
      const priceLabel = formatCurrency(safeContext.price);
      els.visitActionMeta.textContent = [safeContext.typeBien || "Bien", priceLabel, refLabel].filter(Boolean).join(" · ");
    }

    renderImage(els.heroImage, safeContext.photoUrl, title);
    renderContactLink(els.commercialPhoneInline, phone, "");
    renderContactLink(els.commercialPhone, phone, "Telephone · ");
    renderContactLink(els.commercialEmail, safeContext.negociateurEmail, "Email · ");
    renderContactLink(els.agencyPhone, safeContext.agencePhone, "Telephone · ");
    renderContactLink(els.agencyEmail, safeContext.agenceEmail, "Email · ");
    renderContactLink(els.callNowButton, phone, "");
    renderActionLink(els.heroCallCta, phone, "tel:");
    renderActionLink(els.homeCallAction, phone, "tel:");
    renderActionLink(els.homeMailAction, safeContext.agenceEmail || safeContext.negociateurEmail, "tel:");

    if (els.homeCallAction && !els.homeCallAction.classList.contains("hidden")) {
      els.homeCallAction.querySelector(".action-subtitle").textContent = phone || "Conseil immediat";
    }
    if (els.homeMailAction && !els.homeMailAction.classList.contains("hidden")) {
      els.homeMailAction.querySelector(".action-subtitle").textContent = (safeContext.agenceEmail || safeContext.negociateurEmail || "Message rapide");
    }
    if (els.heroContact) setHidden(els.heroContact, !state.ref && state.mode !== "estimation");
    if (els.heroSplash) setHidden(els.heroSplash, !!state.ref && state.mode === "listing");
    if (els.callNowButton) {
      els.callNowButton.textContent = "Appeler maintenant";
      setHidden(els.callNowButton, !phone);
    }

    configureDownloadAction(safeContext);
    configureEstimateAction();
    document.title = `${buildHeroTitle(safeContext)} | GTI Immobilier`;
  }

  function groupSlotsByDay(slots) {
    const groups = new Map();
    slots.forEach((slot, index) => {
      const key = slot.dateKey || slot.displayDateLabel || slot.displayDate || String(index);
      if (!groups.has(key)) {
        groups.set(key, {
          dayKey: key,
          dateLabel: slot.displayDateLabel || slot.displayDate || "",
          weekdayLabel: slot.weekdayLabel || "",
          dayNumber: slot.dayNumber || "",
          monthLabel: slot.monthLabel || "",
          slots: [],
        });
      }
      groups.get(key).slots.push({ ...slot, slotIndex: index });
    });
    return Array.from(groups.values());
  }

  function toMonthKey(value) {
    return String(value || "").slice(0, 7);
  }

  function formatDateTimeRange(slot) {
    if (!slot) return "Choisissez un creneau";
    return `${slot.displayDateLabel || slot.displayDate} a ${slot.displayTime}`;
  }

  function selectSlot(index) {
    state.selectedSlot = state.slots[index] || null;
    Array.from(document.querySelectorAll(".slot-button")).forEach((button) => {
      button.classList.toggle("is-selected", Number(button.dataset.index) === index);
    });
    if (els.selectedSlotLabel) els.selectedSlotLabel.textContent = formatDateTimeRange(state.selectedSlot);
    if (els.submitButton) els.submitButton.disabled = !state.selectedSlot;
    if (els.estimateSubmitButton) els.estimateSubmitButton.disabled = !state.selectedSlot;
  }

  function renderSlotsForSelectedDay() {
    if (!els.slotList) return;
    const daySlots = state.slots.filter((slot) => (slot.dateKey || slot.displayDateLabel) === state.selectedDayKey);
    els.slotList.innerHTML = "";
    els.slotList.classList.remove("hidden");
    if (els.selectedDayLabel) {
      const selectedDay = daySlots[0];
      els.selectedDayLabel.textContent = selectedDay ? (selectedDay.displayDateLabel || selectedDay.displayDate || "Jour choisi") : "Choisissez un jour";
    }

    if (!daySlots.length) {
      const empty = document.createElement("p");
      empty.className = "slot-empty";
      empty.textContent = "Aucun creneau pour ce jour.";
      els.slotList.appendChild(empty);
      return;
    }

    daySlots.forEach((slot) => {
      const globalIndex = state.slots.findIndex((item) => item.startAt === slot.startAt);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "slot-button";
      button.dataset.index = String(globalIndex);
      button.disabled = !slot.available;
      if (!slot.available) button.classList.add("is-unavailable");
      button.innerHTML = [
        `<span class="slot-time">${slot.displayTime}</span>`,
        `<span class="slot-meta">${slot.endDisplayTime || ""}</span>`,
        `<span class="slot-status">${slot.available ? "Disponible" : "Indisponible"}</span>`,
      ].join("");
      if (slot.available) button.addEventListener("click", () => selectSlot(globalIndex));
      els.slotList.appendChild(button);
    });
  }

  function selectDay(dayKey) {
    state.selectedDayKey = dayKey;
    state.selectedMonthKey = toMonthKey(dayKey);
    state.selectedSlot = null;
    if (els.selectedSlotLabel) els.selectedSlotLabel.textContent = "Choisissez un creneau";
    if (els.submitButton) els.submitButton.disabled = true;
    if (els.estimateSubmitButton) els.estimateSubmitButton.disabled = true;
    Array.from(document.querySelectorAll(".day-button")).forEach((button) => {
      button.classList.toggle("is-selected", button.dataset.dayKey === dayKey);
    });
    renderSlotsForSelectedDay();
  }

  function monthTitleFromKey(key, sampleDay) {
    if (!key) return sampleDay && sampleDay.monthLabel ? sampleDay.monthLabel : "";
    const parts = key.split("-");
    const monthName = sampleDay && sampleDay.monthLabel ? sampleDay.monthLabel : "";
    return `${monthName.charAt(0).toUpperCase()}${monthName.slice(1)} ${parts[0]}`;
  }

  function weekdayOffset(dateKey) {
    const date = new Date(`${dateKey}T12:00:00`);
    return (date.getDay() + 6) % 7;
  }

  function groupDaysByMonth(days) {
    const groups = new Map();
    days.forEach((day) => {
      const key = String(day.dayKey || "").slice(0, 7);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(day);
    });
    return Array.from(groups.entries());
  }

  function renderCalendar(days) {
    if (!els.dayList) return;
    els.dayList.innerHTML = "";
    const months = groupDaysByMonth(days);
    if (!months.length) return;
    if (!state.selectedMonthKey || !months.some(([monthKey]) => monthKey === state.selectedMonthKey)) {
      state.selectedMonthKey = months[0][0];
    }
    const monthIndex = months.findIndex(([monthKey]) => monthKey === state.selectedMonthKey);
    const monthDays = monthIndex >= 0 ? months[monthIndex][1] : months[0][1];

    if (els.monthLabel) els.monthLabel.textContent = monthTitleFromKey(state.selectedMonthKey, monthDays[0]);
    if (els.monthPrevButton) els.monthPrevButton.disabled = monthIndex <= 0;
    if (els.monthNextButton) els.monthNextButton.disabled = monthIndex >= months.length - 1;

    const weekdays = document.createElement("div");
    weekdays.className = "calendar-weekdays";
    WEEKDAY_SHORT.forEach((label) => {
      const item = document.createElement("span");
      item.className = "calendar-weekday";
      item.textContent = label;
      weekdays.appendChild(item);
    });
    els.dayList.appendChild(weekdays);

    const grid = document.createElement("div");
    grid.className = "calendar-grid";
    const offset = weekdayOffset(monthDays[0] && monthDays[0].dayKey);
    for (let index = 0; index < offset; index += 1) {
      const filler = document.createElement("span");
      filler.className = "calendar-filler";
      grid.appendChild(filler);
    }

    monthDays.forEach((day) => {
      const availableCount = day.slots.filter((slot) => slot.available).length;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "day-button";
      if (day.dayKey === state.selectedDayKey) button.classList.add("is-selected");
      button.dataset.dayKey = day.dayKey;
      button.innerHTML = [
        `<span class="day-number">${day.dayNumber || ""}</span>`,
        `<span class="day-dot${availableCount ? " is-active" : ""}"></span>`,
      ].join("");
      button.addEventListener("click", () => selectDay(day.dayKey));
      grid.appendChild(button);
    });

    els.dayList.appendChild(grid);
  }

  function renderAgenda(rule, slots) {
    state.slots = Array.isArray(slots) ? slots : [];
    state.selectedSlot = null;
    state.selectedDayKey = null;
    if (els.slotRuleLabel) {
      const prefix = state.mode === "estimation" ? "Agenda estimation" : "Agenda de visite";
      els.slotRuleLabel.textContent = `${prefix} · delai mini ${rule.minDelayHours || 36} h`;
    }
    if (els.selectedSlotLabel) els.selectedSlotLabel.textContent = "Choisissez un creneau";
    if (els.submitButton) els.submitButton.disabled = true;
    if (els.estimateSubmitButton) els.estimateSubmitButton.disabled = true;
    if (!els.slotList) return;
    els.slotList.innerHTML = "";
    els.slotList.classList.add("hidden");
    if (els.dayList) els.dayList.innerHTML = "";
    if (els.selectedDayLabel) els.selectedDayLabel.textContent = "Choisissez un jour";

    if (!state.slots.length) {
      const empty = document.createElement("p");
      empty.className = "slot-empty";
      empty.textContent = "Aucun creneau disponible pour le moment.";
      els.slotList.appendChild(empty);
      return;
    }

    const days = groupSlotsByDay(state.slots);
    state.selectedMonthKey = toMonthKey(days[0] && days[0].dayKey);
    renderCalendar(days);
    state.selectedDayKey = null;
  }

  function shiftMonth(direction) {
    const days = groupSlotsByDay(state.slots);
    const months = groupDaysByMonth(days);
    if (!months.length) return;
    const currentIndex = months.findIndex(([monthKey]) => monthKey === state.selectedMonthKey);
    const targetIndex = currentIndex + direction;
    if (targetIndex < 0 || targetIndex >= months.length) return;
    state.selectedMonthKey = months[targetIndex][0];
    state.selectedDayKey = null;
    state.selectedSlot = null;
    if (els.selectedSlotLabel) els.selectedSlotLabel.textContent = "Choisissez un creneau";
    if (els.selectedDayLabel) els.selectedDayLabel.textContent = "Choisissez un jour";
    if (els.slotList) {
      els.slotList.innerHTML = "";
      els.slotList.classList.add("hidden");
    }
    renderCalendar(days);
  }

  function scrollToSection(section) {
    if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function buildVCard(context) {
    const lines = [
      "BEGIN:VCARD",
      "VERSION:3.0",
      `FN:${context.commercialName || "Conseiller GTI Immobilier"}`,
      `ORG:${context.agenceNom || "GTI Immobilier"}`,
      context.negociateurMobile || context.negociateurPhone ? `TEL;TYPE=CELL:${context.negociateurMobile || context.negociateurPhone}` : "",
      context.negociateurEmail ? `EMAIL:${context.negociateurEmail}` : "",
      context.agenceNom ? `NOTE:${context.agenceNom}` : "",
      "END:VCARD",
    ].filter(Boolean);
    return lines.join("\n");
  }

  function downloadBlob(filename, content, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function handleSaveContact() {
    if (!state.context) return;
    const safeRef = String(state.context.hektorAnnonceId || state.context.token || "contact").replace(/[^\w-]+/g, "-");
    downloadBlob(`contact-gti-${safeRef}.vcf`, buildVCard(state.context), "text/vcard;charset=utf-8");
  }

  function buildEstimateEndpoint() {
    return `/public/appointments/estimation/request${buildQueryRef()}`;
  }

  async function fetchJson(path, options) {
    const response = await fetch(`${getApiBase()}${path}`, {
      headers: { Accept: "application/json", ...(options && options.headers ? options.headers : {}) },
      ...options,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || payload.message || "Erreur API");
    }
    return payload;
  }

  function bindPressAnimations() {
    document.querySelectorAll(".action-tile, .button-primary, .button-strong, .button-ghost, .hero-cta").forEach((element) => {
      const clear = () => element.classList.remove("is-pressing");
      element.addEventListener("pointerdown", () => element.classList.add("is-pressing"));
      element.addEventListener("pointerup", clear);
      element.addEventListener("pointerleave", clear);
      element.addEventListener("pointercancel", clear);
    });
  }

  async function bootstrapHome() {
    const payload = await fetchJson("/public/appointments/estimation/bootstrap");
    state.mode = "home";
    renderSharedContext(payload.context || {});
    setView("home");
  }

  async function bootstrapListing() {
    if (!state.ref) {
      await bootstrapHome();
      return;
    }
    const payload = await fetchJson(`/public/appointments/annonce/${encodeURIComponent(state.ref)}/bootstrap`);
    state.mode = "listing";
    renderSharedContext(payload.context || {});
    renderAgenda(payload.rule || {}, Array.isArray(payload.slots) ? payload.slots : []);
    setView("content");
  }

  async function bootstrapEstimation() {
    const payload = await fetchJson(`/public/appointments/estimation/bootstrap${buildQueryRef()}`);
    state.mode = "estimation";
    renderSharedContext(payload.context || {});
    renderAgenda(payload.rule || {}, Array.isArray(payload.slots) ? payload.slots : []);
    setView("content");
  }

  async function handleVisitSubmit(event) {
    event.preventDefault();
    if (!state.selectedSlot || !state.ref) {
      showError("Choisissez d'abord un creneau.");
      return;
    }
    if (els.submitButton) els.submitButton.disabled = true;
    try {
      await fetchJson(`/public/appointments/annonce/${encodeURIComponent(state.ref)}/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clientName: els.clientName.value.trim(),
          clientPhone: els.clientPhone.value.trim(),
          clientEmail: els.clientEmail.value.trim() || null,
          requestedStartAt: state.selectedSlot.startAt,
          requestedEndAt: state.selectedSlot.endAt,
          message: els.clientMessage.value.trim() || null,
        }),
      });
      setHidden(els.successPanel, false);
      setHidden(els.appointmentForm, true);
    } catch (error) {
      showError(error instanceof Error ? error.message : "Envoi impossible");
      if (els.submitButton) els.submitButton.disabled = false;
    }
  }

  async function handleEstimateSubmit(event) {
    event.preventDefault();
    if (!state.selectedSlot) {
      showError("Choisissez d'abord un creneau.");
      return;
    }
    if (els.estimateSubmitButton) els.estimateSubmitButton.disabled = true;
    try {
      await fetchJson(buildEstimateEndpoint(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          propertyAddress: els.estimatePropertyAddress.value.trim(),
          clientName: els.estimateClientName.value.trim(),
          clientPhone: els.estimateClientPhone.value.trim(),
          clientEmail: els.estimateClientEmail.value.trim() || null,
          requestedStartAt: state.selectedSlot.startAt,
          requestedEndAt: state.selectedSlot.endAt,
          message: els.estimateClientMessage.value.trim() || null,
        }),
      });
      setHidden(els.estimateSuccessPanel, false);
      setHidden(els.estimateAppointmentForm, true);
    } catch (error) {
      showError(error instanceof Error ? error.message : "Envoi impossible");
      if (els.estimateSubmitButton) els.estimateSubmitButton.disabled = false;
    }
  }

  async function bootstrap() {
    state.ref = parseRefFromLocation();
    state.agency = parseAgencyFromLocation();
    bindPressAnimations();
    setLoading(true);
    try {
      if (pageType === "estimation") {
        await bootstrapEstimation();
      } else {
        await bootstrapListing();
      }
      setLoading(false);
    } catch (error) {
      showError(error instanceof Error ? error.message : "Erreur de chargement");
    }
  }

  addListener(els.visitAction, "click", () => scrollToSection(els.visitSection));
  addListener(els.contactAction, "click", () => scrollToSection(els.contactSection));
  addListener(els.monthPrevButton, "click", () => shiftMonth(-1));
  addListener(els.monthNextButton, "click", () => shiftMonth(1));
  addListener(els.homeSaveContactButton, "click", handleSaveContact);
  addListener(els.saveContactButton, "click", handleSaveContact);
  addListener(els.appointmentForm, "submit", handleVisitSubmit);
  addListener(els.estimateAppointmentForm, "submit", handleEstimateSubmit);

  bootstrap();
})();
