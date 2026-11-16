-- ═══════════════════════════════════════════════════════════════════════════
-- LE VERROU DES TABLES DU CHANTIER CLASSEUR -- 16/11/2026
--
-- DEMANDE PAR FREDERIC le 16/11 : « il faut aussi faire ce verrou », puis
-- « Les quatre » apres l'audit.
--
-- ⛔⛔ CE QUE L'AUDIT A TROUVE, ET C'EST PIRE QUE CE QUE JE CROYAIS. Je venais
--   signaler UN oubli sur `app_classeur_avis` (ma table, posee la veille). Le
--   balayage en a trouve TROIS AUTRES, et plus graves :
--
--     table                     RLS      politiques   authenticated
--     app_classeur_lien         DESACTIVEE    0        TOUT, TRUNCATE comprise
--     app_classeur_ligne_id     DESACTIVEE    0        TOUT
--     app_charge_exclusion      DESACTIVEE    0        TOUT
--     app_classeur_avis         active        0        TOUT
--
--   ⭐ LA DIFFERENCE EST CAPITALE : sans RLS, il n'y a AUCUN gardien devant la
--     porte -- le droit suffit. Les TROIS PREMIERES sont donc REELLEMENT
--     ouvertes : n'importe quel compte de l'app peut aujourd'hui lire, modifier,
--     supprimer ou VIDER le gel entier (12 595 liens) et le pont (4 773
--     identites). Ce sont le SOCLE du chantier.
--     `app_classeur_avis`, elle, a RLS active SANS politique : la RLS refuse
--     tout, donc elle est fermee en pratique. Mon oubli etait le MOINS grave des
--     quatre.
--
-- ⛔⛔⛔ ET LA FAUTE EST DEJA DANS LA MEMOIRE DU PROJET, sous le nom
--   « `revoke all from public` NE FERME PAS `authenticated` ». Mon patch B1
--   faisait `revoke all ... from public` et je l'ai cru suffisant. `public` et
--   `authenticated` sont DEUX roles differents : fermer l'un laisse l'autre
--   grand ouvert. Je l'ai refaite le lendemain de l'avoir notee.
--
-- ⭐ AUCUN RISQUE FONCTIONNEL, ET C'EST MESURE : aucune de ces quatre tables
--   n'est citee dans apps/ ni backend/ (grep du 16/11). Seuls les scripts du
--   chantier les utilisent, et ils passent par la CLE DE SERVICE, que ces
--   droits ne concernent pas. Le run de nuit non plus.
--
-- CE QUE CE PATCH NE FAIT PAS : il n'active pas la RLS sur les trois tables qui
--   ne l'ont pas. Retirer le droit SUFFIT a fermer la porte, et activer la RLS
--   sans politique sur une table que des scripts lisent demanderait de verifier
--   chaque lecteur un par un -- un autre geste, un autre jour.
--
-- Retour arriere : patch_verrou_tables_classeur_2026-11-16_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare ouvertes integer;
begin
  select count(*) into ouvertes
    from information_schema.role_table_grants
   where table_schema = 'public' and grantee = 'authenticated'
     and privilege_type = 'TRUNCATE'
     and table_name in ('app_classeur_lien', 'app_classeur_ligne_id',
                        'app_charge_exclusion', 'app_classeur_avis');
  if ouvertes = 0 then
    raise exception '⛔ ARRET : les quatre tables sont DEJA fermees. Quelqu''un est '
      'passe avant -- relire avant de rejouer.';
  end if;
  raise notice '✅ etat d''avant : % des 4 tables portent encore le passe.', ouvertes;
end $$;

-- ─── 2. LE VERROU ──────────────────────────────────────────────────────────
-- ⚠ ON NE TOUCHE PAS A `service_role` NI A `postgres` : ce sont eux qui font
--   tourner le run, les patchs et les scripts du chantier.
revoke all on public.app_classeur_lien      from authenticated, anon;
revoke all on public.app_classeur_ligne_id  from authenticated, anon;
revoke all on public.app_charge_exclusion   from authenticated, anon;
revoke all on public.app_classeur_avis      from authenticated, anon;

-- ─── 3. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  reste    integer;
  service  integer;
  voisines integer;
begin
  -- 3a plus aucun droit pour authenticated ni anon sur les quatre
  select count(*) into reste
    from information_schema.role_table_grants
   where table_schema = 'public' and grantee in ('authenticated', 'anon')
     and table_name in ('app_classeur_lien', 'app_classeur_ligne_id',
                        'app_charge_exclusion', 'app_classeur_avis');
  if reste <> 0 then
    raise exception '⛔ il reste % droit(s) pour authenticated/anon.', reste;
  end if;

  -- 3b ⭐ LE TEMOIN POSITIF, et il compte autant que le reste : service_role
  --   DOIT garder ses droits, sinon le run de nuit tombe demain matin.
  select count(*) into service
    from information_schema.role_table_grants
   where table_schema = 'public' and grantee = 'service_role'
     and privilege_type = 'SELECT'
     and table_name in ('app_classeur_lien', 'app_classeur_ligne_id',
                        'app_charge_exclusion', 'app_classeur_avis');
  if service <> 4 then
    raise exception '⛔⛔ service_role ne lit plus que % table(s) sur 4. LE RUN '
      'TOMBERAIT. Jouer l''INVERSE tout de suite.', service;
  end if;

  -- 3c ⭐ TEMOIN INVERSE : on n'a pas deborde sur les voisines du registre.
  select count(*) into voisines
    from information_schema.role_table_grants
   where table_schema = 'public' and grantee = 'authenticated'
     and privilege_type = 'SELECT'
     and table_name in ('app_affaire_ledger', 'app_affaire_note',
                        'app_affaire_condition', 'app_dossier_current');
  if voisines <> 4 then
    raise exception '⛔ une voisine a perdu sa lecture (% sur 4). Le patch a '
      'deborde.', voisines;
  end if;

  raise notice '✅ 4 tables fermees a authenticated et anon . service_role lit '
    'toujours les 4 . les 4 voisines du registre INTACTES.';
end $$;

commit;
