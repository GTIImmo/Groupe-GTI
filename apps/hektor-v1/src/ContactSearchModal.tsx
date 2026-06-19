import { useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { createHektorContactSearchJob, editSearchOptimistic } from './lib/api'
import type { AppContactSearch, ConsoleJob } from './types'
import ContactSearchFields, {
  contactSearchValueFromSearch,
  contactSearchValueToInput,
  defaultContactSearchValue,
  type ContactSearchFieldsValue,
  type OfferOption,
} from './ContactSearchFields'
import './contact-search.css'

export type ContactSearchModalProps = {
  contactId: string
  contactName?: string | null
  negotiatorLabel?: string | null
  defaultCity?: string | null
  defaultPostalCode?: string | null
  defaultOfferCode?: string | null
  offerOptions?: OfferOption[]
  contactKind?: string | null
  contactQualification?: string | null
  mode?: 'create' | 'edit'
  initialSearch?: AppContactSearch | null
  onClose: () => void
  onCreated?: (job: ConsoleJob) => void
  // Affinage Supabase-first : appelé après une édition optimiste (pas de job) pour
  // que l'écran recharge le rapprochement (déjà recalculé côté serveur).
  onOptimisticSaved?: () => void
}

export default function ContactSearchModal(props: ContactSearchModalProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const isEdit = props.mode === 'edit' && !!props.initialSearch

  const [value, setValue] = useState<ContactSearchFieldsValue>(() => {
    if (props.initialSearch) return contactSearchValueFromSearch(props.initialSearch)
    const seed: Partial<ContactSearchFieldsValue> = {}
    if (props.defaultOfferCode) seed.offerCode = props.defaultOfferCode
    if (props.defaultCity || props.defaultPostalCode) {
      seed.localities = [{ city: (props.defaultCity || '').trim(), postalCode: (props.defaultPostalCode || '').trim() }]
    }
    return defaultContactSearchValue(seed)
  })

  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const submit = async () => {
    setError(null)
    if (!value.typeIds.length) { setError('Sélectionne au moins un type de bien.'); return }
    if (!value.localities.length) { setError('Ajoute au moins une localité.'); return }
    setPending(true)
    try {
      const search = contactSearchValueToInput(value)
      const context = {
        contactKind: props.contactKind ?? null,
        qualification: props.contactQualification ?? null,
        city: props.defaultCity ?? null,
        postalCode: props.defaultPostalCode ?? null,
      }
      if (isEdit && props.initialSearch) {
        // Édition = optimiste : critères écrits direct dans Supabase (rapprochement
        // recalculé sur-le-champ par le RPC), push Hektor débouncé. Pas de job.
        // L'anti-écrasement (base_snapshot) est géré côté serveur via app_search_pending.
        await editSearchOptimistic({ contactId: props.contactId, searchIndex: props.initialSearch.search_index, search, context })
        props.onOptimisticSaved?.()
        // Événement global : recharge la fiche/le rapprochement où qu'on soit (sans drilling).
        try { window.dispatchEvent(new CustomEvent('hektor:search-updated')) } catch { /* noop */ }
        setPending(false)
        setNotice('Recherche mise à jour — rapprochement actualisé')
        window.setTimeout(() => props.onClose(), 1200)
        return
      } else {
        const job = await createHektorContactSearchJob({ contactId: props.contactId, search, context })
        props.onCreated?.(job)
        props.onClose()
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Création de la recherche impossible.')
      setPending(false)
    }
  }

  const searchContextLabel = props.contactKind === 'locataire' ? 'Recherche locataire' : 'Recherche acquereur'

  return createPortal(
    <div className="csearch-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) props.onClose() }}>
      <div className="csearch">
        <div className="edit" role="dialog" aria-modal="true" aria-labelledby="csearchTitle" data-screen-label="Ajouter une recherche">
          <div className="edit-head">
            <div className="edit-h-main">
              <div className="edit-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
              </div>
              <div>
                <div className="edit-eyebrow">Création Hektor</div>
                <h2 className="edit-title" id="csearchTitle">{isEdit ? 'Modifier la recherche' : 'Ajouter une recherche'}</h2>
                <div className="head-meta"><span className="hm-pill"><span className="hm-dot" />{props.contactName ? `${searchContextLabel} pour ${props.contactName}` : searchContextLabel} · resynchronisation Hektor</span></div>
              </div>
            </div>
            <div className="head-right">
              <button className="edit-close" type="button" onClick={props.onClose}>Fermer</button>
            </div>
          </div>

          <div className="edit-context">
            <span className="ctx-k">Compte Hektor</span>
            <span className="ctx-wrap"><span className="ctx-sel">{props.negotiatorLabel || 'Négociateur du contact'}</span></span>
            <span className="ctx-hint">La recherche est créée sous le compte du négociateur du contact.</span>
          </div>

          <div className="wiz-scroll" ref={scrollRef}>
            <ContactSearchFields value={value} onChange={setValue} offerOptions={props.offerOptions} scrollRef={scrollRef} />
          </div>

          <div className="edit-foot">
            {notice
              ? <span className="ok" style={{ color: '#1b8a4b', fontWeight: 700 }}>✓ {notice}</span>
              : error ? <span className="err">{error}</span> : <span className="spacer">Au moins 1 type, 1 commune et un budget max.</span>}
            <button type="button" className="btn-neutral" onClick={props.onClose} disabled={pending || !!notice}>Annuler</button>
            <button type="button" className="btn-brand" onClick={submit} disabled={pending || !!notice}>{notice ? 'Enregistré ✓' : pending ? (isEdit ? 'Enregistrement…' : 'Création…') : (isEdit ? 'Enregistrer la recherche' : 'Créer la recherche')}</button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}
