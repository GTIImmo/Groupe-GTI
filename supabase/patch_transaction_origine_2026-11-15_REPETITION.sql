-- ════════════════════════════════════════════════════════════════════════════
-- REPETITION de patch_transaction_origine_2026-11-15.sql                15/11/2026
-- ════════════════════════════════════════════════════════════════════════════
-- A coller APRES le patch. Elle ne modifie RIEN de facon durable : son seul
-- geste est le temoin inverse du controle 6, qui marque une ligne d'ESSAI puis
-- la demarque dans le MEME bloc -- si quoi que ce soit rate, le bloc leve et
-- tout est annule.
--
-- ⚠⚠ CE FICHIER NE PORTE PAS DE `commit;` -- DELIBEREMENT. Un patch qui porte
--   son propre commit se commite meme joue « a blanc » (lecon du 13/11).
--
-- ⭐⭐ LE TEMOIN QUI COMPTE VRAIMENT est le 6 : la vue doit rendre 1 AVANT la
--   marque, 0 APRES, et 1 de nouveau quand on l'enleve. Sans ce basculement,
--   une vue qui rend 0 ne prouve rien du tout.
-- ════════════════════════════════════════════════════════════════════════════

do $$
declare
  ok int := 0;
  rates text := '';
  d text;
  n bigint;
  n_avant bigint;
  n_pendant bigint;
  n_apres bigint;
  t text;
  essai bigint := 1001424;  -- la ligne d'essai A2, posee le 15/11 a 00:35:39
begin
  -- 1. LA COLONNE EXISTE, ET ELLE EST DU BON TYPE
  select data_type || '/' || is_nullable into t
    from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaire_ledger'
     and column_name = 'transaction_origine';
  if t = 'text/YES' then ok := ok + 1; rates := rates || ' | 1 OK colonne text nullable';
  else rates := rates || ' | 1 RATE colonne : ' || coalesce(t, 'ABSENTE'); end if;

  -- 2. LE COMMENTAIRE EST POSE (sans lui, personne ne sait ce que la marque veut dire)
  select col_description('public.app_affaire_ledger'::regclass,
           (select ordinal_position from information_schema.columns
             where table_schema='public' and table_name='app_affaire_ledger'
               and column_name='transaction_origine')) into t;
  if t is not null and position('classeur' in t) > 0 then
    ok := ok + 1; rates := rates || ' | 2 OK commentaire pose';
  else rates := rates || ' | 2 RATE commentaire absent ou muet'; end if;

  -- 3. LA VUE GARDE SES 7 COLONNES, MEMES NOMS, MEME ORDRE
  select string_agg(column_name, ',' order by ordinal_position) into t
    from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaires_sans_numero_hektor';
  if t = 'app_affaire_id,app_dossier_id,kind,state,montant,date,first_seen_at' then
    ok := ok + 1; rates := rates || ' | 3 OK les 7 colonnes inchangees';
  else rates := rates || ' | 3 RATE colonnes de la vue : ' || coalesce(t, 'VUE ABSENTE'); end if;

  -- 4. LA VUE PORTE LES DEUX CONDITIONS
  select pg_get_viewdef('public.app_affaires_sans_numero_hektor'::regclass, true) into d;
  if position('hektor_affaire_id IS NULL' in d) > 0
     and position('transaction_origine IS NULL' in d) > 0 then
    ok := ok + 1; rates := rates || ' | 4 OK les deux conditions';
  else rates := rates || ' | 4 RATE conditions de la vue'; end if;

  -- 5. LES DROITS SONT INCHANGES : postgres et service_role, et SURTOUT PAS anon
  select string_agg(distinct grantee, ',' order by grantee) into t
    from information_schema.role_table_grants
   where table_schema = 'public' and table_name = 'app_affaires_sans_numero_hektor';
  if t = 'postgres,service_role' then
    ok := ok + 1; rates := rates || ' | 5 OK droits inchanges (ni anon ni authenticated)';
  else rates := rates || ' | 5 RATE droits : ' || coalesce(t, 'AUCUN'); end if;

  -- 6. LE TEMOIN INVERSE -- le seul controle qui prouve que le filtre MORD
  select count(*) into n_avant from public.app_affaires_sans_numero_hektor;
  if not exists (select 1 from public.app_affaire_ledger
                  where app_affaire_id = essai and hektor_affaire_id is null) then
    rates := rates || ' | 6 NON MESURE : la ligne d''essai ' || essai
                   || ' n''est plus la (retiree ?). Le temoin inverse demande UNE ligne'
                   || ' sans numero Hektor ; sans elle on ne peut rien prouver.';
  else
    update public.app_affaire_ledger set transaction_origine = 'essai_temoin'
     where app_affaire_id = essai;
    select count(*) into n_pendant from public.app_affaires_sans_numero_hektor;
    update public.app_affaire_ledger set transaction_origine = null
     where app_affaire_id = essai;
    select count(*) into n_apres from public.app_affaires_sans_numero_hektor;
    if n_pendant = n_avant - 1 and n_apres = n_avant then
      ok := ok + 1;
      rates := rates || ' | 6 OK TEMOIN INVERSE : la vue passe de ' || n_avant
                     || ' a ' || n_pendant || ' quand on marque, et revient a '
                     || n_apres || ' quand on demarque';
    else
      raise exception 'TEMOIN INVERSE RATE -- avant %, marquee %, demarquee % (attendu %, %, %). Le bloc leve expres : la marque de l''essai est ANNULEE avec la transaction.',
        n_avant, n_pendant, n_apres, n_avant, n_avant - 1, n_avant;
    end if;
  end if;

  -- 7. LA GARDE RESTE ENTIERE POUR LA PLAGE APP -- c'est la securite de Frederic
  select count(*) into n from public.app_affaires_sans_numero_hektor
   where app_affaire_id >= 1000000;
  if n >= 1 then
    ok := ok + 1;
    rates := rates || ' | 7 OK la plage app est TOUJOURS surveillee (' || n || ' vue(s))';
  else
    rates := rates || ' | 7 A LIRE : 0 ligne de la plage app sans numero. Vrai si'
                   || ' l''essai a ete retire -- mais alors le controle 6 l''a deja dit.';
  end if;

  -- 8. LE PATCH N'A MARQUE PERSONNE : il ouvre une possibilite, il n'ecrit pas
  select count(*) into n from public.app_affaire_ledger
   where transaction_origine is not null;
  if n = 0 then ok := ok + 1; rates := rates || ' | 8 OK 0 ligne marquee (le patch n''ecrit aucune donnee)';
  else rates := rates || ' | 8 A LIRE : ' || n || ' ligne(s) deja marquee(s)'; end if;

  raise notice '% CONTROLE(S) VERT(S) SUR 8 -- %', ok, rates;
  if ok < 8 then
    raise exception 'REPETITION INCOMPLETE : % sur 8. Voir le detail ci-dessus.', ok;
  end if;
end $$;
