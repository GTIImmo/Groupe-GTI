// RECRUTEMENT E1 (24/11/2026) — écrire à UN candidat : les modèles, le montage de l'e-mail (texte + HTML), l'envoi.
// Proposition validée : notice/RECRUTEMENT_EMAILS_AUDIT_ET_PROPOSITION_2026-11-24.md (§2 A) ; maquette, planche 1.
// Texte validé sur le fond le 24/11 : notice/RECRUTEMENT_MODELE_EMAIL_PREMIER_CONTACT_2026-11-24.md.
// ⛔ Rien ne part sans le clic de l'administrateur. L'envoi passe par la route Gmail EXISTANTE du serveur
//   (/google-workspace/gmail/send : clé Workspace, journal app_google_workspace_action_log), depuis SA boîte.
// ⛔ L'envoi depuis l'app dort derrière l'interrupteur `recrutement_envoi_email` ; éteint, la fenêtre ouvre la
//   messagerie de l'administrateur avec le texte prêt (mailto), comme avant.
import { lienPieceEmail, sendGoogleWorkspaceCrmEmail, type GmailPieceOrdinateur } from './api'
import { nomReseau, type Candidat, type Detail } from './recrutement'
import { hasSupabaseEnv, supabase } from './supabase'

export type ModeleCle = 'premier' | 'relance' | 'rdv' | 'libre'
export type Modele = { cle: ModeleCle; nom: string; objet: string; texte: string }

// {cle} = rempli depuis la fiche ; [EN MAJUSCULES] = à compléter à la main (l'envoi reste bloqué tant qu'il en reste).
const SIGNATURE = 'Bien cordialement,\n{expediteur}\nGTI Immobilier'
export const MODELES: Modele[] = [
  {
    cle: 'premier', nom: 'Premier contact',
    objet: 'Une proposition de collaboration près de chez vous — GTI Immobilier',
    texte: 'Bonjour {prenom},\n\nJe suis {expediteur}, chez GTI Immobilier, un groupe de 17 agences dans la Loire, la Haute-Loire, '
      + 'le Puy-de-Dôme et l\'Ardèche. Nous cherchons des agents commerciaux autour de notre agence de {agence_proche}, et votre '
      + 'parcours dans l\'immobilier nous a donné envie de vous écrire.\n\n[CE QUE GTI PROPOSE]\n\nSi l\'idée vous intéresse, je vous '
      + 'propose un échange de vingt minutes, au téléphone ou à l\'agence de {agence_proche}, au moment qui vous convient. Et si ce '
      + 'n\'est pas le moment, une simple réponse suffit.\n\n' + SIGNATURE,
  },
  {
    cle: 'relance', nom: 'Relance',
    objet: 'Notre proposition de collaboration — GTI Immobilier',
    texte: 'Bonjour {prenom},\n\nJe me permets de revenir vers vous au sujet de mon précédent message : nous cherchons toujours des '
      + 'agents commerciaux autour de notre agence de {agence_proche}.\n\nSi vous avez vingt minutes dans les prochains jours, '
      + 'j\'aurais plaisir à en parler avec vous, au téléphone ou à l\'agence. Et si ce n\'est pas le moment, dites-le-moi simplement.\n\n'
      + SIGNATURE,
  },
  {
    cle: 'rdv', nom: 'Proposer un rendez-vous',
    objet: 'Notre rendez-vous — GTI Immobilier',
    texte: 'Bonjour {prenom},\n\nMerci pour votre retour. Je vous propose de nous retrouver [JOUR ET HEURE], à l\'agence de '
      + '{agence_proche} ou au téléphone, comme vous préférez.\n\nDites-moi si cela vous convient ; sinon, proposez-moi le moment qui '
      + 'vous arrange.\n\n' + SIGNATURE,
  },
  { cle: 'libre', nom: 'Message libre', objet: '', texte: 'Bonjour {prenom},\n\n\n\n' + SIGNATURE },
]

export function remplir(texte: string, valeurs: Record<string, string>): string {
  return texte.replace(/\{([a-z_]+)\}/g, (tout, cle: string) => (cle in valeurs ? valeurs[cle] : tout))
}

/** Les passages encore « à compléter » : [EN CROCHETS], ou une case {…} restée vide. */
export function trous(texte: string): string[] {
  return [...new Set([...(texte.match(/\[[^\]\n]{2,60}\]/g) ?? []), ...(texte.match(/\{[a-z_]+\}/g) ?? [])])]
}

// ─── le bloc d'information (article 14 du RGPD), texte validé le 24/11 ───

export type Reglages = { envoi: boolean; adressePostale: string | null; contactDonnees: string | null }

/** D'où vient sa coordonnée, en clair ; null = elle nous l'a donnée elle-même (pas de bloc « source »). */
export function sourceDe(d: Detail): string | null {
  const f = d.fiche
  if (f.origine === 'collecte') {
    return f.reseau === 'registre' ? 'l\'annuaire public des entreprises (registre national)' : `l'annuaire public des conseillers ${nomReseau(f.reseau)}`
  }
  return /annuaire/i.test(f.source_contact ?? '') ? 'un annuaire public' : null
}

/** Le bloc complet est dû au premier contact d'une personne trouvée dans un annuaire, tant qu'elle n'est pas informée. */
export function blocDu(d: Detail): boolean {
  return sourceDe(d) != null && !d.suivi?.info_donnee_le
}

export function blocTexte(d: Detail, r: Reglages): string {
  const source = sourceDe(d)
  const lien = d.fiche.origine === 'collecte' && d.fiche.url ? ` (${d.fiche.url})` : ''
  if (!blocDu(d)) return 'Vous préférez que nous ne vous écrivions plus ? Répondez simplement « Ne plus me contacter ».'
  return [
    'Pourquoi vous recevez ce message, et ce que nous savons de vous',
    `• Nous avons trouvé vos coordonnées professionnelles sur ${source}${lien}, où elles sont affichées publiquement.`,
    '• Nous gardons seulement : vos nom et prénom, votre commune, votre réseau, les coordonnées professionnelles affichées et, '
      + 's\'il existe, votre numéro SIREN avec les informations publiques du registre des entreprises.',
    `• Responsable : GTI Immobilier, ${r.adressePostale ?? '[ADRESSE POSTALE DE GTI]'}. But : vous proposer une collaboration comme `
      + 'agent commercial. Base : notre intérêt légitime à recruter dans notre métier.',
    '• Seuls les responsables du recrutement chez GTI y ont accès. Elles sont hébergées chez nos prestataires techniques (base de '
      + 'données et serveur), qui n\'en font rien d\'autre. Rien n\'est vendu ni transmis à qui que ce soit.',
    '• Sans échange avec vous, tout est effacé au bout de trois ans (et de nos copies de sauvegarde un an après au plus).',
    '• À tout moment, vous pouvez voir ces informations, les faire corriger ou effacer, ou refuser tout nouveau contact : répondez '
      + `simplement « Ne plus me contacter », ou écrivez à ${r.contactDonnees ?? '[ADRESSE DE CONTACT POUR LES DONNÉES]'}. Vous pouvez `
      + 'aussi vous adresser à la CNIL (cnil.fr).',
  ].join('\n')
}

// ─── le montage ───

const echapper = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const paragraphes = (texte: string, style: string) => texte.trim().split(/\n{2,}/)
  .map((p) => `<p style="${style}">${echapper(p).replace(/\n/g, '<br>')}</p>`).join('')

export function texteComplet(corps: string, bloc: string): string {
  return `${corps.trim()}\n\n—\n${bloc}`
}

/** Le HTML tel qu'elle le recevra : habillage GTI simple, styles en ligne (Gmail ignore les feuilles de style). */
export function html(corps: string, bloc: string): string {
  return '<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
    + '<body style="margin:0;background:#f6f7f8;font-family:Arial,Helvetica,sans-serif;color:#222323">'
    + '<div style="padding:20px 12px"><div style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid #e2e5e6;border-radius:12px;overflow:hidden">'
    + '<div style="background:#222323;color:#ffffff;padding:14px 20px;font-weight:bold;font-size:16px">GTI Immobilier</div>'
    + `<div style="padding:20px;font-size:14px;line-height:1.6">${paragraphes(corps, 'margin:0 0 12px')}</div>`
    + `<div style="padding:14px 20px 18px;border-top:1px solid #eef0f1;font-size:12px;line-height:1.55;color:#5c6163">${paragraphes(bloc, 'margin:0 0 6px')}</div>`
    + '</div></div></body></html>'
}

// ─── les réglages et l'expéditeur ───

const enLocal = () => !hasSupabaseEnv || !supabase

/** Une valeur de app_setting TELLE QUELLE (loadAppSettingValeur la met en minuscules : pas pour une adresse). */
async function lireReglage(cle: string): Promise<string | null> {
  if (!supabase) return null
  try {
    const { data, error } = await supabase.from('app_setting').select('value').eq('key', cle).maybeSingle()
    if (error || !data) return null
    return String((data as { value?: unknown }).value ?? '').trim() || null
  } catch {
    return null
  }
}

export async function lireReglages(): Promise<Reglages> {
  // (sans crochets : des crochets seraient pris pour un passage « à compléter », et l'envoi resterait bloqué)
  if (enLocal()) return { envoi: true, adressePostale: 'adresse postale de GTI (essai local)', contactDonnees: 'donnees@exemple.invalid' }
  const [envoi, adressePostale, contactDonnees] = await Promise.all([
    lireReglage('recrutement_envoi_email'), lireReglage('recrutement_email_adresse_postale'), lireReglage('recrutement_email_contact_donnees'),
  ])
  return { envoi: ['on', 'admin', 'true', '1', 'yes'].includes((envoi ?? '').toLowerCase()), adressePostale, contactDonnees }
}

export type Expediteur = { email: string; nom: string }
export async function lireExpediteur(): Promise<Expediteur | null> {
  if (enLocal()) return { email: 'vous@gti-immobilier.fr', nom: 'Votre nom' }
  try {
    const { data } = await supabase!.auth.getUser()
    const u = data?.user
    if (!u?.email) return null
    const { data: p } = await supabase!.from('app_user_profile').select('display_name').eq('id', u.id).maybeSingle()
    const nom = String((p as { display_name?: unknown } | null)?.display_name ?? '').trim()
    return { email: u.email, nom: nom || u.email }
  } catch {
    return null
  }
}

// ─── l'envoi ───

export async function envoyer(p: {
  de: Expediteur; a: string; objet: string; corps: string; bloc: string; pieces: GmailPieceOrdinateur[]; reseau: string; identifiant: string
}): Promise<void> {
  if (enLocal()) return
  const attachments = await Promise.all(p.pieces.map((piece) => lienPieceEmail(piece)))
  const r = await sendGoogleWorkspaceCrmEmail({
    subjectEmail: p.de.email, to: [p.a], subject: p.objet.trim(),
    bodyText: texteComplet(p.corps, p.bloc), bodyHtml: html(p.corps, p.bloc),
    fromName: `${p.de.nom} — GTI Immobilier`.slice(0, 120), replyTo: p.de.email, attachments,
    relatedEntityType: 'recrutement', relatedEntityId: `${p.reseau}/${p.identifiant}`.slice(0, 120),
  })
  if (!r?.ok) throw new Error('Gmail a refusé l’envoi.')
}

/** Les valeurs des cases {…} pour un candidat. */
export function valeursPour(d: Detail, candidat: Candidat | null, de: Expediteur | null): Record<string, string> {
  const prenom = (d.carnet.find((c) => c.champ === 'prenom')?.valeur ?? d.fiche.prenom ?? '').trim()
  return {
    prenom: prenom || '{prenom}',
    agence_proche: candidat?.agence_gti_proche || '{agence_proche}',
    expediteur: de?.nom || '{expediteur}',
  }
}
