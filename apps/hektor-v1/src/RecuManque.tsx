// GED (12/11/2026, morceau 3) -- LE BLOC « REÇU / MANQUE » en haut de l'onglet Documents : les pièces attendues au
// moment en cours du dossier (lib/gedPieces.ts), reçues ou non trouvées. Derrière l'interrupteur `ged_recu_manque`.
// On SIGNALE, on ne bloque rien. Une pièce non trouvée se dépose d'un clic, son type déjà choisi.
// Les anciens documents comptent par leur NOM (décision du 12/11 : le stock n'est pas classé) ; ceux déposés avec
// l'outil comptent par le type que l'utilisateur leur a donné.
import { useEffect, useMemo, useState } from 'react'
import { loadGedClassements } from './lib/ged'
import { LIBELLE_MOMENT, recuManque, type FaitsDuBien, type LignePiece } from './lib/gedPieces'
import type { ConsoleDocument } from './types'
import './RecuManque.css'

const NIVEAU: Record<LignePiece['niveau'], string> = {
  obligatoire: 'obligatoire',
  bonne_pratique: 'bonne pratique',
  selon_le_cas: 'selon le cas',
}

export function RecuManque({
  hektorAnnonceId, documents, faits, onDeposer,
}: {
  hektorAnnonceId: string | number
  documents: ConsoleDocument[]
  faits: FaitsDuBien
  onDeposer?: (typeCode: string, libelle: string) => void
}) {
  const [classements, setClassements] = useState<Map<string, string>>(() => new Map())
  const [ouvrirPrecedents, setOuvrirPrecedents] = useState(false)
  // ce qui manque d'abord ; les pièces reçues se replient sur une ligne (écran bas : 665 px)
  const [ouvrirRecues, setOuvrirRecues] = useState(false)
  const nbDocuments = documents.length

  useEffect(() => {
    let annule = false
    void loadGedClassements(hektorAnnonceId).then((m) => { if (!annule) setClassements(m) })
    return () => { annule = true }
    // relu quand la liste des documents change (un dépôt vient d'arriver)
  }, [hektorAnnonceId, nbDocuments])

  const resultat = useMemo(() => recuManque(
    faits,
    documents
      .filter((d) => d.present_in_hektor !== false)
      .map((d) => ({ nom: d.document_name, typeCode: classements.get(d.id) ?? null })),
  ), [faits, documents, classements])

  const ligne = (l: LignePiece) => {
    const recu = l.etat === 'recu'
    const contenu = (
      <>
        <span className={`gm-ic is-${l.etat}`} aria-hidden="true">{recu ? '✓' : l.etat === 'selon_le_cas' ? '?' : ''}</span>
        <span className="gm-t">
          {l.libelle}
          {l.sensible ? <span className="gm-prive" title="Toujours privé">privé</span> : null}
          <small>{NIVEAU[l.niveau]}{l.pourquoi ? ` : ${l.pourquoi}` : ''}</small>
        </span>
        <span className="gm-d">
          {recu
            ? `${l.dansUnDossier ? 'Dans un dossier de diagnostics : ' : ''}${l.documents.slice(0, 2).join(', ')}${l.documents.length > 2 ? ` (+${l.documents.length - 2})` : ''}`
            : l.etat === 'selon_le_cas'
              ? 'La fiche ne dit pas si elle est due'
              : onDeposer ? 'Non trouvée : déposer' : 'Non trouvée'}
        </span>
      </>
    )
    if (!recu && onDeposer) {
      return (
        <button key={l.cle} type="button" className={`gm-l is-${l.etat}`} onClick={() => onDeposer(l.typeADeposer, l.libelle)} aria-label={`Déposer : ${l.libelle}`}>
          {contenu}
        </button>
      )
    }
    return <div key={l.cle} className={`gm-l is-${l.etat}`}>{contenu}</div>
  }

  const manquantesAvant = resultat.precedents.reduce((n, p) => n + p.manquantes.length, 0)

  return (
    <section className="gm" aria-label="Reçu / manque">
      <div className="gm-h">
        <h4>{`${LIBELLE_MOMENT[resultat.moment]} : ${resultat.recues} pièce${resultat.recues > 1 ? 's' : ''} sur ${resultat.attendues}`}</h4>
        <span>Reçu / manque, d'après le type de chaque document (son nom pour les anciens)</span>
      </div>
      <div className="gm-liste">{resultat.pieces.filter((l) => l.etat !== 'recu').map(ligne)}</div>
      {resultat.recues ? (
        <div className="gm-avant">
          <button type="button" className="gm-avant-b" onClick={() => setOuvrirRecues((v) => !v)} aria-expanded={ouvrirRecues}>
            {`${ouvrirRecues ? '▾' : '▸'} ${resultat.recues} pièce${resultat.recues > 1 ? 's' : ''} reçue${resultat.recues > 1 ? 's' : ''}`}
          </button>
          {ouvrirRecues ? <div className="gm-liste">{resultat.pieces.filter((l) => l.etat === 'recu').map(ligne)}</div> : null}
        </div>
      ) : null}
      {manquantesAvant ? (
        <div className="gm-avant">
          <button type="button" className="gm-avant-b" onClick={() => setOuvrirPrecedents((v) => !v)} aria-expanded={ouvrirPrecedents}>
            {`${ouvrirPrecedents ? '▾' : '▸'} Moments précédents : ${manquantesAvant} pièce${manquantesAvant > 1 ? 's' : ''} obligatoire${manquantesAvant > 1 ? 's' : ''} non trouvée${manquantesAvant > 1 ? 's' : ''}`}
          </button>
          {ouvrirPrecedents ? resultat.precedents.map((p) => (
            <div key={p.moment} className="gm-liste">
              <p className="gm-avant-t">{LIBELLE_MOMENT[p.moment]}</p>
              {p.manquantes.map(ligne)}
            </div>
          )) : null}
        </div>
      ) : null}
    </section>
  )
}
