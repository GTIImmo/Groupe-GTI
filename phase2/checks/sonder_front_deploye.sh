#!/usr/bin/env bash
# Sonde le front DEPLOYE jusqu'a y voir les textes de 7-3a.
# Lecon du 08/10 : on ne conclut JAMAIS « le deploiement est casse » juste apres
# un push -- on sonde en boucle, PUIS on parle. Et lecon du 15/10 : le domaine
# peut servir l'ancien paquet depuis le cache pendant un bon moment.
DOMAINE="https://groupe-gti.vercel.app"
ATTENDUS=("Clôturer ce mandat" "Date de clôture" "close_date" "Rouvrir le mandat" "Demander l'annulation de ce mandat")

for essai in $(seq 1 24); do
  HTML=$(curl -s --max-time 25 "$DOMAINE/" 2>/dev/null)
  JS=$(printf '%s' "$HTML" | grep -oE '/assets/index-[A-Za-z0-9_-]+\.js' | head -1)
  if [ -z "$JS" ]; then
    echo "essai $essai : pas encore de paquet nomme dans la page"
    sleep 15; continue
  fi
  CORPS=$(curl -s --max-time 60 "$DOMAINE$JS" 2>/dev/null)
  TAILLE=$(printf '%s' "$CORPS" | wc -c)
  TROUVES=0
  for mot in "${ATTENDUS[@]}"; do
    if printf '%s' "$CORPS" | grep -qF "$mot"; then TROUVES=$((TROUVES+1)); fi
  done
  echo "essai $essai : $JS ($TAILLE octets) -- $TROUVES/${#ATTENDUS[@]} textes neufs"
  if [ "$TROUVES" -eq "${#ATTENDUS[@]}" ]; then
    echo
    echo "=== EN LIGNE, ET VERIFIE MOT PAR MOT ==="
    echo "paquet servi : $JS"
    for mot in "${ATTENDUS[@]}"; do
      printf '  %-40s %s fois\n' "$mot" "$(printf '%s' "$CORPS" | grep -oF "$mot" | wc -l)"
    done
    CSS=$(printf '%s' "$HTML" | grep -oE '/assets/index-[A-Za-z0-9_-]+\.css' | head -1)
    if [ -n "$CSS" ]; then
      NB=$(curl -s --max-time 60 "$DOMAINE$CSS" | grep -oF "md-cloture" | wc -l)
      printf '  %-40s %s fois (dans %s)\n' "md-cloture (CSS)" "$NB" "$CSS"
    fi
    exit 0
  fi
  sleep 15
done
echo
echo "ABANDON : 24 essais (6 min) et les textes ne sont pas servis. NE PAS CONCLURE : interroger Vercel."
exit 1
