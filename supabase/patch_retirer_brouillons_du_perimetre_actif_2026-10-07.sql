-- ============================================================================
-- RETIRER LES 441 BROUILLONS DU PERIMETRE ACTIF                     07/10/2026
-- ============================================================================
-- CE QUI S'EST PASSE. Le 07/10 a 09:52, un push lance avec `--all-local-current`
-- a envoye au cloud TOUT le perimetre local, brouillons compris :
--     app_dossier_current  13 463 -> 13 904   (+441)
--     et l'ecran « annonces actives » est passe de 724 a 949 (+225)
--
-- POURQUOI. Le perimetre actif de l'app CONTIENT les brouillons, parce que le
-- filtre qui devrait les exclure est derriere un interrupteur ETEINT :
--     export_app_payload.BROUILLON_BUCKET_ENABLED = False
--     -> brouillon_active_exclusion_sql() rend une chaine VIDE
-- La SEULE chose qui les tenait hors du cloud etait le filtre INCREMENTIEL du
-- push de nuit (il n'envoie que ce qui a bouge recemment, et ces brouillons
-- datent du 01/10). `--all-local-current` contourne exactement ce filtre.
--
-- ⚠ ON NE TOUCHE PAS A `BROUILLON_BUCKET_ENABLED` : il commande la feature
--   brouillon d'un AUTRE developpeur, et l'allumer changerait le perimetre de
--   l'app partout. Ce patch ne repare que la consequence.
--
-- CE QUI RASSURE SUR L'EXACTITUDE. La doublure descendue a 08:15 -- donc l'etat
-- du cloud AVANT ce push -- contenait 0 brouillon. Retirer ces 441 restaure donc
-- l'etat d'avant AU NOMBRE PRES, sans rien perdre d'autre.
--
-- ⚠ RIEN N'EST PERDU : ces 441 annonces restent dans
--   app_brouillon_annonce_index_current (508 lignes), qui est leur place, et le
--   miroir local garde tout.
-- ⚠ LE REGISTRE N'EST PAS TOUCHE. Un seul brouillon y a une ligne -- annonce
--   63087, mandat 18923 -- et elle est LEGITIME : un mandat signe figure au
--   registre, c'est sa definition.
-- ============================================================================

-- ── 1. L'ETAT AVANT, a lire et a garder ────────────────────────────────────
select (select count(*) from public.app_dossier_current)                      as fiches_actives,
       (select count(*) from public.app_dossier_current where statut_annonce
          in ('Actif','Sous offre','Sous compromis'))                         as ecran_annonces_actives,
       (select count(*) from public.app_dossier_current d
          join public.app_brouillon_annonce_index_current b using (hektor_annonce_id)) as brouillons_a_retirer;
-- ATTENDU : 13 904 · 949 · 441
-- ⛔ SI `brouillons_a_retirer` N'EST PAS 441, NE PAS CONTINUER : l'etat a bouge
--    depuis la mesure, il faut re-mesurer avant de supprimer.

-- ── 2. LA SUPPRESSION, EN UN SEUL BLOC ─────────────────────────────────────
-- Tout ou rien : si une ligne resiste, la transaction entiere est annulee.
-- L'ORDRE COMPTE : les travaux d'abord, car leur filtre LIT app_dossier_current.
begin;

with cibles as (
  select d.app_dossier_id
    from public.app_dossier_current d
    join public.app_brouillon_annonce_index_current b using (hektor_annonce_id)
)
delete from public.app_work_item_current
 where app_dossier_id in (select app_dossier_id from cibles);

delete from public.app_dossier_detail_current
 where hektor_annonce_id in (select hektor_annonce_id
                               from public.app_brouillon_annonce_index_current);

delete from public.app_dossier_current
 where hektor_annonce_id in (select hektor_annonce_id
                               from public.app_brouillon_annonce_index_current);

commit;

-- ── 3. L'ETAT APRES ────────────────────────────────────────────────────────
select (select count(*) from public.app_dossier_current)                      as fiches_actives,
       (select count(*) from public.app_dossier_current where statut_annonce
          in ('Actif','Sous offre','Sous compromis'))                         as ecran_annonces_actives,
       (select count(*) from public.app_dossier_current d
          join public.app_brouillon_annonce_index_current b using (hektor_annonce_id)) as brouillons_restants,
       (select count(*) from public.app_brouillon_annonce_index_current)       as index_brouillon_intact,
       (select count(*) from public.app_mandat_register_current)               as registre_intact;
-- ATTENDU : 13 463 · 724 · 0 · 508 · 24 494

-- ── ET CE QUI RESTE A DECIDER, PLUS TARD ───────────────────────────────────
-- Le trou est STRUCTUREL : tant que BROUILLON_BUCKET_ENABLED est eteint, tout
-- push COMPLET (--all-local-current, --full-rebuild, une base neuve) refera
-- entrer les brouillons dans le perimetre actif. Deux issues, et c'est un
-- arbitrage, pas une reparation :
--     a) allumer l'interrupteur -> a voir avec le dev de la feature brouillon
--     b) ne plus jamais lancer de push complet -> fragile, ca s'oublie
-- ============================================================================
