// bienvu — quelques pictos au trait, pour remplacer les emojis des modales.
// Même écriture que le reste de l'interface : 24 × 24, trait de 1,8, extrémités arrondies,
// couleur = `currentColor` (le CSS décide). Décoratifs : aria-hidden.
import type { ReactNode } from 'react'

const TRAITS: Record<string, ReactNode> = {
  // un crayon qui écrit : « je remplis moi-même »
  pen: <><path d="M4 20h4L19 9a2.1 2.1 0 0 0-3-3L5 17z" /><path d="m14.5 7.5 3 3" /></>,
  // un appareil photo : « par photo »
  camera: <><path d="M4 8h3l1.6-2h6.8L17 8h3v11H4z" /><circle cx="12" cy="13" r="3.4" /></>,
  // un cadre de numérisation : « scanner la fiche »
  scan: <><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" /><path d="M7 12h10" /></>,
  // des étincelles : « assisté par l'IA »
  sparkles: <><path d="m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6z" /><path d="m18.5 15 .7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" /></>,
  // une feuille qu'on télécharge : « le patron vierge »
  file: <><path d="M7 3h7l4 4v14H7z" /><path d="M14 3v4h4" /><path d="M12 11v6m0 0-2.4-2.4M12 17l2.4-2.4" /></>,
  // un triangle d'alerte
  alert: <><path d="M12 4 3 19h18z" /><path d="M12 10v4M12 16.6v.4" /></>,
}

export function BvIcon(props: { name: keyof typeof TRAITS | string; className?: string }) {
  return (
    <svg className={props.className ?? 'bv-ico'} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {TRAITS[props.name] ?? null}
    </svg>
  )
}
