-- =====================================================================
-- ETAPE (1) DE LA CHARGE : LE CLASSEUR FAIT FOI -- 04/11/2026
-- =====================================================================
-- SES DEUX DECISIONS DU 04/11 :
--   1. « go »  -> on pose la charge du classeur sur le registre des mandats
--   2. « oui » -> LA VALEUR DU CLASSEUR FAIT FOI, comme une saisie humaine
--                 -> elle va AU CARNET, avec origine = 'classeur'
--
-- CE PATCH NE POSE PAS LES DONNEES. Il prepare le terrain, et il est
-- INDISPENSABLE AVANT :
--   patch_charge_classeur_2026-11-04_DONNEES.sql (les 837 lignes)
--
-- =====================================================================
-- ⛔⛔ POURQUOI CE PATCH EXISTE : SANS LUI, LA PREMIERE REPOSE EFFACE TOUT
-- =====================================================================
-- app_reposer_charge_mandat_app filtre « origine = 'mandat_app' » AUX
-- QUATRE ENDROITS, y compris dans sa partie EFFACEMENT :
--
--     UPDATE app_mandat_register_current SET mandat_charge_honoraires_app = NULL
--      WHERE ... AND NOT EXISTS (SELECT 1 FROM app_mandat_champ_app k
--                                 WHERE k.origine = 'mandat_app' ...)
--
-- Donc une valeur du registre SANS ligne « mandat_app » est effacee.
-- Les 837 lignes du classeur auraient ete balayees au premier passage.
--
-- ⚠ ELLE N'EST APPELEE PAR PERSONNE AUJOURD'HUI -- mesure du 04/11, avec
--   temoin positif : sa soeur app_reposer_cloture_mandat_app EST appelee
--   (phase2/sync/push_single_annonce_to_supabase.py:710), celle de la
--   charge n'apparait dans aucun .py/.js/.ps1/.ts du depot.
--   C'est donc un MECANISME INSTALLE A MOITIE : le jour ou quelqu'un
--   l'ajoute au run par symetrie avec la cloture, il detruit tout.
--   « Une reserve d'audit non traitee devient le bug. »
--
-- =====================================================================
-- CE QUE LE PATCH CHANGE, ET RIEN DE PLUS
-- =====================================================================
--   A. app_reposer_charge_mandat_app : ses 3 filtres de LECTURE passent de
--      « = 'mandat_app' » a « in ('mandat_app', 'classeur') ».
--      Les 3 sont des lectures -- verifie par regex avant remplacement.
--
--   B. app_set_mandat_charge_optimistic : SON DELETE SEULEMENT passe aux
--      deux origines, pour que l'ecran puisse VIDER une charge venue du
--      classeur, et pas seulement la changer. C'est la consequence de sa
--      decision n° 2 : « elle fait foi » = elle se comporte comme une saisie.
--
--      ⛔ SON INSERT GARDE « origine = 'mandat_app' » : c'est lui qui rend
--         la main a l'humain. Une saisie ecrase la valeur du classeur et
--         reprend l'origine. Le patch VERIFIE qu'il est intact (le compte
--         d'ecritures 'mandat_app' doit rester a 1) et s'ARRETE sinon.
--
-- ⚠ LE PIEGE QUI A FAIT MORDRE LE GARDE-FOU : la porte de saisie porte
--   DEUX occurrences de « origine ... 'mandat_app' » -- le filtre du DELETE
--   et l'ECRITURE du DO UPDATE. Un remplacement global aurait casse la
--   reprise en main par l'humain. On distingue par « AND » : le DELETE est
--   le seul a l'avoir.
--
-- SAUVEGARDE : app_sauvegarde_fonction_20261104 (4 fonctions, avec empreintes)
--              app_sauvegarde_charge_avant_20261104 (le carnet d'avant)
-- RETOUR ARRIERE : patch_charge_classeur_2026-11-04_INVERSE.sql
-- CONTROLE       : patch_charge_classeur_2026-11-04_REPETITION.sql
-- =====================================================================

do $$
declare src text; src2 text; n int;
begin
  -- ===== A. LA REPOSE =====
  select pg_get_functiondef(p.oid) into src
    from pg_proc p join pg_namespace n2 on n2.oid=p.pronamespace
   where p.proname='app_reposer_charge_mandat_app' and n2.nspname='public';
  if md5(src) <> 'f84d178ea95e06e030a5c5a2681dfb6f' then
    raise exception 'ARRET : la repose a change depuis la mesure du 04/11 (md5 %)', md5(src);
  end if;
  src2 := regexp_replace(src, '(AND\s+k?\.?origine\s*)=(\s*)''mandat_app''',
                              '\1in (''mandat_app'', ''classeur'')', 'g');
  n := (select count(*) from regexp_matches(src2, 'in \(''mandat_app'', ''classeur''\)', 'g'));
  if n <> 3 then raise exception 'ARRET : % elargissements dans la repose, 3 attendus', n; end if;
  if src2 ~ 'origine\s*=\s*''mandat_app''' then
    raise exception 'ARRET : il reste un filtre etroit dans la repose';
  end if;
  if src2 not like '%plancher%' or src2 not like '%effacements%' or src2 not like '%poses%' then
    raise exception 'ARRET : le remplacement a abime la repose';
  end if;
  execute src2;

  -- ===== B. LE DELETE DE LA PORTE DE SAISIE, LUI SEUL =====
  select pg_get_functiondef(p.oid) into src
    from pg_proc p join pg_namespace n2 on n2.oid=p.pronamespace
   where p.proname='app_set_mandat_charge_optimistic' and n2.nspname='public';
  if md5(src) <> '9c96157ba520c57156a82fd987f193f0' then
    raise exception 'ARRET : la porte de saisie a change (md5 %)', md5(src);
  end if;
  src2 := regexp_replace(src, '(AND\s+origine\s*)=(\s*)''mandat_app''',
                              '\1in (''mandat_app'', ''classeur'')', 'g');
  n := (select count(*) from regexp_matches(src2, 'in \(''mandat_app'', ''classeur''\)', 'g'));
  if n <> 1 then raise exception 'ARRET : % elargissements dans la saisie, 1 attendu', n; end if;
  n := (select count(*) from regexp_matches(src2, 'origine\s*=\s*''mandat_app'',', 'g'));
  if n <> 1 then raise exception 'ARRET : l ecriture mandat_app a disparu (% trouvee) -- la saisie perdrait la main', n; end if;
  if src2 not like '%charge_invalide%' or src2 not like '%mandat_introuvable%' then
    raise exception 'ARRET : le remplacement a abime la porte de saisie';
  end if;
  execute src2;
end $$;

-- ---------------------------------------------------------------------
-- CONTROLE IMMEDIAT
-- ---------------------------------------------------------------------
select p.proname,
       (select count(*) from regexp_matches(pg_get_functiondef(p.oid),
          'in \(''mandat_app'', ''classeur''\)', 'g')) as filtres_elargis,
       (select count(*) from regexp_matches(pg_get_functiondef(p.oid),
          'origine\s*=\s*''mandat_app'',', 'g')) as ecritures_preservees
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public'
   and p.proname in ('app_reposer_charge_mandat_app','app_set_mandat_charge_optimistic')
 order by 1;
-- attendu : la repose 3 et 0 . la saisie 1 et 1
