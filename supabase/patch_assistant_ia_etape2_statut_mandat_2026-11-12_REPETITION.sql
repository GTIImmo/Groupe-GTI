-- RÉPÉTITION — patch_assistant_ia_etape2_statut_mandat_2026-11-12.sql (ASSISTANT IA, étape 2, décision « B »).
-- Pose les fonctions et la vue DANS une transaction, compare la fonction aux 4 080 cas calculés par le VRAI code de
-- l'écran (backend/tests/cas_statut_mandat_ecran.cjs), mesure la vue à la place d'un admin puis d'un négociateur, puis
-- lève une erreur VOLONTAIRE qui porte les verdicts : RIEN n'est gardé. Attendu : « 7 OK, 0 KO ».
-- ⚠ Le bloc « LES CAS » se régénère par le script si l'écran change sa règle : une différence = un KO au ①.
begin;
set local lock_timeout = '3s';
do $garde$
begin
  if to_regclass('public.app_v_mandat_statut') is not null then raise exception 'ARRET : deja pose'; end if;
end
$garde$;

-- ① le statut normalisé : NFD sans accents, trim, minuscules
create function public.app_mandat_statut_norm(p_statut text)
returns text language sql immutable set search_path = public as $f$
  select lower(translate(regexp_replace(coalesce(p_statut, ''), '^\s+|\s+$', '', 'g'),
    'àâäáãåçéèêëíìîïñóòôöõúùûüýÿÀÂÄÁÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝ',
    'aaaaaaceeeeiiiinooooouuuuyyAAAAAACEEEEIIIINOOOOOUUUUY'))
$f$;

-- ② la date de fin est-elle encore valable ? (CASE imbriqués : jamais de conversion avant le test du format)
create function public.app_mandat_date_fin_valide(p_fin text)
returns boolean language sql stable set search_path = public as $f$
  select case
    when p_fin is null or p_fin = '' then true
    when p_fin !~ '^\d{4}-\d{2}-\d{2}$' then true                       -- illisible pour nous = valide (0 cas en base)
    else case
      when substr(p_fin, 6, 2)::int not between 1 and 12 or substr(p_fin, 9, 2)::int not between 1 and 31 then true
      when substr(p_fin, 1, 4)::int = 0 then false                       -- l'an 0000 est passé
      else (make_date(substr(p_fin, 1, 4)::int, substr(p_fin, 6, 2)::int, 1) + (substr(p_fin, 9, 2)::int - 1))
           >= (now() at time zone 'Europe/Paris')::date                  -- le 30 février = le 2 mars, comme l'écran
    end
  end
$f$;

-- ③ Actif / Vendu / Clos / Échu
create function public.app_mandat_statut(p_statut text, p_fin text, p_cloture text, p_vente text)
returns text language sql stable set search_path = public as $f$
  select case
    when coalesce(p_vente, '') <> '' or s like '%vendu%' or s like '%vente%' then 'Vendu'
    when regexp_replace(coalesce(p_cloture, ''), '^\s+|\s+$', '', 'g') <> '' or s like '%clos%' or s like '%clotur%' then 'Clos'
    when not public.app_mandat_date_fin_valide(p_fin) then 'Échu'
    else 'Actif'
  end
  from (select public.app_mandat_statut_norm(p_statut) as s) n
$f$;

-- ④ En cours / Annulé
create function public.app_mandat_etat(p_statut text, p_fin text)
returns text language sql stable set search_path = public as $f$
  select case
    when s like '%vendu%' or s like '%vente%' or s like '%clos%' or s like '%clotur%' then 'Annulé'
    when s like '%offre%' or s like '%compromis%' then 'En cours'
    when s = 'actif' and public.app_mandat_date_fin_valide(p_fin) then 'En cours'
    else 'Annulé'
  end
  from (select public.app_mandat_statut_norm(p_statut) as s) n
$f$;

-- ⑤ la vue : le registre + les deux colonnes
create view public.app_v_mandat_statut with (security_invoker = true) as
select r.*,
       public.app_mandat_statut(r.statut_annonce, r.mandat_date_fin, r.mandat_date_cloture, r.vente_id) as statut_mandat,
       public.app_mandat_etat(r.statut_annonce, r.mandat_date_fin) as etat_mandat
from public.app_registre_mandats_current r;

comment on view public.app_v_mandat_statut is
  'Registre des mandats + statut_mandat (Actif/Vendu/Clos/Échu) et etat_mandat (En cours/Annulé), calculés comme '
  'l''écran (api.ts:75 et 93). Posé le 12/11/2026 pour l''assistant IA (décision « B »). Droits du lecteur.';

revoke all on function public.app_mandat_statut_norm(text) from public, anon;
revoke all on function public.app_mandat_date_fin_valide(text) from public, anon;
revoke all on function public.app_mandat_statut(text, text, text, text) from public, anon;
revoke all on function public.app_mandat_etat(text, text) from public, anon;
grant execute on function public.app_mandat_statut_norm(text) to authenticated, service_role;
grant execute on function public.app_mandat_date_fin_valide(text) to authenticated, service_role;
grant execute on function public.app_mandat_statut(text, text, text, text) to authenticated, service_role;
grant execute on function public.app_mandat_etat(text, text) to authenticated, service_role;
revoke all on table public.app_v_mandat_statut from public, anon, authenticated;
grant select on table public.app_v_mandat_statut to authenticated, service_role;

do $essai$
declare statuts text[]; dates text[]; clotures text[]; ventes text[]; attendus text;
        s text; d text; c text; v text; d_reel text; obtenu text; attendu text; n int := 0; ecarts int := 0; exemples text := '';
        auj date := (now() at time zone 'Europe/Paris')::date;
        v_admin uuid; v_nego uuid; n_reg_admin int; n_vue_admin int; n_reg_nego int; n_vue_nego int; t0 timestamptz; ms int;
        repartition text; ok int := 0; ko int := 0; j text := '';
begin
  -- ─────────────── LES CAS (sortie de : node backend/tests/cas_statut_mandat_ecran.cjs)
  -- 4080 cas, attendus calculés par le code de l'écran (api.ts) le 2026-11-12
  statuts  := array[null, '', 'Actif', ' Actif ', 'ACTIF', 'Vendu', 'Clos', 'Clôturé', 'Estimation', 'Sous compromis', 'Sous offre', 'Recherche active', 'Sans recherche', 'Contact inconnu', 'Recherche archivée', 'En vente', 'Archivé']::text[];
  dates    := array[null, '', 'HIER', 'AUJOURDHUI', 'DEMAIN', '2019-03-01', '2031-12-31', '2026-02-30', '2031-02-31', '2031-04-31', '2026-13-01', '2026-00-10', '2026-01-32', '2026-01-00', '0000-01-01', 'abc']::text[];  -- HIER / AUJOURDHUI / DEMAIN = jetons remplacés par la date de Paris
  clotures := array[null, '', ' ', '2026-01-01', '2026-01-01 10:00:00']::text[];
  ventes   := array[null, '', '12345']::text[];
  attendus := 'ANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOENENVNENENVNENENVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOEOEOVOEOEOVOEOEOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOEOEOVOEOEOVOEOEOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOEOEOVOEOEOVOEOEOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOEOEOVOEOEOVOEOEOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOEOEOVOEOEOVOEOEOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOEOEOVOEOEOVOEOEOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOEOEOVOEOEOVOEOEOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOEOEOVOEOEOVOEOEOVOCOCOVOCOCOVOAOAOVOAOAOVOAOAOVOCOCOVOCOCOVOANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVNENENVNENENVNENENVNCNCNVNCNCNVNANANVNANANVNANANVNCNCNVNCNCNVN';
  -- ───────────────
  foreach s in array statuts loop foreach d in array dates loop foreach c in array clotures loop foreach v in array ventes loop
    d_reel := case d when 'HIER' then to_char(auj - 1, 'YYYY-MM-DD') when 'AUJOURDHUI' then to_char(auj, 'YYYY-MM-DD')
                     when 'DEMAIN' then to_char(auj + 1, 'YYYY-MM-DD') else d end;
    obtenu := case public.app_mandat_statut(s, d_reel, c, v) when 'Actif' then 'A' when 'Vendu' then 'V' when 'Clos' then 'C' when 'Échu' then 'E' else '?' end
           || case public.app_mandat_etat(s, d_reel) when 'En cours' then 'O' when 'Annulé' then 'N' else '?' end;
    attendu := substr(attendus, n * 2 + 1, 2);
    if obtenu is distinct from attendu then
      ecarts := ecarts + 1;
      if ecarts <= 5 then exemples := exemples || format(E'\n     statut=%L fin=%L cloture=%L vente=%L : base %s, écran %s', s, d, c, v, obtenu, attendu); end if;
    end if;
    n := n + 1;
  end loop; end loop; end loop; end loop;

  select id into v_admin from public.app_user_profile where is_active and role = 'admin' order by id limit 1;
  select id into v_nego  from public.app_user_profile where is_active and role = 'commercial' order by id limit 1;
  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_reg_admin from public.app_registre_mandats_current;
  t0 := clock_timestamp();
  select string_agg(x, ', ') into repartition
    from (select statut_mandat || ' ' || count(*) as x from public.app_v_mandat_statut group by statut_mandat order by 1) r;
  ms := extract(milliseconds from clock_timestamp() - t0)::int;
  select count(*) into n_vue_admin from public.app_v_mandat_statut;
  reset role;
  perform set_config('request.jwt.claims', json_build_object('sub', v_nego, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_reg_nego from public.app_registre_mandats_current;
  select count(*) into n_vue_nego from public.app_v_mandat_statut;
  reset role;

  if ecarts = 0 and n = length(attendus) / 2 then ok := ok + 1; j := j || format(E'\nOK  ① la base dit comme l''écran sur les %s cas', n);
  else ko := ko + 1; j := j || format(E'\nKO  ① %s écart(s) sur %s cas (attendus pour %s)%s', ecarts, n, length(attendus) / 2, exemples); end if;
  if n_vue_admin = n_reg_admin and n_reg_admin > 0 then ok := ok + 1; j := j || format(E'\nOK  ② l''admin voit autant de lignes dans la vue que dans le registre : %s', n_vue_admin);
  else ko := ko + 1; j := j || format(E'\nKO  ② vue %s / registre %s', n_vue_admin, n_reg_admin); end if;
  if n_vue_nego = n_reg_nego and n_reg_nego > 0 then ok := ok + 1; j := j || format(E'\nOK  ③ un négociateur aussi (les droits du lecteur passent) : %s', n_vue_nego);
  else ko := ko + 1; j := j || format(E'\nKO  ③ vue %s / registre %s', n_vue_nego, n_reg_nego); end if;
  if ms < 3000 then ok := ok + 1; j := j || format(E'\nOK  ④ compter par statut prend %s ms (sous 3 s ; le plafond est 8 s)', ms);
  else ko := ko + 1; j := j || format(E'\nKO  ④ %s ms', ms); end if;
  if not has_table_privilege('anon', 'public.app_v_mandat_statut', 'select')
     and not has_function_privilege('anon', 'public.app_mandat_statut(text,text,text,text)', 'execute') then ok := ok + 1; j := j || E'\nOK  ⑤ la clé publique ne lit ni n''exécute rien';
  else ko := ko + 1; j := j || E'\nKO  ⑤'; end if;
  if (select count(*) from pg_depend dp join pg_rewrite rw on rw.oid = dp.objid join pg_class k on k.oid = rw.ev_class
       where dp.refobjid = 'public.app_registre_mandats_current'::regclass and k.relname = 'app_v_mandat_statut') > 0
  then ok := ok + 1; j := j || E'\nOK  ⑥ la dépendance au registre est déclarée (un futur « drop view » du registre échouera bruyamment)';
  else ko := ko + 1; j := j || E'\nKO  ⑥'; end if;
  if public.app_mandat_statut('Actif', to_char(auj - 1, 'YYYY-MM-DD'), null, null) = 'Échu'
     and public.app_mandat_statut('Actif', to_char(auj, 'YYYY-MM-DD'), null, null) = 'Actif' then ok := ok + 1; j := j || E'\nOK  ⑦ témoin : fin hier = Échu, fin aujourd''hui = Actif';
  else ko := ko + 1; j := j || E'\nKO  ⑦'; end if;
  raise exception 'RÉPÉTITION ASSISTANT IA étape 2, statut des mandats (rien n''est gardé) : % OK, % KO%   — répartition : %', ok, ko, j, repartition;
end
$essai$;
rollback;
