-- ═══════════════════════════════════════════════════════════════════════════════
-- ASSISTANT IA — ÉTAPE 2 : LE STATUT D'UN MANDAT, CALCULÉ UNE FOIS DANS LA BASE   12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note : notice/ETAPE2_AGENT_QUI_REPOND_AUDIT_2026-11-12.md §7 question 2.
-- Décision de Frédéric le 12/11 : « B » — le calcul de l'écran est posé UNE fois dans la base ;
-- l'assistant s'en sert, l'écran pourra le reprendre plus tard.
--
-- ─── CE QUE CE PATCH POSE ───
--   ① app_mandat_statut_norm(texte)       le statut d'annonce sans accents, sans espaces autour, en minuscules
--                                         (= normalizeMandateStatusValue, api.ts:57) ;
--   ② app_mandat_date_fin_valide(texte)   la date de fin n'est pas dépassée (= isMandateEndDateStillValid,
--                                         api.ts:65), AVEC les bizarreries de l'écran : vide = valide ; une
--                                         date qui déborde (30 février) est décalée au mois suivant ; un mois
--                                         13 ou un jour 32 ou 00 = illisible = valide ; « aujourd'hui » à Paris ;
--   ③ app_mandat_statut(...)              Actif / Vendu / Clos / Échu (= mandatStatutForRegisterRow, api.ts:93) ;
--   ④ app_mandat_etat(...)                En cours / Annulé (= mandateLifecycleState, api.ts:75) ;
--   ⑤ app_v_mandat_statut                 le registre des mandats + les deux colonnes calculées
--                                         `statut_mandat` et `etat_mandat`, avec les droits du lecteur.
-- La PREUVE que la base dit comme l'écran : la répétition compare la fonction à 4 080 cas calculés par
-- le VRAI code de l'écran (backend/tests/cas_statut_mandat_ecran.cjs extrait les fonctions de api.ts).
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Il ne touche ni au registre (`app_registre_mandats_current`), ni à l'écran : l'écran garde son propre
--   calcul tant qu'on ne le branche pas (décision à part). ⚠ Il y a donc DEUX copies jusque-là ; la
--   répétition et le script de cas sont le garde-fou : si l'écran change sa règle, le script le verra.
-- ⛔ Aucune écriture : des fonctions de calcul et une vue.
--
-- ─── LES DROITS ───
-- La vue est en `security_invoker` : le lecteur n'y voit que ce que le registre lui montre déjà.
-- Les fonctions ne lisent aucune table (calcul pur) ; exécutables par `authenticated`, pas par `anon`.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · La vue DÉPEND du registre. Quatre anciens patchs font `drop view app_registre_mandats_current` puis la
--     recréent : un prochain patch de ce genre devra retirer puis reposer `app_v_mandat_statut`, comme il doit
--     DÉJÀ le faire pour `app_filter_catalog_registre` (mesuré le 12/11 : une vue dépend déjà du registre).
--     Sans `cascade`, l'oubli fait échouer le patch bruyamment, il ne casse rien en silence.
--   · Rien d'autre ne lit ces objets neufs.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_assistant_ia_etape2_statut_mandat_2026-11-12_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_assistant_ia_etape2_statut_mandat_2026-11-12_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_registre_mandats_current') is null then raise exception 'ARRET : registre absent'; end if;
  if to_regclass('public.app_v_mandat_statut') is not null or to_regprocedure('public.app_mandat_statut(text,text,text,text)') is not null then
    raise exception 'ARRET : deja pose ?';
  end if;
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

do $verif$
begin
  if (select count(*) from public.app_v_mandat_statut) <> (select count(*) from public.app_registre_mandats_current) then
    raise exception 'ARRET : la vue ne rend pas le meme nombre de lignes que le registre';
  end if;
  if has_table_privilege('anon', 'public.app_v_mandat_statut', 'select') then raise exception 'ARRET : anon lit la vue'; end if;
end
$verif$;

commit;
