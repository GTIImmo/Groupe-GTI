// Mandat sans fiche -- demande de Frederic du 03/11/2026 (« les identifier clairement dans le front »).
// Audit : memoire annonces-sans-date-de-mandat-causes ; registre PROTEXA Export_RT14405_12598.xls.
//
// DEUX ETATS, et seulement sur une annonce VIVANTE (« Sans mandat », l'etat 1, n'est pas touche --
// decision du 03/11) :
//   . « Fiche manquante »  : un numero de mandat, mais aucune date de debut. Chez Hektor, l'annonce n'a
//     que le champ « N° mandat » (keyData.NO_MANDAT), son onglet Mandat est vide. Au 03/11 : 63244 / 18928.
//   . « Fiche ailleurs »   : meme chose, mais le MEME numero porte des dates sur une AUTRE annonce du
//     registre. Au 03/11 : 63003 / 18831, dont la fiche est restee sur 62927, archivee le 24/08 (le bien a
//     ete recree le 03/09 et n'a recu que le numero).
// ⚠ Rien n'est ecrit, rien n'est devine : la regle lit la ligne, la jumelle se lit dans le registre
//   (app_registre_mandats_current), une seule fois par numero. Si elle n'est pas lisible (droits, reseau),
//   on reste sur « Fiche manquante » -- jamais d'erreur affichee pour ca.
// ⚠ Les ventes, clotures et archives sont ECARTEES expres : 11 lignes anciennes du registre n'ont pas de
//   dates (dont les reservations brulees 18424 et 18651) et ne se reparent pas ; les nommer est un autre
//   sujet (decision du 03/11).
// Le remede est chez Hektor (decision du 27/10 : l'agence corrige, l'app ne force pas). Le correctif du
// 02/11 (APP_RELIRE_DETAIL_MANDAT_ABSENT, sync_raw.py) ramene la fiche la nuit qui suit.
import { useEffect, useState } from 'react'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import './fiche-mandat.css'

type LigneMandat = {
  hektor_annonce_id?: number | string | null
  numero_mandat?: string | null
  mandat_date_debut?: string | null
  archive?: boolean | number | string | null
  statut_annonce?: string | null
  register_source_kind?: string | null
}

type Jumelle = { annonce: string; archivee: boolean; statut: string; debut: string; fin: string }

export type EtatFicheMandat = {
  cle: 'fiche_manquante' | 'fiche_ailleurs'
  numero: string
  court: string
  phrase: string
  jumelle: Jumelle | null
}

const dateValide = (value?: string | null) => {
  const texte = String(value ?? '').trim()
  return texte !== '' && !texte.startsWith('0000')
}

const jjmmaaaa = (value: string) => {
  const [a, m, j] = value.slice(0, 10).split('-')
  return a && m && j ? `${j}/${m}/${a}` : value
}

const estArchivee = (value: LigneMandat['archive']) => value === true || value === 1 || String(value ?? '') === '1'

/** Le numero si la ligne est une annonce vivante avec un numero et sans date de debut, sinon null. */
export function numeroSansFiche(item: LigneMandat | null | undefined, autreDateDebut?: string | null): string | null {
  if (!item) return null
  const numero = String(item.numero_mandat ?? '').trim()
  if (!numero || dateValide(item.mandat_date_debut) || dateValide(autreDateDebut)) return null
  if (estArchivee(item.archive)) return null
  if (item.register_source_kind && item.register_source_kind !== 'actif') return null
  if (/^(vendu|clos|archiv)/i.test(String(item.statut_annonce ?? '').trim())) return null
  return numero
}

// Une lecture par numero, partagee par toutes les lignes et tous les ecrans.
const jumellesLues = new Map<string, Promise<Jumelle | null>>()

function lireJumelle(numero: string, annonce: string): Promise<Jumelle | null> {
  const cle = `${numero}|${annonce}`
  const deja = jumellesLues.get(cle)
  if (deja) return deja
  const lecture = (async () => {
    if (!hasSupabaseEnv || !supabase) return null
    const { data, error } = await supabase
      .from('app_registre_mandats_current')
      .select('hektor_annonce_id,archive,statut_annonce,mandat_date_debut,mandat_date_fin')
      .eq('numero_mandat', numero)
      .not('mandat_date_debut', 'is', null)
      .limit(5)
    if (error || !data) return null
    const ligne = (data as Array<Record<string, unknown>>).find((row) =>
      String(row.hektor_annonce_id ?? '') !== annonce && dateValide(row.mandat_date_debut as string | null))
    if (!ligne) return null
    return {
      annonce: String(ligne.hektor_annonce_id ?? ''),
      archivee: estArchivee(ligne.archive as LigneMandat['archive']),
      statut: String(ligne.statut_annonce ?? ''),
      debut: String(ligne.mandat_date_debut ?? ''),
      fin: String(ligne.mandat_date_fin ?? ''),
    }
  })().catch(() => null)
  jumellesLues.set(cle, lecture)
  return lecture
}

function etatDe(numero: string, jumelle: Jumelle | null): EtatFicheMandat {
  if (jumelle) {
    const periode = dateValide(jumelle.fin) ? `du ${jjmmaaaa(jumelle.debut)} au ${jjmmaaaa(jumelle.fin)}` : `du ${jjmmaaaa(jumelle.debut)}`
    return {
      cle: 'fiche_ailleurs',
      numero,
      court: 'Fiche ailleurs',
      phrase: `La fiche du mandat n° ${numero} (${periode}) est restée sur l'annonce ${jumelle.archivee ? 'archivée ' : ''}${jumelle.annonce}. Cette annonce n'a reçu que le numéro : rattacher ou recréer la fiche dans l'onglet Mandat de l'annonce chez Hektor. L'app la reprendra la nuit suivante.`,
      jumelle,
    }
  }
  return {
    cle: 'fiche_manquante',
    numero,
    court: 'Fiche manquante',
    phrase: `Le n° ${numero} est pris, mais Hektor n'a aucune fiche mandat sur cette annonce : dates, type et mandants manquent. À créer dans l'onglet Mandat de l'annonce chez Hektor. L'app la reprendra la nuit suivante.`,
    jumelle: null,
  }
}

/** null pour toute annonce normale (aucune lecture). */
export function useFicheMandat(item: LigneMandat | null | undefined, autreDateDebut?: string | null): EtatFicheMandat | null {
  const numero = numeroSansFiche(item, autreDateDebut)
  const annonce = String(item?.hektor_annonce_id ?? '')
  const [jumelle, setJumelle] = useState<Jumelle | null>(null)
  useEffect(() => {
    setJumelle(null)
    if (!numero) return
    let vivant = true
    void lireJumelle(numero, annonce).then((trouvee) => { if (vivant) setJumelle(trouvee) })
    return () => { vivant = false }
  }, [numero, annonce])
  return numero ? etatDe(numero, jumelle) : null
}

const BOUCLIER = 'M12 3l7 3v5c0 4.2-2.7 8-7 10-4.3-2-7-5.8-7-10V6z'

/** La pastille : rouge, le detail au survol. Meme forme que le bouclier de la liste Annonces. */
export function PastilleFicheMandat({ etat }: { etat: EtatFicheMandat }) {
  return (
    <span className="fm-pastille" title={etat.phrase}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d={BOUCLIER} /><path d="M12 8.5v4M12 15.5h.01" />
      </svg>
      {etat.court}
    </span>
  )
}

/** Le message en clair (fiche, ligne depliee) : la phrase entiere, pas seulement au survol. */
export function MessageFicheMandat({ etat }: { etat: EtatFicheMandat }) {
  return (
    <div className="fm-message" role="note">
      <PastilleFicheMandat etat={etat} />
      <span>{etat.phrase}</span>
    </div>
  )
}

/** Raccourcis pour les ecrans qui n'ont pas deja l'etat en main (une ligne de liste, une carte). */
export function PastilleFicheMandatDe({ item }: { item: LigneMandat }) {
  const etat = useFicheMandat(item)
  return etat ? <PastilleFicheMandat etat={etat} /> : null
}

export function MessageFicheMandatDe({ item, autreDateDebut }: { item: LigneMandat | null | undefined; autreDateDebut?: string | null }) {
  const etat = useFicheMandat(item, autreDateDebut)
  return etat ? <MessageFicheMandat etat={etat} /> : null
}
