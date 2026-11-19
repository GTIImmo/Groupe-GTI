// La fenêtre de dépôt ouverte AU-DESSUS du bien (skin cockpit). Tant qu'elle est là, « Ce que dit… » ne s'ouvre pas seule :
// essai réel du 19/11 (§12.53-54) -- la fenêtre s'ouvrait PENDANT le dépôt, son « Enregistrer » sous le curseur, à la place
// du « Fermer » / « Envoyer » du dépôt, et ses lignes à trancher sont cochées d'avance : un clic de trop écrivait chez Hektor.
// Le dépôt posé dans le panneau (skin classique) ne se signale pas : il ne cache rien.
import { useEffect, useState } from 'react'

const EVENEMENT = 'ged:fenetre-depot'
let ouvertes = 0

export function signalerFenetreDepot(ouverte: boolean) {
  ouvertes = Math.max(0, ouvertes + (ouverte ? 1 : -1))
  window.dispatchEvent(new CustomEvent(EVENEMENT))
}

export function useFenetreDepotOuverte(): boolean {
  const [ouverte, setOuverte] = useState(ouvertes > 0)
  useEffect(() => {
    const maj = () => setOuverte(ouvertes > 0)
    maj()
    window.addEventListener(EVENEMENT, maj)
    return () => window.removeEventListener(EVENEMENT, maj)
  }, [])
  return ouverte
}
