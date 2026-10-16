#!/usr/bin/env bash
# Sonde le front DEPLOYE jusqu'a ce qu'il porte l'etat attendu.
#
# Lecon du 08/10 : on ne conclut JAMAIS « le deploiement est casse » juste apres
# un push -- on sonde en boucle, PUIS on parle. Et le domaine peut servir
# l'ancien paquet depuis le cache pendant un bon moment.
#
# ⚠⚠ LECON DU 16/10, PAYEE SUR CE SCRIPT MEME : une sonde qui ne cherche que ce
#    qui doit APPARAITRE est satisfaite par la VERSION D'AVANT. La premiere
#    version de ce script a repondu « EN LIGNE » sur l'ancien paquet, parce que
#    les textes qu'elle guettait y etaient deja. Une sonde de deploiement se fait
#    DANS LES DEUX SENS : ce qui doit etre la, ET ce qui doit avoir disparu.
#    (Meme regle que la repetition d'un patch SQL : le temoin inverse.)
#
# Usage :
#   sonder_front_deploye.sh "texte attendu|autre attendu" "texte disparu|autre"
# Sans argument, il joue l'etat du 16/10 (chantier ⑦-3a).

DOMAINE="https://groupe-gti.vercel.app"
IFS='|' read -r -a ATTENDUS <<< "${1:-Demander l'annulation de ce mandat|Corriger la date de clôture|c'est ce qui en garde la trace|close_date}"
IFS='|' read -r -a DISPARUS <<< "${2:-Clôturer ce mandat|Rouvrir le mandat}"

for essai in $(seq 1 24); do
  HTML=$(curl -s --max-time 25 "$DOMAINE/" 2>/dev/null)
  JS=$(printf '%s' "$HTML" | grep -oE '/assets/index-[A-Za-z0-9_-]+\.js' | head -1)
  if [ -z "$JS" ]; then
    echo "essai $essai : pas encore de paquet nomme dans la page"; sleep 15; continue
  fi
  CORPS=$(curl -s --max-time 60 "$DOMAINE$JS" 2>/dev/null)

  OK=0; MANQUE=""
  for mot in "${ATTENDUS[@]}"; do
    if printf '%s' "$CORPS" | grep -qF "$mot"; then OK=$((OK+1)); else MANQUE="$MANQUE [+]$mot"; fi
  done
  PARTIS=0
  for mot in "${DISPARUS[@]}"; do
    # une entree VIDE veut dire « rien a faire disparaitre » : on ne la compte pas
    # comme un succes gratuit, on la retire du total.
    if [ -z "$mot" ]; then continue; fi
    if printf '%s' "$CORPS" | grep -qF "$mot"; then MANQUE="$MANQUE [-]$mot"; else PARTIS=$((PARTIS+1)); fi
  done
  ATTENDU_PARTIS=0
  for mot in "${DISPARUS[@]}"; do if [ -n "$mot" ]; then ATTENDU_PARTIS=$((ATTENDU_PARTIS+1)); fi; done

  echo "essai $essai : $JS -- presents $OK/${#ATTENDUS[@]} · disparus $PARTIS/$ATTENDU_PARTIS$MANQUE"

  if [ "$OK" -eq "${#ATTENDUS[@]}" ] && [ "$PARTIS" -eq "$ATTENDU_PARTIS" ]; then
    echo
    echo "=== EN LIGNE, ET VERIFIE DANS LES DEUX SENS ==="
    echo "paquet servi : $JS ($(printf '%s' "$CORPS" | wc -c) octets)"
    for mot in "${ATTENDUS[@]}"; do printf '  PRESENT  %-44s %s fois\n' "$mot" "$(printf '%s' "$CORPS" | grep -oF "$mot" | wc -l)"; done
    for mot in "${DISPARUS[@]}"; do printf '  DISPARU  %-44s 0 fois\n' "$mot"; done
    exit 0
  fi
  sleep 15
done
echo
echo "ABANDON : 24 essais (6 min) sans atteindre l'etat attendu. NE PAS CONCLURE : interroger Vercel."
exit 1
