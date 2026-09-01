# Handoff — Chantier idnego, étape MAPPING (mesure du volume)

> Date : 2026-06-21. À coller comme prompt de départ d'une **nouvelle session**.
> But de l'étape : extraire l'API Hektor + comparer, pour **chiffrer le volume exact**
> d'écarts idnego. **Aucune correction cette session — mesure seulement.**

---

## PROMPT À COLLER

```
CONTEXTE (projet GTI / Hektor↔Supabase)
Mes annonces et contacts (local hektor.sqlite + Supabase) portent un numéro de
négociateur (idnego) qui ne correspond plus toujours à celui de Hektor aujourd'hui.
Cause : Hektor a modifié/nettoyé ses idnego SANS bumper la date de modification,
donc mon sync delta (basé sur datemaj) est aveugle et ne l'a jamais corrigé.
Détails en mémoire : idnego-probleme-et-outil.md + note
notice/NOTE_CORRECTIFS_NEGO_DOUBLONS_2026-06-21.md

⚠️ FIABILITÉ DU HANDOFF : la STRUCTURE / le PÉRIMÈTRE ci-dessous a été audité, tu
peux t'y fier (ça ne change pas). En revanche RE-MESURE les volumes toi-même par
re-fetch — mes chiffres ne sont qu'un garde-fou de cohérence, signale tout écart.

OBJECTIF DE CETTE SESSION (mesure seulement, AUCUNE écriture/correction)
Extraire l'API Hektor et construire un MAPPING pour mesurer le VOLUME EXACT de
corrections idnego à prévoir. On ne corrige rien : on compare et on chiffre.

PÉRIMÈTRE (audité — fiable)
Seules 2 vraies sources d'idnego : les ANNONCES et les CONTACTS. Tout le reste
(transactions offres/compromis/ventes, registre, index, RDV…) ne fait que recopier
le négo de l'annonce ou du contact (vérifié : dans les transactions le négo est
imbriqué sous annonce.NEGOCIATEUR + acquereurs/mandants.id_negociateur). Hors périmètre.
- Annonce : champ API « NEGOCIATEUR » (présent dans le LISTING, pas besoin du détail)
- Contact : champ API « id_negociateur » (dans le listing)

CE QU'IL FAUT PRODUIRE (un rapport, LECTURE SEULE)
1. Re-fetch via l'API la liste négo courante : listNegos actif=1 ET actif=0
   (= univers négo actuel de Hektor, actifs + inactifs).
2. Re-fetch les listings annonces (active + archived) → { hektor_annonce_id : NEGOCIATEUR }.
3. Re-fetch les listings contacts (active + archived) → { hektor_contact_id : id_negociateur }.
4. Comparer avec le stocké — ATTENTION AU PÉRIMÈTRE COMPLET (actif + archivé) :
   - Annonces (~56 563) : local hektor_annonce.hektor_negociateur_id ; côté Supabase
     l'annonce est répartie sur 3 INDEX → app_dossier_current.commercial_id (current)
     + app_archive_annonce_index_current.commercial_id (archive)
     + app_historical_annonce_index_current.commercial_id (historical).
   - Contacts (~354 657) : local hektor_contact.hektor_negociateur_id. ⚠️ Côté
     Supabase, SEULS ~57 127 contacts sont synchronisés (app_contact_current,
     hektor_negociateur_id) — le reste (filtré) n'est PAS dans Supabase. Donc la
     comparaison de fond se fait sur le LOCAL ; Supabase ne concerne que le sous-ensemble.
5. Rapport chiffré, pour annonces ET contacts :
   - IDENTIQUE (idnego stocké = idnego Hektor actuel) → rien à faire
   - DIFFÉRENT (Hektor a un autre négo ; ex. VA6482 : j'avais 20, Hektor a 1) → à corriger
   - Pour les DIFFÉRENTS : le négo Hektor actuel est-il actif ou inactif ?
   - Orphelin : idnego (stocké ou Hektor) absent de la liste négo.

REPÈRES TECHNIQUES
- Client API : hektor_pipeline/common.py (HektorClient, get_json). Listings paginés.
  La réponse listNegos est dans la clé « res » en live, « data » dans le raw stocké.
- Index local : data/hektor.sqlite. Raw API dans raw_api_response (endpoints
  list_annonces_active/archived, list_contacts_active/archived, listNegos).
- Supabase ref : projet dwaqxfrinihnychuoptk. Annuaire négo =
  app_hektor_negotiator_agency_directory (colonne is_active).
- PÉRIMÈTRE COMPLET (À RE-MESURER, mes 1ers chiffres ne portaient QUE sur le current
  Supabase = FAUX) :
  * Annonces : ~56 563 au total (local hektor_annonce) ; dont ~26 044 avec un négo.
    Réparties Supabase : current 13 510 + archive 34 397 + historical 8 745.
  * Contacts : ~354 657 au total (local hektor_contact) ; dont ~72 704 avec un négo ;
    seulement ~57 127 synchronisés dans Supabase.
  * Orphelins (négo absent de l'annuaire) : ~0 (1 contact). La répartition
    actif/inactif sur ce périmètre complet reste à mesurer via listNegos.

RÈGLES DE DÉVELOPPEMENT (les mêmes que sur tout le projet — à respecter strictement)
- NE PAS ÉCRASER LE CODE EXISTANT : changements ADDITIFS / CHIRURGICAUX uniquement,
  jamais de remplacement massif. Respecter le style du code autour.
- PROD = CONFIRMATION AU COUP PAR COUP : STOP OBLIGATOIRE avant toute écriture prod
  (Supabase, Hektor) et avant toute migration. On présente l'action exacte et on
  attend un « oui » explicite et spécifique (un « vas y » global ne suffit pas — le
  garde-fou bloque sinon). Les migrations Supabase = OK seulement au coup par coup.
- LECTURE SEULE CETTE SESSION : extraire + comparer + chiffrer. AUCUNE écriture
  local/Supabase/Hektor, AUCUNE migration. Le script de correction viendra après.
- CREDENTIALS : je n'entre JAMAIS de mot de passe / accès (refuser un accès
  provisoire). Si une action exige une connexion, c'est l'utilisateur qui la fait.
- VÉRIFIER EN LIGNE / CONSOLE D'ABORD : un écran qui « plante » = lire la console JS
  du site déployé AVANT de suspecter la couche données (l'app lit Supabase en
  authenticated, pas anon).
- DÉPLOIEMENT (pour plus tard, pas cette session) : front = git push origin
  refonte-mobile:main (→ Vercel). Worker = 4 services Windows, RESTART par
  l'utilisateur (Get-Service HektorConsoleWorker* | Restart-Service -Force).
  Fin de message commit : Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>.
- ENTITÉS DE TEST UNIQUEMENT : annonce VA6482 (app_dossier 1068399, hektor_annonce
  24113), contact 603798. Ne pas toucher aux biens/contacts d'autres négos sans accord.
- ALLER À L'ESSENTIEL : agir quand on a de quoi agir, ne pas re-dériver des faits
  déjà établis, recommander plutôt que dérouler toutes les options.
- OUTIL existant : refresh_annonce_nego_from_api.py (re-fetch négo d'une annonce).

LIVRABLE : un rapport clair du volume exact d'écarts (annonces + contacts), avec la
répartition identique / différent / actif-inactif / orphelin, pour décider ensuite
du script de correction (niveau 1 = alignement auto ; niveau 2 = réaffectation
métier des cas restés sur un négo inactif).
```

---

## 🎯 STRATÉGIE N°1 — Fallback AGENCE (écrire les entités à négo inactif sans réaffecter)

**Acquis (testé 2026-06-22)** : un négo INACTIF (générique OU personne partie) n'est PAS
impersonnable par le worker → écriture impossible par le chemin négo. MAIS écrire via le
contexte **AGENCE** marche (testé end-to-end : prix écrit dans Hektor sur une annonce idnego 2
inactif, sans réaffecter). → Pas besoin de réaffectation massive : **fallback agence**.

**Audit des zones (2026-06-22)** : toute écriture Hektor via impersonation passe par **UN seul
point** = `ensureHektorExecutionContext` (console_job_worker.js). ~15 appelants (annonce :
update_fields/change_status/create_draft/restore/photos/documents/link_mandant ; contact :
create/update/recherche). **Backend + Python n'écrivent PAS dans Hektor via négo** (confirmé,
seul console_job_worker.js a switchHektorUserContext/upval).

**Implémenté (2026-06-22, NON committé, dans le worker)** : fallback centralisé dans
`ensureHektorExecutionContext` — si aucun négo ACTIF résolu → résout le contexte agence
(`resolveAgencyContextForFallback` : annonce via `resolveHektorAnnonceAgencyContext`, contact via
payload) + `ensureHektorAgencySession` au lieu de throw. **Flag-gated** :
`CONSOLE_HEKTOR_AGENCY_FALLBACK=true` (env) OU `write_via_agency:true` (payload). Sans flag =
100% inchangé. Le prototype `write_via_agency` dans handleUpdateHektorAnnonceFields a été retiré
(redondant).

**⚠️ RAFFINEMENT DÉCOUVERT au test (2026-06-22) — la DÉTECTION est à revoir** :
le fallback centralisé (déclenché sur `target.idUser` null) **ne fire PAS** car
`resolveHektorExecutionUser` est « malin » : quand le négo propriétaire est inactif, il
résout un **COLLÈGUE actif de la même agence** (ligne 1395/1422, `resolveHektorNegotiatorFromAgencyDirectory`)
→ target non-null → pas de fallback. Et le collègue **ne peut pas** écrire le prix d'une
annonce qui n'est pas la sienne → Hektor « modification directe du prix refusée, workflow
mandat/statut ». Or l'**AGENCE (admin) le PEUT** (test direct réussi via write_via_agency forcé).
Règle Hektor apprise : négo propriétaire actif ✅, négo collègue ❌, agence/admin ✅.
→ **CORRIGER LA DÉTECTION** : déclencher le fallback agence quand **le négo PROPRE de l'entité
(dossier.commercial_id / negociateur_email) est inactif** — NE PAS se contenter du « no négo
résolu » (un collègue résout toujours). 2 pistes : (a) court-circuiter `resolveHektorExecutionUser`
et tester directement l'activité du négo propriétaire ; (b) retry-via-agence sur l'erreur
« modification directe refusée ». État actuel : fallback centralisé IMPLÉMENTÉ mais détection
insuffisante → **à reprendre en session dédiée** (chaque essai = restart worker).

**RESTE À FAIRE** : (1) corriger la détection (ci-dessus) ; (2) **valider par TYPE d'écriture**
(photos/docs/change_status/create) ; (3) activer en prod (env flag) ; (4) commit si validé.
NB change_status (transactionMode offre/compromis/vente) à vérifier.

## Rappel des 2 niveaux du chantier (après le mapping)
1. **Alignement automatique** : script re-fetch annonces + contacts → écrase l'idnego
   en local + Supabase. Corrige les écarts type VA6482.
2. **Réaffectation métier** : pour les entités restées chez Hektor sur un négo
   inactif/parti → décision humaine (à qui réattribuer), volume réduit.
