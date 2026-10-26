// youtrust_client.js -- client de l'API Youtrust (= Yousign v3), tache A.2 « signature en propre ».
//
// DORMANT : aucun handler du worker ne l'appelle encore (decision D2 du 26/10 : le circuit
// Youtrust ne s'allume qu'a la coupure). Seul l'essai `essai_youtrust_sandbox.js` l'utilise.
// Audit et architecture : notice/AUDIT_SIGNATURE_YOUTRUST_2026-10-26.md.
//
// - La cle vient de YOUTRUST_API_KEY (Console/.env), jamais du navigateur.
// - L'adresse vient de YOUTRUST_BASE_URL ; par defaut la SANDBOX. La production exige de la
//   poser explicitement : on ne bascule pas par accident sur des envois factures.
// - Aucune dependance : fetch / FormData / Blob de Node >= 18.

const crypto = require("crypto");

const SANDBOX_URL = "https://api-sandbox.yousign.app/v3";
const PRODUCTION_URL = "https://api.yousign.app/v3";

class YoutrustError extends Error {
  constructor(message, { status, body, method, path } = {}) {
    super(message);
    this.name = "YoutrustError";
    this.status = status;
    this.body = body;
    this.method = method;
    this.path = path;
  }
}

function attendre(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function creerClientYoutrust(options = {}) {
  const apiKey = String(options.apiKey || process.env.YOUTRUST_API_KEY || "").trim();
  const baseUrl = String(options.baseUrl || process.env.YOUTRUST_BASE_URL || SANDBOX_URL).replace(/\/+$/, "");
  const maxTentatives429 = Number(options.maxTentatives429 || 3);
  if (!apiKey) throw new YoutrustError("YOUTRUST_API_KEY absente (Console/.env)");
  const sandbox = baseUrl === SANDBOX_URL;

  // Un appel. Sur 429, on attend le Ratelimit-Reset annonce (60 s au plus) puis on rejoue ;
  // tout autre statut hors 2xx leve une YoutrustError qui porte le corps de la reponse.
  async function requete(method, path, { json, form, query, binaire } = {}) {
    const url = new URL(baseUrl + path);
    for (const [k, v] of Object.entries(query || {})) {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    }
    const headers = { Authorization: `Bearer ${apiKey}`, Accept: binaire ? "*/*" : "application/json" };
    let body;
    if (json !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(json);
    } else if (form) {
      body = form; // FormData : fetch pose lui-meme la frontiere multipart
    }
    for (let tentative = 1; ; tentative += 1) {
      const res = await fetch(url, { method, headers, body });
      if (res.status === 429 && tentative <= maxTentatives429) {
        const reset = Number(res.headers.get("ratelimit-reset")) || 10;
        await attendre(Math.min(reset, 60) * 1000 + 500);
        continue;
      }
      if (!res.ok) {
        const texte = await res.text().catch(() => "");
        let corps = texte;
        try { corps = JSON.parse(texte); } catch (_) { /* corps non JSON, garde le texte */ }
        throw new YoutrustError(`Youtrust ${method} ${path} -> HTTP ${res.status}`, {
          status: res.status, body: corps, method, path,
        });
      }
      if (binaire) {
        return {
          buffer: Buffer.from(await res.arrayBuffer()),
          contentType: res.headers.get("content-type") || "",
        };
      }
      if (res.status === 204) return null;
      const texte = await res.text();
      return texte ? JSON.parse(texte) : null;
    }
  }

  return {
    baseUrl,
    sandbox,
    requete,

    // --- demande de signature ---------------------------------------------------------
    creerDemande: (payload) => requete("POST", "/signature_requests", { json: payload }),
    lireDemande: (srId) => requete("GET", `/signature_requests/${srId}`),
    activer: (srId) => requete("POST", `/signature_requests/${srId}/activate`),
    // reason : contractualization_aborted | errors_in_document | other
    annuler: (srId, reason = "other", customNote = null) =>
      requete("POST", `/signature_requests/${srId}/cancel`, {
        json: { reason, ...(customNote ? { custom_note: customNote } : {}) },
      }),
    supprimerBrouillon: (srId) => requete("DELETE", `/signature_requests/${srId}`),

    // --- documents --------------------------------------------------------------------
    // parseAnchors : Youtrust lit les ancres {{sN|signature|l|h}} du PDF a l'activation.
    ajouterDocument: (srId, { buffer, filename, nature = "signable_document", parseAnchors = false }) => {
      const form = new FormData();
      form.append("file", new Blob([buffer], { type: "application/pdf" }), filename);
      form.append("nature", nature);
      if (parseAnchors) form.append("parse_anchors", "true");
      return requete("POST", `/signature_requests/${srId}/documents`, { form });
    },
    listerChamps: (srId, docId) => requete("GET", `/signature_requests/${srId}/documents/${docId}/fields`),
    // version : "completed" (signe) ou "current" ; un seul document -> PDF, sinon ZIP
    telechargerDocuments: (srId, version = "completed") =>
      requete("GET", `/signature_requests/${srId}/documents/download`, { query: { version }, binaire: true }),

    // --- signataires ------------------------------------------------------------------
    ajouterSignataire: (srId, payload) => requete("POST", `/signature_requests/${srId}/signers`, { json: payload }),
    lireSignataire: (srId, signerId) => requete("GET", `/signature_requests/${srId}/signers/${signerId}`),
    // possible seulement si la demande est ongoing ET le signataire « notified »
    relancerSignataire: (srId, signerId) =>
      requete("POST", `/signature_requests/${srId}/signers/${signerId}/send_reminder`),
    telechargerAuditTrail: (srId, signerId) =>
      requete("GET", `/signature_requests/${srId}/signers/${signerId}/audit_trails/download`, { binaire: true }),
  };
}

// Verification d'un webhook : en-tete X-Yousign-Signature-256 = "sha256=" + HMAC hex du CORPS BRUT.
// A appeler sur les octets recus, jamais sur un JSON re-serialise.
function verifierSignatureWebhook(corpsBrut, enTete, secret) {
  if (!enTete || !secret) return false;
  const attendu = "sha256=" + crypto.createHmac("sha256", secret).update(corpsBrut).digest("hex");
  const a = Buffer.from(String(enTete), "utf8");
  const b = Buffer.from(attendu, "utf8");
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

module.exports = {
  creerClientYoutrust,
  verifierSignatureWebhook,
  YoutrustError,
  SANDBOX_URL,
  PRODUCTION_URL,
};
