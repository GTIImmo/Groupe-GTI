import type { ReactNode } from 'react'
import { BienvuSymbol } from '../BienvuLogo'
import { APP_BIENVU_ENABLED } from '../lib/bienvuFlag'

export type AppScreen = 'accueil' | 'annonces' | 'mandats' | 'estimations' | 'registre' | 'contacts' | 'agenda' | 'suivi' | 'sante'

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

const mobileNavItems: Array<{ screen: AppScreen; label: string; icon: string; adminOnly?: boolean; adminStrictOnly?: boolean }> = [
  { screen: 'accueil', label: 'Accueil', icon: 'home' },
  { screen: 'mandats', label: 'Annonces', icon: 'home' },
  { screen: 'estimations', label: 'Estimations', icon: 'trend' },
  { screen: 'contacts', label: 'Contacts', icon: 'contact' },
  { screen: 'agenda', label: 'Agenda', icon: 'calendar' },
  { screen: 'registre', label: 'Mandats', icon: 'doc' },
  { screen: 'suivi', label: 'Suivi', icon: 'target', adminOnly: true },
  // ⚠ L'ecran Sante reste ADMIN SEUL -- exception voulue par Frederic le 12/10,
  //   alors que Suivi et l'outil Utilisateurs s'ouvrent au manager.
  { screen: 'sante', label: 'Santé', icon: 'target', adminStrictOnly: true },
]

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

  return (
    <div className="mobile-app-shell">
      <header className="mobile-app-header">
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

      <div className="mobile-session-card" aria-label="Session">
        <span>{agencyLabel}</span>
        {onSignOut ? <button type="button" onClick={onSignOut}>Déconnexion</button> : null}
      </div>
    </div>
  )
}
