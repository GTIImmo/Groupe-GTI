(function () {
  const $ = (id) => document.getElementById(id);
  const state = {
    ref: null,
    context: null,
    slots: [],
    selectedSlot: null,
  };

  const els = {
    loadingPanel: $("loadingPanel"),
    errorPanel: $("errorPanel"),
    errorMessage: $("errorMessage"),
    contentPanel: $("contentPanel"),
    listingTitle: $("listingTitle"),
    listingMeta: $("listingMeta"),
    commercialName: $("commercialName"),
    agencyName: $("agencyName"),
    dossierNumber: $("dossierNumber"),
    mandatNumber: $("mandatNumber"),
    slotRuleLabel: $("slotRuleLabel"),
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
    return `${slot.displayDate} a ${slot.displayTime}`;
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
    els.listingMeta.textContent = [context.address, context.ville, price].filter(Boolean).join(" / ");
    els.commercialName.textContent = context.commercialName || "-";
    els.agencyName.textContent = context.agenceNom || "-";
    els.dossierNumber.textContent = context.numeroDossier || "-";
    els.mandatNumber.textContent = context.numeroMandat || "-";
  }

  function selectSlot(index) {
    state.selectedSlot = state.slots[index] || null;
    Array.from(els.slotList.querySelectorAll(".slot-button")).forEach((button) => {
      button.classList.toggle("is-selected", Number(button.dataset.index) === index);
    });
    els.selectedSlotLabel.textContent = formatDateTimeRange(state.selectedSlot);
    els.submitButton.disabled = !state.selectedSlot;
  }

  function groupSlotsByDate(slots) {
    const groups = new Map();
    slots.forEach((slot, index) => {
      const key = slot.displayDate || "Autre";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push({ slot, index });
    });
    return groups;
  }

  function renderSlots(rule, slots) {
    state.slots = Array.isArray(slots) ? slots : [];
    els.slotRuleLabel.textContent = `Delai mini ${rule.minDelayHours} h`;
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

    const groups = groupSlotsByDate(state.slots);
    groups.forEach((entries, dateLabel) => {
      const group = document.createElement("section");
      group.className = "slot-group";

      const title = document.createElement("span");
      title.className = "group-label";
      title.textContent = dateLabel;
      group.appendChild(title);

      const row = document.createElement("div");
      row.className = "slot-row";

      entries.forEach(({ slot, index }) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "slot-button";
        button.dataset.index = String(index);
        button.innerHTML = `<span class="slot-time">${slot.displayTime}</span><span class="slot-meta">Creneau indicatif</span>`;
        button.addEventListener("click", () => selectSlot(index));
        row.appendChild(button);
      });

      group.appendChild(row);
      els.slotList.appendChild(group);
    });
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
      const context = await fetchJson(`/public/appointments/annonce/${encodeURIComponent(state.ref)}`);
      const slotsPayload = await fetchJson(`/public/appointments/annonce/${encodeURIComponent(state.ref)}/slots`);
      state.context = context;
      renderContext(context);
      renderSlots(slotsPayload.rule, slotsPayload.slots);
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
