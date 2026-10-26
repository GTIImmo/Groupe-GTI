// Repères Youtrust (« Smart Anchors ») des PDF à signer — tâche A.2, lot 2.
// Plan : notice/PLAN_DEV_SIGNATURE_YOUTRUST_2026-10-26.md.
//
// Ils ne sont écrits QUE quand l'interrupteur `signature_youtrust` est allumé, et seulement dans
// le HTML envoyé au worker pour fabriquer le PDF : l'aperçu à l'écran, et le PDF tant que
// l'interrupteur est éteint, restent ceux d'aujourd'hui.
//
// Règles mesurées au lot 1 (essai sandbox du 26/10) :
//  - un repère tient sur UNE ligne, en Arial 10 px, de la couleur du fond de la case (invisible) ;
//  - Youtrust pose le champ au coin haut-gauche du repère ;
//  - l'index sN suit l'ORDRE de création des signataires : mandants 1..N, puis le mandataire en
//    N+1. Un repère sans signataire est ignoré EN SILENCE : le worker devra contrôler
//    « nb de champs = nb de signataires » (lot 4) ;
//  - les repères doivent être posés APRÈS le remplacement des {{…}} du gabarit du mandat, sinon
//    ce remplacement les efface.

export const SIGNATURE_LARGEUR = 150
export const SIGNATURE_HAUTEUR = 45

// Une mention est apposée par Youtrust au moment où le signataire signe (il ne la tape pas).
export const MENTION_MANDAT = 'Bon pour mandat'
export const MENTION_AVENANT = 'Bon pour accord'

// Fond des cases de signature du mandat (.mandat-signature-area) et de l'avenant.
export const FOND_CASE_SIGNATURE = '#fafbfc'

// Les séparateurs du motif Youtrust ne doivent jamais apparaître dans un texte libre.
function texteDeRepere(texte: string) {
  return String(texte).replace(/[|{}<>]/g, ' ').replace(/\s+/g, ' ').trim()
}

export function repereSignature(index: number) {
  return `{{s${index}|signature|${SIGNATURE_LARGEUR}|${SIGNATURE_HAUTEUR}}}`
}

export function repereMention(index: number, mention: string) {
  return `{{s${index}|mention|${texteDeRepere(mention)}|mention_s${index}}}`
}

// Le repère, invisible, posé au coin haut-gauche de son conteneur (qui doit être en position
// relative). Le style est en ligne : il ne dépend d'aucune feuille du gabarit.
export function repereHtml(repere: string, fond = FOND_CASE_SIGNATURE) {
  return `<span class="yt-repere" style="position:absolute;left:4px;top:4px;right:auto;bottom:auto;color:${fond};font-family:Arial,Helvetica,sans-serif;font-size:10px;line-height:1;letter-spacing:0;text-transform:none;white-space:nowrap">${repere}</span>`
}

// Les deux repères d'une case de MANDANT : la mention (dans sa propre bande) et la signature.
export function zoneMentionHtml(index: number, mention: string, fond = FOND_CASE_SIGNATURE) {
  return `<div class="yt-mention" style="position:relative;height:18px;margin-bottom:3px;background:${fond};border-radius:3px">${repereHtml(repereMention(index, mention), fond)}</div>`
}
