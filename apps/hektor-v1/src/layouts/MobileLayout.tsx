import type { ReactNode } from 'react'

export type AppScreen = 'accueil' | 'annonces' | 'mandats' | 'estimations' | 'registre' | 'contacts' | 'agenda' | 'suivi' | 'sante'

type MobileLayoutProps = {
  children: ReactNode
  currentScreen: AppScreen
  title: string
  isAdmin: boolean
  userInitials: string
  userLabel: string
  agencyLabel: string
  onNavigate: (screen: AppScreen) => void
  onOpenUsers?: () => void
  onSignOut?: () => void
}

const mobileNavItems: Array<{ screen: AppScreen; label: string; icon: string; adminOnly?: boolean }> = [
  { screen: 'accueil', label: 'Accueil', icon: 'home' },
  { screen: 'mandats', label: 'Annonces', icon: 'home' },
  { screen: 'estimations', label: 'Estimations', icon: 'trend' },
  { screen: 'contacts', label: 'Contacts', icon: 'contact' },
  { screen: 'agenda', label: 'Agenda', icon: 'calendar' },
  { screen: 'registre', label: 'Mandats', icon: 'doc' },
  { screen: 'suivi', label: 'Suivi', icon: 'target', adminOnly: true },
  { screen: 'sante', label: 'Santé', icon: 'target', adminOnly: true },
]

export function MobileLayout({
  children,
  currentScreen,
  title,
  isAdmin,
  userInitials,
  userLabel,
  agencyLabel,
  onNavigate,
  onOpenUsers,
  onSignOut,
}: MobileLayoutProps) {
  const visibleNav = mobileNavItems.filter((item) => !item.adminOnly || isAdmin)

  return (
    <div className="mobile-app-shell">
      <header className="mobile-app-header">
        <div className="mobile-brand-mark" aria-hidden="true" />
        <div className="mobile-title-block">
          <span>GTI Immobilier</span>
          <h1>{title}</h1>
        </div>
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
