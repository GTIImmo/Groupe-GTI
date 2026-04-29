(function () {
  const $ = (id) => document.getElementById(id);
  const state = {
    ref: null,
    context: null,
    slots: [],
    selectedSlot: null,
    selectedDayKey: null,
  };
  const WEEKDAY_SHORT = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"];

  const els = {
    loadingPanel: $("loadingPanel"),
    errorPanel: $("errorPanel"),
    errorMessage: $("errorMessage"),
    contentPanel: $("contentPanel"),
    listingPhoto: $("listingPhoto"),
    listingTitle: $("listingTitle"),
    listingCity: $("listingCity"),
    listingType: $("listingType"),
    listingPrice: $("listingPrice"),
    commercialName: $("commercialName"),
    commercialPhone: $("commercialPhone"),
    commercialEmail: $("commercialEmail"),
    agencyName: $("agencyName"),
    agencyPhone: $("agencyPhone"),
    agencyEmail: $("agencyEmail"),
    slotRuleLabel: $("slotRuleLabel"),
    dayList: $("dayList"),
    slotList: $("slotList"),
    selectedSlotLabel: $("selectedSlotLabel"),
    appointmentForm: $("appointmentForm"),
    submitButton: $("submitButton"),
    successPanel: $("successPanel"),
    clientName: $("clientName"),
    clientPhone: $("clientPhone"),
    clientEmail: $("clientEmail"),
    clientMessage: $("clientMessage"),
  };

  function getApiBase() {
    const bodyBase = document.body.getAttribute("data-api-base") || "";
    if (bodyBase.trim()) return bodyBase.trim().replace(/\/+$/, "");
    return `${window.location.origin.replace(/\/+$/, "")}/api`;
  }

  function parseRefFromLocation() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    const rdvIndex = parts.indexOf("rdv");
    if (rdvIndex >= 0 && parts[rdvIndex + 1] === "annonce" && parts[rdvIndex + 2]) {
      return decodeURIComponent(parts[rdvIndex + 2]);
    }
    const params = new URLSearchParams(window.location.search);
    return params.get("ref") || "";
  }

  function showError(message) {
    els.loadingPanel.classList.add("hidden");
    els.contentPanel.classList.add("hidden");
    els.errorPanel.classList.remove("hidden");
    els.errorMessage.textContent = message || "Erreur inattendue.";
  }

  function formatDateTimeRange(slot) {
    if (!slot) return "Choisissez un creneau";
    return `${slot.displayDateLabel || slot.displayDate} a ${slot.displayTime}`;
  }

  function renderContext(context) {
    const price = typeof context.price === "number"
      ? new Intl.NumberFormat("fr-FR", {
        style: "currency",
        currency: "EUR",
        maximumFractionDigits: 0,
      }).format(context.price)
      : "Prix sur demande";

    els.listingTitle.textContent = context.title || `Annonce ${context.hektorAnnonceId}`;
    els.listingCity.textContent = context.ville || "Ville non renseignee";
    els.listingType.textContent = context.typeBien || "Bien immobilier";
    els.listingPrice.textContent = price;
    els.commercialName.textContent = context.commercialName || "-";
    els.agencyName.textContent = context.agenceNom || "-";
    renderContactLink(els.commercialPhone, context.negociateurMobile || context.negociateurPhone, "Tel. ");
    renderContactLink(els.commercialEmail, context.negociateurEmail, "");
    renderContactLink(els.agencyPhone, context.agencePhone, "Tel. ");
    renderContactLink(els.agencyEmail, context.agenceEmail, "");

    if (context.photoUrl) {
      els.listingPhoto.src = context.photoUrl;
      els.listingPhoto.classList.remove("hidden");
    } else {
      els.listingPhoto.removeAttribute("src");
      els.listingPhoto.classList.add("hidden");
    }
  }

  function renderContactLink(element, value, prefix) {
    const text = (value || "").trim();
    if (!text) {
      element.textContent = "";
      element.classList.add("hidden");
      element.removeAttribute("href");
      return;
    }
    const isEmail = text.includes("@");
    element.textContent = `${prefix}${text}`;
    element.href = isEmail ? `mailto:${text}` : `tel:${text.replace(/\s+/g, "")}`;
    element.classList.remove("hidden");
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

  function selectSlot(index) {
    state.selectedSlot = state.slots[index] || null;
    Array.from(els.slotList.querySelectorAll(".slot-button")).forEach((button) => {
      button.classList.toggle("is-selected", Number(button.dataset.index) === index);
    });
    els.selectedSlotLabel.textContent = formatDateTimeRange(state.selectedSlot);
    els.submitButton.disabled = !state.selectedSlot;
  }

  function selectDay(dayKey) {
    state.selectedDayKey = dayKey;
    state.selectedSlot = null;
    els.selectedSlotLabel.textContent = "Choisissez un creneau";
    els.submitButton.disabled = true;
    Array.from(els.dayList.querySelectorAll(".day-button")).forEach((button) => {
      button.classList.toggle("is-selected", button.dataset.dayKey === dayKey);
    });
    renderSlotsForSelectedDay();
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

  function monthTitleFromKey(key, sampleDay) {
    if (!key) return sampleDay?.monthLabel || "";
    const [yearText, monthText] = key.split("-");
    const year = Number(yearText);
    const monthIndex = Number(monthText) - 1;
    const monthName = sampleDay?.monthLabel || "";
    return `${monthName.charAt(0).toUpperCase()}${monthName.slice(1)} ${year}`;
  }

  function weekdayOffset(dateKey) {
    const date = new Date(`${dateKey}T12:00:00`);
    return (date.getDay() + 6) % 7;
  }

  function renderCalendar(days) {
    els.dayList.innerHTML = "";
    groupDaysByMonth(days).forEach(([monthKey, monthDays]) => {
      const month = document.createElement("section");
      month.className = "calendar-month";

      const title = document.createElement("h3");
      title.className = "calendar-title";
      title.textContent = monthTitleFromKey(monthKey, monthDays[0]);
      month.appendChild(title);

      const weekdays = document.createElement("div");
      weekdays.className = "calendar-weekdays";
      WEEKDAY_SHORT.forEach((label) => {
        const item = document.createElement("span");
        item.className = "calendar-weekday";
        item.textContent = label;
        weekdays.appendChild(item);
      });
      month.appendChild(weekdays);

      const grid = document.createElement("div");
      grid.className = "calendar-grid";
      const offset = weekdayOffset(monthDays[0]?.dayKey);
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
        button.dataset.dayKey = day.dayKey;
        button.innerHTML = [
          `<span class="day-name">${day.weekdayLabel || ""}</span>`,
          `<span class="day-number">${day.dayNumber || ""}</span>`,
          `<span class="day-count">${availableCount} libre${availableCount > 1 ? "s" : ""}</span>`,
        ].join("");
        button.addEventListener("click", () => selectDay(day.dayKey));
        grid.appendChild(button);
      });

      month.appendChild(grid);
      els.dayList.appendChild(month);
    });
  }

  function renderSlotsForSelectedDay() {
    const daySlots = state.slots.filter((slot) => (slot.dateKey || slot.displayDateLabel) === state.selectedDayKey);
    els.slotList.innerHTML = "";

    if (!daySlots.length) {
      const empty = document.createElement("p");
      empty.className = "panel-intro";
      empty.textContent = "Aucun creneau disponible pour ce jour.";
      els.slotList.appendChild(empty);
      return;
    }

    daySlots.forEach((slot, index) => {
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
      if (slot.available) {
        button.addEventListener("click", () => selectSlot(globalIndex));
      }
      els.slotList.appendChild(button);
    });
  }

  function renderAgenda(rule, slots) {
    state.slots = Array.isArray(slots) ? slots : [];
    state.selectedSlot = null;
    els.slotRuleLabel.textContent = `Agenda de visite - delai mini ${rule.minDelayHours} h`;
    els.dayList.innerHTML = "";
    els.slotList.innerHTML = "";
    els.selectedSlotLabel.textContent = "Choisissez un creneau";
    els.submitButton.disabled = true;

    if (!state.slots.length) {
      const empty = document.createElement("p");
      empty.className = "panel-intro";
      empty.textContent = "Aucun creneau disponible pour le moment.";
      els.slotList.appendChild(empty);
      return;
    }

    const days = groupSlotsByDay(state.slots);
    renderCalendar(days);
    state.selectedDayKey = days[0]?.dayKey || null;
    if (state.selectedDayKey) {
      selectDay(state.selectedDayKey);
    }
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

  async function bootstrap() {
    state.ref = parseRefFromLocation();
    els.loadingPanel.classList.remove("hidden");
    if (!state.ref) {
      showError("Reference annonce introuvable dans l'URL.");
      return;
    }
    try {
      const bootstrapPayload = await fetchJson(`/public/appointments/annonce/${encodeURIComponent(state.ref)}/bootstrap`);
      state.context = bootstrapPayload.context || null;
      renderContext(bootstrapPayload.context || {});
      renderAgenda(bootstrapPayload.rule || {}, Array.isArray(bootstrapPayload.slots) ? bootstrapPayload.slots : []);
      els.loadingPanel.classList.add("hidden");
      els.contentPanel.classList.remove("hidden");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Erreur de chargement");
    }
  }

  els.appointmentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.selectedSlot) {
      showError("Choisissez d'abord un creneau.");
      return;
    }
    els.submitButton.disabled = true;
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
      els.successPanel.classList.remove("hidden");
      els.appointmentForm.classList.add("hidden");
    } catch (error) {
      showError(error instanceof Error ? error.message : "Envoi impossible");
      els.submitButton.disabled = false;
    }
  });

  bootstrap();
})();
