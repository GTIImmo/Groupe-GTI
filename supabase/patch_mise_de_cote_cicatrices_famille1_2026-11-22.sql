-- ═══════════════════════════════════════════════════════════════════════════════
-- METTRE DE COTE LES 3 CICATRICES DE LA FAMILLE 1 (cause etablie)          22/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⛔ FABRIQUE, NON JOUE. Son mot du 22/11 (« le patch est accorde », § 4) : « FAMILLE 1, cause
--   etablie : 1001563, 1001580, 1001482. Fabrique leur mise de cote. » -- et la famille 2
--   (1001561, 1001593) N'EST PAS ICI : « NE LES TOUCHE PAS ».
--
-- CE QUE CE SONT : trois offres posees le 16/11 par le lot du classeur, qui REPRODUISENT une
--   vraie offre de Hektor -- meme bien, meme genre, meme VRAIE date (le journal de l'offre), le
--   MEME acheteur -- dont nos gestes du 11-12/11 avaient deplace la colonne `date` :
--     1001482  UTLG66LE (ligne 4131) bien 10527  jumelle 5055  STAUFFER   refus du 11/11 18:21
--     1001563  A07EC3DH (ligne 535)  bien 5262   jumelle 1876  GUERIN     cascade 11/11 + reacceptee 12/11
--     1001580  3S4ZWOFK (ligne 2388) bien 24733  jumelle 11958 CIMINO     cascade 11/11 + reacceptee 12/11
--              (sa ligne porte « Acquereur DI FORTI ROLLAND, Vendeur CIMINO » : colonnes INVERSEES au
--               classeur -- sa voisine 4113 dit « Vendeur DI FORTI », et Hektor porte CIMINO partout)
--   Chacune est SEULE dans sa chaine, sous un numero ne d'elle seule (scission du 18/11 06:34) :
--   D2019-0649, D2024-0505, D2020-0607. Aucune autre piece ne porte ces etiquettes, aucun avis ne
--   cite ces numeros, aucun verdict du protocole ne s'appuie sur elles (mesure du 22/11).
--
-- ⭐ REGLE 6 : « ON NE SUPPRIME PAS, ON MET DE COTE AVEC SON ANCIEN NUMERO DE DOSSIER ». Chaque
--   ligne part ENTIERE dans une table de garde datee, et le registre des cicatrices garde son
--   ancien numero, son ancienne etiquette, sa jumelle et son pourquoi. L'INVERSE la repose a
--   l'identique.
--
-- ⛔⛔ L'ORDRE, ET IL N'EST PAS NEGOCIABLE (mesure du 22/11, le vrai chainage rejoue sur copie) :
--   SANS 1001563 ET 1001580, LA NUIT D'AUJOURD'HUI RE-REUNIT GUERIN ET PAYSAC (535 / 3540) ET
--   CIMINO ET SOUDANI (2388 / 4113) : leur separation ne tient que par ces copies. Elle ne tient
--   sans elles que par la COUPE « C5 aux portes » -- donc :
--     0. la COUPE des 4 lignes est en production (detachements_manuels.csv + l'interrupteur) ;
--     1. python -X utf8 phase2/checks/mettre_de_cote_cicatrices_du_local_2026-11-22.py --verifier-avant
--        (il refuse si la coupe n'y est pas) ;
--     2. CE PATCH, puis sa REPETITION ;
--     3. le meme script --pour-de-vrai, LE MEME JOUR, AVANT LA NUIT : le registre LOCAL est le
--        maitre, et le push de la nuit les RECREERAIT chez Supabase, SANS leur marque (le trou du
--        18/11, § 4.6 de l'audit independant).
--
-- ⛔ CE QUE CE PATCH NE FAIT PAS : il ne touche NI la colonne `date` (son § 5 : on corrige les
--   lecteurs, jamais la donnee), NI les jumelles 5055 / 1876 / 11958, NI les 187 autres copies, NI
--   quoi que ce soit chez Hektor.
--
-- RETOUR ARRIERE : patch_mise_de_cote_cicatrices_famille1_2026-11-22_INVERSE.sql (+ le local)
-- CONTROLE       : patch_mise_de_cote_cicatrices_famille1_2026-11-22_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

-- ── ① LES GARDES : exactement CES 3 lignes, telles que mesurees -- sinon RIEN n'est ecrit ───
do $$
declare n int; r record;
begin
  select count(*) into n from public.app_affaire_ledger
   where app_affaire_id in (1001482, 1001563, 1001580)
     and transaction_origine = 'classeur' and kind = 'offre' and hektor_affaire_id is null;
  if n <> 3 then
    raise exception '⛔ garde : % ligne(s) conformes au lieu de 3 -- rien n''est ecrit', n;
  end if;
  for r in
    select * from (values (1001482::bigint, 'UTLG66LE', 'D2019-0649', 5055::bigint),
                          (1001563::bigint, 'A07EC3DH', 'D2024-0505', 1876::bigint),
                          (1001580::bigint, '3S4ZWOFK', 'D2020-0607', 11958::bigint)) v(copie, iu, numero, jumelle)
  loop
    -- la copie : son ligne du classeur, son numero, SEULE dans sa chaine et sous son etiquette
    if not exists (select 1 from public.app_affaire_ledger c
                    where c.app_affaire_id = r.copie and c.payload_json ->> 'classeur_id_unique' = r.iu
                      and c.app_dossier_numero = r.numero
                      and (select count(*) from public.app_affaire_ledger x where x.app_chaine_id = c.app_chaine_id) = 1
                      and (select count(*) from public.app_affaire_ledger x where x.app_dossier_uuid = c.app_dossier_uuid) = 1)
    then
      raise exception '⛔ garde : la copie % n''est plus telle que mesuree (ligne %, numero %, seule) -- rien n''est ecrit',
        r.copie, r.iu, r.numero;
    end if;
    -- sa jumelle : la vraie offre de Hektor, a la meme VRAIE date (la fonction de la base)
    if not exists (select 1 from public.app_affaire_ledger j, public.app_affaire_ledger c
                    where j.app_affaire_id = r.jumelle and c.app_affaire_id = r.copie
                      and j.kind = 'offre' and j.hektor_annonce_id = c.hektor_annonce_id
                      and coalesce(j.transaction_origine, '') <> 'classeur'
                      and public.app_dossier_jour_date_transaction(j.kind, j.date, j.propositions_json, j.app_affaire_id)
                          = left(c.date, 10))
    then
      raise exception '⛔ garde : la jumelle % de la copie % n''est plus a sa vraie date -- rien n''est ecrit',
        r.jumelle, r.copie;
    end if;
  end loop;
  if to_regclass('public.app_affaire_ledger_mise_de_cote_cicatrices_20261122') is not null then
    raise exception '⛔ garde : la table de garde existe deja -- ce patch ne se rejoue pas';
  end if;
end $$;

-- ── ② LE REGISTRE DES CICATRICES (permanent) + LES TABLES DE GARDE DATEES ─────────────────
create table if not exists public.app_classeur_cicatrice_mise_de_cote (
  app_affaire_id        bigint primary key,
  id_unique             text not null,
  jumelle               bigint not null,
  ancien_app_chaine_id  bigint,
  ancien_dossier_uuid   uuid,
  ancien_dossier_numero text,
  pourquoi              text not null,
  mis_de_cote_le        timestamptz not null default now(),
  mis_de_cote_par       text not null
);
revoke all on public.app_classeur_cicatrice_mise_de_cote from public, anon, authenticated;

create table public.app_affaire_ledger_mise_de_cote_cicatrices_20261122
  as select * from public.app_affaire_ledger where false;
create table public.app_affaire_note_mise_de_cote_cicatrices_20261122
  as select * from public.app_affaire_note where false;
revoke all on public.app_affaire_ledger_mise_de_cote_cicatrices_20261122 from public, anon, authenticated;
revoke all on public.app_affaire_note_mise_de_cote_cicatrices_20261122 from public, anon, authenticated;

insert into public.app_affaire_ledger_mise_de_cote_cicatrices_20261122
  select * from public.app_affaire_ledger where app_affaire_id in (1001482, 1001563, 1001580);
insert into public.app_affaire_note_mise_de_cote_cicatrices_20261122
  select * from public.app_affaire_note where app_affaire_id in (1001482, 1001563, 1001580);

insert into public.app_classeur_cicatrice_mise_de_cote
  (app_affaire_id, id_unique, jumelle, ancien_app_chaine_id, ancien_dossier_uuid, ancien_dossier_numero, pourquoi,
   mis_de_cote_par)
select c.app_affaire_id, v.iu, v.jumelle, c.app_chaine_id, c.app_dossier_uuid, c.app_dossier_numero, v.pourquoi,
       'patch_mise_de_cote_cicatrices_famille1_2026-11-22'
  from public.app_affaire_ledger c
  join (values
    (1001482::bigint, 'UTLG66LE', 5055::bigint, 'cicatrice, forme B : reproduit l''offre 5055 (STAUFFER, 18/12/2019) dont '
      'le refus du 11/11 18:21 (lot « table ») a deplace la date ; seule dans sa chaine'),
    (1001563::bigint, 'A07EC3DH', 1876::bigint, 'cicatrice, forme B : reproduit l''offre 1876 (GUERIN, 12/01/2024) dont la '
      'cascade du 11/11 et la reacceptation du 12/11 ont deplace la date ; seule dans sa chaine'),
    (1001580::bigint, '3S4ZWOFK', 11958::bigint, 'cicatrice, forme B : reproduit l''offre 11958 (CIMINO, 12/06/2020 ; '
      'colonnes Acquereur / Vendeur inversees au classeur) dont la cascade du 11/11 et la reacceptation du 12/11 ont '
      'deplace la date ; seule dans sa chaine')) v(copie, iu, jumelle, pourquoi)
    on v.copie = c.app_affaire_id;

-- ── ③ LA MISE DE COTE : la note d'abord, puis la ligne (seulement les copies marquees) ────────
delete from public.app_affaire_note
 where app_affaire_id in (1001482, 1001563, 1001580) and origine = 'classeur';
delete from public.app_affaire_ledger
 where app_affaire_id in (1001482, 1001563, 1001580) and transaction_origine = 'classeur';

-- ── ④ LE CONTROLE, DANS LA MEME TRANSACTION -- il juge SA part ───────────────────────────────
do $$
declare reste int; g1 int; g2 int; g3 int; notes_restees int; lot int; jum int;
begin
  select count(*) into reste from public.app_affaire_ledger where app_affaire_id in (1001482, 1001563, 1001580);
  if reste <> 0 then raise exception '⛔ % ligne(s) restent au registre', reste; end if;
  select count(*) into g1 from public.app_affaire_ledger_mise_de_cote_cicatrices_20261122;
  select count(*) into g2 from public.app_affaire_note_mise_de_cote_cicatrices_20261122;
  select count(*) into g3 from public.app_classeur_cicatrice_mise_de_cote
   where app_affaire_id in (1001482, 1001563, 1001580) and ancien_dossier_numero is not null;
  if g1 <> 3 or g2 <> 3 or g3 <> 3 then
    raise exception '⛔ garde incomplete : registre %, notes %, cicatrices avec ancien numero %', g1, g2, g3;
  end if;
  select count(*) into notes_restees from public.app_affaire_note where app_affaire_id in (1001482, 1001563, 1001580);
  if notes_restees <> 0 then raise exception '⛔ % note(s) restent', notes_restees; end if;
  -- ⭐ TEMOIN INVERSE : les 187 autres copies et les 3 jumelles n'ont PAS bouge
  select count(*) into lot from public.app_affaire_ledger where transaction_origine = 'classeur';
  if lot <> 187 then raise exception '⛔ temoin inverse : % copies au lieu de 187', lot; end if;
  select count(*) into jum from public.app_affaire_ledger where app_affaire_id in (5055, 1876, 11958);
  if jum <> 3 then raise exception '⛔ temoin inverse : % jumelle(s) au lieu de 3', jum; end if;
  raise notice '✅ 3 cicatrices mises de cote avec leur ancien numero (% note(s) gardees), 187 copies et 3 jumelles intactes', g2;
end $$;

commit;
