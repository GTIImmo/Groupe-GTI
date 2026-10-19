// bienvu — l'interrupteur, lu UNE FOIS au build par Vite (toute bascule exige un rebuild).
// Même lecture que main.tsx et index.html ; éteint par défaut.
export const APP_BIENVU_ENABLED = ['true', '1', 'on', 'yes'].includes(
  String(import.meta.env.VITE_APP_BIENVU_ENABLED ?? '').trim().toLowerCase(),
)
