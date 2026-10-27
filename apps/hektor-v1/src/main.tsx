import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import '@fontsource-variable/inter'
import '@fontsource/hanken-grotesk/400.css'
import '@fontsource/hanken-grotesk/500.css'
import '@fontsource/hanken-grotesk/600.css'
import '@fontsource/hanken-grotesk/700.css'
import '@fontsource/hanken-grotesk/800.css'
import '@fontsource/spectral/500.css'
import '@fontsource/spectral/600.css'
import '@fontsource/spectral/700.css'
import '@fontsource/fraunces/500.css'
import '@fontsource/fraunces/600.css'
import '@fontsource/fraunces/700.css'
import './design-system.css'
import './styles.css'
import './layout-overrides.css'
import './mobile.css'
import './detail-premium.css'
import './fiche-annonce-v5.css'
import './fiche-estimation.css'
import './fiche-contact-v2.css'
import './mandat-detail-v1.css'
import './recherche-acquereur.css'
import './recherche-mandat.css'
import './annonces-v2.css'
import './registre-v2.css'
import './notifications-bell.css'
import './rapprochement-stats.css'
import './nav-icons-v2.css'
import './estimation-listing-v2.css'
import './annuaire-contacts-v2.css'
import './fa-cockpit-v2.css'
import './fa-mandat-v3.css'
import './contact-detail-v2.css'
import './bienvu.css'
import './menu-lateral-net.css'

// bienvu (refonte graphique, charte d'octobre 2026) : ÉTEINT par défaut. Lu au BUILD par Vite,
// donc toute bascule Vercel exige un rebuild. Éteint, bienvu.css ne change aucun pixel.
if (['true', '1', 'on', 'yes'].includes(String(import.meta.env.VITE_APP_BIENVU_ENABLED ?? '').trim().toLowerCase())) {
  document.documentElement.classList.add('bv')
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
