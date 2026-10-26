import { useEffect, useRef, useState, type ReactNode } from 'react'
import { BienvuLogo, BienvuSymbol } from '../BienvuLogo'
import { APP_BIENVU_ENABLED } from '../lib/bienvuFlag'
import '../menu-tiroir.css'

export type AppScreen = 'accueil' | 'annonces' | 'mandats' | 'estimations' | 'registre' | 'contacts' | 'agenda' | 'suivi' | 'sante'

// ⛔ 26/10/2026 -- LE MENU « TROIS TRAITS » (demande de Frederic).
//   Sur telephone, la barre d'icones sous l'en-tete ne tenait plus (8 entrees pour un admin : libelles coupes,
//   « Annon… », « Estimatio… ») et prenait 60 px de chaque ecran. Elle est REMPLACEE par un bouton ☰ qui ouvre un
//   panneau avec toutes les vues en entier. Tablette (>= 768 px) : la barre du bas reste, le ☰ s'ajoute.
//   `false` = l'ancienne barre d'icones, en une ligne.
const MENU_TIROIR = true

type MobileLayoutProps = {
  children: ReactNode
  currentScreen: AppScreen
  title: string
  // « admin ou manager » depuis le 12/10 : c'est ce qui ouvre Suivi et l'outil
  // Utilisateurs au manager.
  isAdmin: boolean
  // ADMIN STRICT : rien que l'ecran Sante s'en sert.
  isAdminStrict?: boolean
  userInitials: string
  userLabel: string
  agencyLabel: string
  onNavigate: (screen: AppScreen) => void
  onOpenUsers?: () => void
  onSignOut?: () => void
  // POINT 4 (26/10/2026) : la loupe de la recherche globale, dans la barre du haut.
  onOpenSearch?: () => void
}

const mobileNavItems: Array<{ screen: AppScreen; label: string; icon: string; detail: string; adminOnly?: boolean; adminStrictOnly?: boolean }> = [
  { screen: 'accueil', label: 'Accueil', icon: 'home', detail: 'Ma journée, mes priorités' },
  { screen: 'mandats', label: 'Annonces', icon: 'home', detail: 'Le portefeuille de biens' },
  { screen: 'estimations', label: 'Estimations', icon: 'trend', detail: 'Avis de valeur en cours' },
  { screen: 'registre', label: 'Mandats', icon: 'doc', detail: 'Le registre des mandats' },
  { screen: 'contacts', label: 'Contacts', icon: 'contact', detail: 'Annuaire et recherches' },
  { screen: 'agenda', label: 'Agenda', icon: 'calendar', detail: 'Rendez-vous et visites' },
  { screen: 'suivi', label: 'Suivi', icon: 'target', detail: 'Demandes et validations', adminOnly: true },
  // ⚠ L'ecran Sante reste ADMIN SEUL -- exception voulue par Frederic le 12/10,
  //   alors que Suivi et l'outil Utilisateurs s'ouvrent au manager.
  { screen: 'sante', label: 'Santé', icon: 'target', detail: 'Surveillance du système', adminStrictOnly: true },
]

// Les pictos du panneau : un dessin par vue (les memes idees que le menu du bureau, nav-icons-v2.css).
const PICTOS: Partial<Record<AppScreen, ReactNode>> = {
  accueil: <path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" />,
  mandats: <><rect x="3" y="8" width="8" height="13" rx="1" /><path d="M11 21V4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v17M6 12h2M6 16h2M15 7h2M15 11h2M15 15h2M2 21h20" /></>,
  estimations: <><circle cx="10" cy="10" r="6.5" /><path d="m20 20-5.2-5.2M12.2 8a2.8 2.8 0 1 0 0 4M7.6 9.4h3.4M7.6 10.8h3.4" /></>,
  registre: <><path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" /><path d="M14 3v5h5M9 13h6M9 17c1.2-1.5 2.2-1.5 3 0s1.8 1.5 3 0" /></>,
  contacts: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="11" r="2.5" /><path d="M5.5 17c.8-1.8 2-2.6 3.5-2.6s2.7.8 3.5 2.6M15 10h3M15 14h3" /></>,
  agenda: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18M9 15l2 2 4-4" /></>,
  suivi: <><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4V3h6v1M9 11l2 2 4-4M9 17h6" /></>,
  sante: <path d="M3 12h4l2-6 4 12 2-6h6" />,
}

function Picto({ screen }: { screen: AppScreen }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {PICTOS[screen]}
    </svg>
  )
}

export function MobileLayout({
  children,
  currentScreen,
  title,
  isAdmin,
  isAdminStrict,
  userInitials,
  userLabel,
  agencyLabel,
  onNavigate,
  onOpenUsers,
  onSignOut,
  onOpenSearch,
}: MobileLayoutProps) {
  const visibleNav = mobileNavItems.filter((item) => {
    if (item.adminStrictOnly) return Boolean(isAdminStrict)
    if (item.adminOnly) return isAdmin
    return true
  })
  const [menuOuvert, setMenuOuvert] = useState(false)
  const entreeEnCoursRef = useRef<HTMLButtonElement | null>(null)

  // Echap ferme le panneau ; a l'ouverture, le curseur va sur la vue en cours.
  useEffect(() => {
    if (!menuOuvert) return
    const surTouche = (event: KeyboardEvent) => { if (event.key === 'Escape') setMenuOuvert(false) }
    window.addEventListener('keydown', surTouche)
    window.setTimeout(() => entreeEnCoursRef.current?.focus(), 0)
    return () => window.removeEventListener('keydown', surTouche)
  }, [menuOuvert])

  const aller = (screen: AppScreen) => {
    setMenuOuvert(false)
    onNavigate(screen)
  }
  const principales = visibleNav.filter((item) => !item.adminOnly && !item.adminStrictOnly)
  const pilotage = visibleNav.filter((item) => item.adminOnly || item.adminStrictOnly)
  const entree = (item: (typeof visibleNav)[number]) => {
    const actif = currentScreen === item.screen
    return (
      <button
        key={item.screen}
        ref={actif ? entreeEnCoursRef : undefined}
        type="button"
        className={`mtiroir-entree${actif ? ' is-active' : ''}`}
        aria-current={actif ? 'page' : undefined}
        onClick={() => aller(item.screen)}
      >
        <span className="mtiroir-picto"><Picto screen={item.screen} /></span>
        <span className="mtiroir-libelle">
          <strong>{item.label}</strong>
          <small>{item.detail}</small>
        </span>
        {actif ? <span className="mtiroir-ici">Ici</span> : null}
      </button>
    )
  }

  return (
    <div className={`mobile-app-shell${MENU_TIROIR ? ' has-tiroir' : ''}`}>
      <header className={`mobile-app-header${onOpenSearch ? ' has-search' : ''}${MENU_TIROIR ? ' has-tiroir' : ''}`}>
        {MENU_TIROIR ? (
          <button
            className={`mobile-burger${menuOuvert ? ' is-open' : ''}`}
            type="button"
            aria-label={menuOuvert ? 'Fermer le menu' : 'Ouvrir le menu'}
            aria-expanded={menuOuvert}
            aria-controls="mobile-tiroir"
            onClick={() => setMenuOuvert((v) => !v)}
          >
            <span /><span /><span />
          </button>
        ) : null}
        {/* bienvu (lot 3) : le symbole remplace la forme dessinée en CSS ; « GTI Immobilier » devient le nom du logiciel */}
        {APP_BIENVU_ENABLED
          ? <div className="mobile-brand-mark mobile-brand-mark-bv" aria-hidden="true"><BienvuSymbol /></div>
          : <div className="mobile-brand-mark" aria-hidden="true" />}
        <div className="mobile-title-block">
          <span>{APP_BIENVU_ENABLED ? 'bienvu' : 'GTI Immobilier'}</span>
          <h1>{title}</h1>
        </div>
        {onOpenSearch ? (
          <button className="mobile-search-button" type="button" onClick={onOpenSearch} aria-label="Rechercher partout">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" /><path d="m20 20-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
          </button>
        ) : null}
        <button className="mobile-user-button" type="button" onClick={isAdmin ? onOpenUsers : undefined} aria-label={userLabel}>
          {userInitials}
        </button>
      </header>

      <main className="mobile-app-content">{children}</main>

      <nav className="mobile-bottom-nav" aria-label="Navigation mobile">
        {visibleNav.map((item) => (
          <button
            key={item.screen}
            className={`mobile-bottom-nav-item ${currentScreen === item.screen ? 'is-active' : ''}`}
            type="button"
            onClick={() => onNavigate(item.screen)}
          >
            <span className={`mobile-nav-icon mobile-nav-icon-${item.icon}`} aria-hidden="true" />
            <strong>{item.label}</strong>
          </button>
        ))}
      </nav>

      {MENU_TIROIR ? (
        <div className={`mtiroir-fond${menuOuvert ? ' is-open' : ''}`} onClick={() => setMenuOuvert(false)} aria-hidden={!menuOuvert}>
          <aside
            id="mobile-tiroir"
            className="mtiroir"
            role="dialog"
            aria-modal="true"
            aria-label="Menu"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mtiroir-tete">
              <div className="mtiroir-marque">
                {APP_BIENVU_ENABLED ? <BienvuLogo /> : <strong>GTI Immobilier</strong>}
              </div>
              <button type="button" className="mtiroir-fermer" aria-label="Fermer le menu" onClick={() => setMenuOuvert(false)}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
              </button>
            </div>
            {onOpenSearch ? (
              <button type="button" className="mtiroir-recherche" onClick={() => { setMenuOuvert(false); onOpenSearch() }}>
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" /><path d="m20 20-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
                <span>Rechercher partout…</span>
              </button>
            ) : null}
            <nav className="mtiroir-liste" aria-label="Vues">
              <p className="mtiroir-section">Travail</p>
              {principales.map(entree)}
              {pilotage.length ? <p className="mtiroir-section">Pilotage</p> : null}
              {pilotage.map(entree)}
            </nav>
            <div className="mtiroir-pied">
              <span className="mtiroir-avatar" aria-hidden="true">{userInitials}</span>
              <span className="mtiroir-qui">
                <strong>{userLabel}</strong>
                <small>{agencyLabel}</small>
              </span>
              <span className="mtiroir-actions">
                {isAdmin && onOpenUsers ? <button type="button" onClick={() => { setMenuOuvert(false); onOpenUsers() }}>Utilisateurs</button> : null}
                {onSignOut ? <button type="button" className="is-sortie" onClick={() => { setMenuOuvert(false); onSignOut() }}>Déconnexion</button> : null}
              </span>
            </div>
          </aside>
        </div>
      ) : null}

      <div className="mobile-session-card" aria-label="Session">
        <span>{agencyLabel}</span>
        {onSignOut ? <button type="button" onClick={onSignOut}>Déconnexion</button> : null}
      </div>
    </div>
  )
}
