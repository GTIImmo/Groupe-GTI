// bienvu — signaux de démarrage vers l'écran de démarrage posé par index.html.
//
// L'écran de démarrage vit hors de React (il doit être peint avant l'arrivée du paquet). Il
// n'existe que si VITE_APP_BIENVU_ENABLED est allumé au build ; éteint, `window.__bvSplash`
// n'est pas défini et tout ce fichier ne fait rien.
//
// Règle : il part dès que les données sont prêtes, jamais plus tard.
//   · pas de session            -> prêt dès que la session est connue (c'est l'écran de connexion)
//   · session + première page   -> prêt quand la première page de biens a répondu (réussie ou non)
// Il revient quand on se connecte sans recharger la page (mot de passe) : session absente puis présente.

type Splash = { show: () => void; hide: () => void }

let sessionKnown = false
let hasSession = false
let dataDone = false

function splash(): Splash | undefined {
  return (window as unknown as { __bvSplash?: Splash }).__bvSplash
}

function sync() {
  if (sessionKnown && (!hasSession || dataDone)) splash()?.hide()
}

export const bvBoot = {
  /** La session est connue (au démarrage, à la connexion, à la déconnexion). Idempotent. */
  session(has: boolean) {
    const wasSignedOut = sessionKnown && !hasSession
    sessionKnown = true
    hasSession = has
    if (!has) dataDone = false
    if (has && wasSignedOut) {
      // connexion sans rechargement : l'écran de démarrage revient jusqu'aux premières données
      dataDone = false
      splash()?.show()
    }
    sync()
  },
  /** La première page de biens a répondu (réussie ou en erreur : l'écran porte alors son propre message). */
  data() {
    dataDone = true
    sync()
  },
}
