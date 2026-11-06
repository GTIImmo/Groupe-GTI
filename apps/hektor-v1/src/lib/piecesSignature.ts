// A.2 P8-4 (06/11/2026) -- LES PIÈCES D'UN DOCUMENT SIGNÉ que l'écran peut ouvrir au coffre : l'original non signé, et
// les preuves (Youtrust : une preuve PDF par signataire ; ImmoSign : le ZIP des preuves et le ZIP de la procédure).
// Tout est rangé dans le DOSSIER du document au coffre (`annonces/<annonce>/documents/<id>/…`) : la règle de lecture
// l'ouvre depuis patch_a2_p8_4_preuves_coffre_2026-11-06.sql. Une pièce sans chemin au coffre (le serveur seul : 40 ZIP
// ImmoSign au 06/11) n'est PAS proposée. L'original n'a pas de chemin enregistré : il est DÉDUIT, et 76 signés sur 466
// ne l'ont pas au coffre -- la fenêtre vérifie donc la présence de chaque pièce avant d'offrir le geste (api.ts piecesAuCoffre).
// L'original : mesuré le 06/11, 390 signés sur 390 qui l'ont au coffre le rangent à la racine du dossier, sous le NOM de
// leur copie serveur (`metadata_json.local_archive_path`, qui reste l'original quand le signé arrive).

export type PieceSignature = {
  cle: string
  libelle: string
  storagePath: string
  bucket: string | null
  genre: 'original' | 'preuve' | 'procedure'
  format: 'pdf' | 'zip'
  signataireIndex: number | null
}

type FichierRange = { storage_path?: string | null; storage_bucket?: string | null; filename?: string | null; index?: number | null; role?: string | null }
type Metadonnees = {
  local_archive_path?: string | null
  signed_document?: { provider?: string | null; storage_path?: string | null; storage_bucket?: string | null; preuves?: FichierRange[] | null } | null
  immosign_files?: { proofs_zip?: FichierRange | null; procedure_zip?: FichierRange | null } | null
}

const ROLE: Record<string, string> = { mandant: 'mandant', mandataire: 'mandataire (négociateur)' }
const nomDeFichier = (chemin: string) => chemin.split(/[\\/]/).pop() ?? ''

export function piecesDeSignature(document: { storage_path?: string | null; metadata_json?: unknown }): PieceSignature[] {
  const md = (document.metadata_json ?? {}) as Metadonnees
  const sd = md.signed_document
  if (!sd) return []
  const bucket = sd.storage_bucket ?? null
  const pieces: PieceSignature[] = []

  // L'original non signé : le signé est rangé sous …/<id>/signed/<nom> ; l'original à la racine du même dossier.
  const cheminSigne = String(document.storage_path ?? sd.storage_path ?? '')
  const nomOriginal = md.local_archive_path ? nomDeFichier(md.local_archive_path) : ''
  if (cheminSigne.includes('/signed/') && nomOriginal) {
    pieces.push({ cle: 'original', libelle: 'Original non signé', storagePath: `${cheminSigne.split('/signed/')[0]}/${nomOriginal}`, bucket, genre: 'original', format: 'pdf', signataireIndex: null })
  }

  if (sd.provider === 'youtrust') {
    for (const p of Array.isArray(sd.preuves) ? sd.preuves : []) {
      if (!p?.storage_path) continue
      const role = ROLE[String(p.role ?? '')] ?? 'signataire'
      pieces.push({ cle: `preuve-${p.index ?? pieces.length}`, libelle: `Preuve de signature — ${role}${p.index ? ` (case ${p.index})` : ''}`, storagePath: p.storage_path, bucket: p.storage_bucket ?? bucket, genre: 'preuve', format: 'pdf', signataireIndex: p.index ?? null })
    }
  } else {
    const f = md.immosign_files
    if (f?.proofs_zip?.storage_path) pieces.push({ cle: 'preuves-zip', libelle: 'Preuves de signature (ZIP)', storagePath: f.proofs_zip.storage_path, bucket: f.proofs_zip.storage_bucket ?? bucket, genre: 'preuve', format: 'zip', signataireIndex: null })
    if (f?.procedure_zip?.storage_path) pieces.push({ cle: 'procedure-zip', libelle: 'Dossier de la procédure (ZIP)', storagePath: f.procedure_zip.storage_path, bucket: f.procedure_zip.storage_bucket ?? bucket, genre: 'procedure', format: 'zip', signataireIndex: null })
  }
  return pieces
}
