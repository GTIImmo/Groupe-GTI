import { useEffect, useState } from 'react'

// ─────────────────────────────────────────────────────────────────────────────
// 17/11/2026 (note étape 4 §57-59) -- LE RELAIS « ASSISTANT -> FENÊTRE DE DÉPÔT GED ».
// La carte « déposer des documents » de l'assistant ne dépose rien : l'écran retélécharge les fichiers joints (le
// trombone) et les POSE ici pour un bien ; la fiche de CE bien ouvre « Médias & pièces » sur Documents, le panneau ouvre
// la fenêtre GED, et la fenêtre les prend par `ajouterFichiers` (le chemin d'un glisser-déposer : garde RIB, sensibles,
// doublon, classement, lecture -- tout l'agent GED). Un dépôt n'est pris qu'UNE fois (son jeton), puis retiré.
// Pas d'état dans la base : c'est un passage de main dans la page, qui disparaît au rechargement.
// La fenêtre lit elle-même le dépôt de SON bien (useDepotAssistant) : aucune propriété neuve dans App.tsx (son test GED
// borne le bloc `formulaireAjout`).
// ─────────────────────────────────────────────────────────────────────────────

export type DepotAssistant = { jeton: number; appDossierId: number; fichiers: File[] }

const EVENEMENT_DEPOT_ASSISTANT = 'gti-depot-assistant'
let enAttente: DepotAssistant | null = null

export function poserDepotAssistant(appDossierId: number, fichiers: File[]): void {
  enAttente = { jeton: Date.now(), appDossierId, fichiers }
  window.dispatchEvent(new Event(EVENEMENT_DEPOT_ASSISTANT))
}

export function retirerDepotAssistant(jeton: number): void {
  if (enAttente?.jeton !== jeton) return
  enAttente = null
  window.dispatchEvent(new Event(EVENEMENT_DEPOT_ASSISTANT))
}

/** Le dépôt en attente pour CE bien (ou rien). */
export function useDepotAssistant(appDossierId: number | null | undefined): DepotAssistant | null {
  const lire = () => (enAttente && appDossierId != null && enAttente.appDossierId === Number(appDossierId) ? enAttente : null)
  const [depot, setDepot] = useState<DepotAssistant | null>(lire)
  useEffect(() => {
    const ecouter = () => setDepot(lire())
    ecouter()
    window.addEventListener(EVENEMENT_DEPOT_ASSISTANT, ecouter)
    return () => window.removeEventListener(EVENEMENT_DEPOT_ASSISTANT, ecouter)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appDossierId])
  return depot
}
