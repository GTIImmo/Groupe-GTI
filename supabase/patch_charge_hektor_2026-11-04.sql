-- =====================================================================
-- ETAPE (2) DE LA CHARGE : LE MIROIR, LA OU LE CLASSEUR SE TAIT -- 04/11/2026
-- =====================================================================
-- SA DECISION : « ensuite b et c » -- b = poser la charge que Hektor nous
-- descend, la ou le classeur ne dit rien.
--
-- ⭐ LA NUANCE QUI AUTORISE CE GESTE, et que j'avais mal posee le 03/11 :
--   le juge a montre que Hektor n'apporte que +1,3 point LA OU LE CLASSEUR
--   PARLE DEJA (97,9 % contre 96,4 % pour « toujours vendeur », verifie le
--   04/11 sur les 837 posees -- echantillon 2x celui du juge).
--   Il n'a JAMAIS montre que Hektor etait inutile LA OU LE CLASSEUR EST MUET :
--   23 737 mandats sur 24 574. Du vide ne vaut pas 95 %, il ne vaut RIEN.
--
-- L ORDRE DE PRECEDENCE, desormais complet :
--     SAISIE HUMAINE  >  LE CLASSEUR  >  HEKTOR  >  defaut « vendeur »
--   Chaque valeur garde SA PROVENANCE, donc on peut retirer UNE SEULE source
--   sans toucher aux autres.
--
-- =====================================================================
-- CE QUI A ETE POSE, MESURE
-- =====================================================================
--   carnet       23 475   =  837 classeur + 22 638 hektor + 0 saisie
--   registre     23 475   (reflet fidele : 0 ecart)
--   dont hektor  22 638   =  22 543 vendeur + 95 acquereur
--   couverture     95,5 % du registre  (elle etait a 3,4 %)
--   les 837 du classeur : INTACTES (garde « carnet vide seulement »)
--
-- =====================================================================
-- ⛔⛔ DEUX FAUSSES ALERTES QUE J AI LEVEES MOI-MEME, A NE PAS REFAIRE
-- =====================================================================
-- 1. « L EXTRACTION SQL NE TROUVE AUCUN ACQUEREUR » -- vrai, et la cause etait
--    mon REGEX : dans `register_detail_payload_json`, l'accent est ECHAPPE
--    (« Honoraires acquéreur ou locataire »), donc `acqu\w*reur` ne mord
--    pas. ⭐ LE REMEDE : s'accrocher aux mots SANS ACCENT, « ou bailleur
--    montant » et « ou locataire », qui sont stables.
--
-- 2. « LE PAYLOAD EST UNE ENVELOPPE, 96,8 % disent detail_available:false, donc
--    la voie SQL est morte » -- FAUX, et j'ai failli jeter la bonne methode.
--    Le drapeau coexiste avec le texte des honoraires. ⭐ Ce qui l'a tranche :
--    les DEUX chemins convergent. Le miroir local et le payload trouvent tous
--    deux 95 acquereurs posables.
--
-- 3. ⛔ ET MON « TRESOR DE 1 813 ACQUEREURS » ETAIT FAUX. Le miroir local porte
--    1 813 paires (annonce x mandat) a charge acquereur, mais 1 718 de ces
--    mandats N EXISTENT PAS au registre. Posables : 95.
--    ⭐ LA LECON : un compte de paires issues d'un blob n'est pas un compte de
--      lignes posables. Croiser avec la cible AVANT d'annoncer un gisement.
--
-- =====================================================================
-- LES GARDES, ECRITES DANS LA REQUETE
-- =====================================================================
--   GARDE 1  le carnet doit etre VIDE pour (annonce, mandat) : on n'ecrase ni
--            une saisie humaine ni le classeur.
--   GARDE 2  les DEUX cases remplies -> on ECARTE (indecidable). 5 lignes.
--            Controle : c10 verifie qu'aucune ligne posee n'a les deux cases.
--   GARDE 3  on prend la DERNIERE occurrence (WITH ORDINALITY ... order by n
--            desc) : le bloc est un HISTORIQUE, jusqu'a 6 lignes, et la charge
--            y bascule parfois (14 annonces mesurees le 03/11).
--
-- ⛔ PREALABLE OBLIGATOIRE, SANS QUOI LA PREMIERE REPOSE EFFACE LES 22 638 :
--   app_reposer_charge_mandat_app et app_set_mandat_charge_optimistic doivent
--   connaitre la 3e origine. Le bloc ci-dessous le fait, avec garde-fou.
--
-- SAUVEGARDES : app_sauvegarde_charge_avant_hektor_20261104 (le carnet d'avant,
--   841 lignes), app_sauvegarde_fonction_20261104 (les fonctions + empreintes).
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. LES DEUX FONCTIONS APPRENNENT LA 3e ORIGINE
-- ---------------------------------------------------------------------
do $$
declare src text; src2 text; n int;
begin
  select pg_get_functiondef(p.oid) into src from pg_proc p
    join pg_namespace n2 on n2.oid = p.pronamespace
   where p.proname = 'app_reposer_charge_mandat_app' and n2.nspname = 'public';
  if md5(src) <> '4a1af5f3de4f160a9c4e03cf09688674' then
    raise exception 'ARRET : la repose n est pas celle du 04/11 (md5 %)', md5(src);
  end if;
  src2 := replace(src, 'in (''mandat_app'', ''classeur'')',
                       'in (''mandat_app'', ''classeur'', ''hektor'')');
  n := (select count(*) from regexp_matches(src2,
          'in \(''mandat_app'', ''classeur'', ''hektor''\)', 'g'));
  if n <> 3 then raise exception 'ARRET : % elargissements, 3 attendus', n; end if;
  execute src2;

  select pg_get_functiondef(p.oid) into src from pg_proc p
    join pg_namespace n2 on n2.oid = p.pronamespace
   where p.proname = 'app_set_mandat_charge_optimistic' and n2.nspname = 'public';
  if md5(src) <> '5a71b9c660a182dbfa2139eaa053c34f' then
    raise exception 'ARRET : la porte de saisie n est pas celle du 04/11 (md5 %)', md5(src);
  end if;
  src2 := replace(src, 'in (''mandat_app'', ''classeur'')',
                       'in (''mandat_app'', ''classeur'', ''hektor'')');
  n := (select count(*) from regexp_matches(src2,
          'in \(''mandat_app'', ''classeur'', ''hektor''\)', 'g'));
  if n <> 1 then raise exception 'ARRET : % elargissements, 1 attendu', n; end if;
  -- ⛔ L ECRITURE DOIT RESTER 'mandat_app' : c'est elle qui rend la main a l'humain
  n := (select count(*) from regexp_matches(src2, 'origine\s*=\s*''mandat_app'',', 'g'));
  if n <> 1 then raise exception 'ARRET : l ecriture mandat_app a disparu (%)', n; end if;
  execute src2;
end $$;

-- ---------------------------------------------------------------------
-- 2. LA POSE
-- ---------------------------------------------------------------------
with ex as (
  select r.hektor_annonce_id::text as ann, r.numero_mandat::text as man,
    (select t.mv[1]::numeric from regexp_matches(r.register_detail_payload_json::text,
        'ou bailleur montant\s*:\s*([0-9]+(?:\.[0-9]+)?)', 'g')
        with ordinality as t(mv, n) order by t.n desc limit 1) as v,
    (select t.mv[1]::numeric from regexp_matches(r.register_detail_payload_json::text,
        'ou locataire\s*:\s*([0-9]+(?:\.[0-9]+)?)', 'g')
        with ordinality as t(mv, n) order by t.n desc limit 1) as a
    from public.app_mandat_register_current r
   where r.numero_mandat is not null
     and r.register_detail_payload_json is not null
     and not exists (select 1 from public.app_mandat_champ_app k
                      where k.champ = 'charge_commission'
                        and k.hektor_annonce_id = r.hektor_annonce_id::text
                        and k.numero_mandat = r.numero_mandat::text)
     -- GARDE 4 (05/11/2026) : LES EXCLUSIONS DECLAREES. Sa decision « C » sur les
     --   2 mandats que le CLASSEUR se contredit lui-meme. ⚠ CETTE GARDE MANQUAIT
     --   LE 04/11, et ca s'est vu : la pose du miroir avait rempli 46338/17322
     --   avec « vendeur » -- precisement le point conteste. Retiree le 05/11.
     --   ⛔ TOUTE porte qui pose la charge DOIT consulter cette table.
     and not exists (select 1 from public.app_charge_exclusion e
                      where e.hektor_annonce_id = r.hektor_annonce_id::text
                        and e.numero_mandat = r.numero_mandat::text)
), q as (
  select ann, man,
         case when coalesce(v,0) > 0 and coalesce(a,0) > 0 then null
              when coalesce(v,0) > 0 then 'vendeur'
              when coalesce(a,0) > 0 then 'acquereur'
              else null end as charge
    from ex
), poses as (
  insert into public.app_mandat_champ_app
    (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
  select ann, man, 'charge_commission', charge, 'hektor', 'hektor:payload_registre', now()
    from q where charge is not null
  on conflict (hektor_annonce_id, numero_mandat, champ) do nothing
  returning valeur_app)
select count(*) as posees,
       count(*) filter (where valeur_app = 'vendeur') as vendeur,
       count(*) filter (where valeur_app = 'acquereur') as acquereur
  from poses;
-- attendu : 22 638 posees, 22 543 vendeur, 95 acquereur

-- ---------------------------------------------------------------------
-- 3. LE REFLET
-- ---------------------------------------------------------------------
select public.app_reposer_charge_mandat_app(null, 10000) as repose;
-- attendu : posees 22 638, effacees 0, lignes_carnet 23 475

-- ---------------------------------------------------------------------
-- 4. LE CONTROLE -- les 10 colonnes doivent etre vertes
-- ---------------------------------------------------------------------
select
  (select count(*) from app_mandat_champ_app where champ='charge_commission') = 23475
    as c01_carnet_23475,
  (select count(*) from app_mandat_champ_app
    where champ='charge_commission' and origine='classeur') = 837
    as c02_les_837_du_classeur_INTACTES,
  (select count(*) from app_mandat_champ_app
    where champ='charge_commission' and origine='hektor') = 22638
    as c03_hektor_22638,
  (select count(*) from app_mandat_register_current
    where nullif(trim(coalesce(mandat_charge_honoraires_app,'')),'') is not null) = 23475
    as c04_registre_23475,
  (select count(*) from app_mandat_champ_app k join app_mandat_register_current r
      on r.hektor_annonce_id::text = k.hektor_annonce_id
     and r.numero_mandat::text = k.numero_mandat
    where k.champ='charge_commission'
      and coalesce(r.mandat_charge_honoraires_app,'') <> k.valeur_app) = 0
    as c05_reflet_fidele,
  (select count(*) from app_mandat_champ_app where champ='charge_commission'
     and valeur_app not in ('vendeur','acquereur')) = 0
    as c06_vocabulaire_propre,
  -- ⭐ TEMOIN POSITIF sur la classe RARE : sans lui, les zeros ci-dessus ne valent rien
  (select count(*) from app_mandat_champ_app
    where champ='charge_commission' and origine='hektor' and valeur_app='acquereur') = 95
    as c07_temoin_positif_95_acquereurs,
  -- ⭐ TEMOIN INVERSE : aucune ligne « les DEUX cases » n'a ete posee
  (select count(*) from app_mandat_champ_app k
    where k.champ='charge_commission' and k.origine='hektor'
      and exists (select 1 from app_mandat_register_current r
                   where r.hektor_annonce_id::text = k.hektor_annonce_id
                     and r.numero_mandat::text = k.numero_mandat
                     and r.register_detail_payload_json::text ~ 'ou bailleur montant\s*:\s*[1-9]'
                     and r.register_detail_payload_json::text ~ 'ou locataire\s*:\s*[1-9]')) = 0
    as c08_aucune_ligne_aux_deux_cases,
  (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname='app_reposer_charge_mandat_app'
      and pg_get_functiondef(p.oid) like '%''hektor''%') = 1
    as c09_la_repose_voit_hektor,
  (select count(*) from app_sauvegarde_charge_avant_hektor_20261104) = 841
    as c10_la_sauvegarde_existe;

-- ---------------------------------------------------------------------
-- RETOUR ARRIERE -- une seule commande, parce que la PROVENANCE est ecrite
-- ---------------------------------------------------------------------
-- ⚠ COMMENTE EXPRES. Il ne touche QUE les lignes origine='hektor' : le classeur
--   et les saisies humaines restent INTACTS.
--
-- delete from public.app_mandat_champ_app
--  where champ='charge_commission' and origine='hektor';
-- select public.app_reposer_charge_mandat_app(null, 10000) as repose;
-- -- la repose doit alors annoncer « effacees » = 22 638.
--
-- ⬜ ET SI ON VOULAIT AUSSI DEFAIRE L ELARGISSEMENT DES FONCTIONS : les
--   definitions d'avant sont dans app_sauvegarde_fonction_20261104, mais ⛔ ne
--   PAS les remettre tant que des lignes origine='hektor' ou 'classeur' vivent
--   -- la repose redeviendrait aveugle et les effacerait du registre.
