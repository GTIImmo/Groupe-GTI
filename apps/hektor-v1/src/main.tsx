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
import './design-system.css'
import './styles.css'
import './layout-overrides.css'
import './mobile.css'
import './detail-premium.css'
import './fiche-annonce-v5.css'
import './fiche-estimation.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
