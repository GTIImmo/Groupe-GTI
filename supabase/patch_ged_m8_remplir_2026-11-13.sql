-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — MORCEAU 8 : GARDER LA DÉCISION « REMPLIR / IGNORER »          13/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.18. « Vas y » de Frédéric (13/11).
--
-- ─── CE QUE CE PATCH POSE ───
--   ① app_ged_decision   UNE décision humaine sur une proposition « remplir » : le bien, la lecture d'où vient la
--                        valeur, la proposition (clé), le champ, la valeur, la décision (remplie / ignoree / echec),
--                        ce qui a été envoyé ou le refus, QUI et QUAND. Une ligne ne se modifie ni ne s'efface :
--                        c'est le journal (« une saisie ne se perd jamais »). La plus récente fait foi.
--   ② app_ged_decider()  la seule porte d'écriture : compte actif, interrupteur ged_remplir allumé POUR L'APPELANT,
--                        bien dans son périmètre ; l'auteur est auth.uid(), jamais un paramètre.
--   ③ l'interrupteur ged_remplir, ÉTEINT (off / admin / on).
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Il n'écrit RIEN sur la fiche, ni chez Hektor, ni au registre : le remplissage passe par les gestes EXISTANTS,
--   appelés par l'écran (app_edit_annonce_optimistic, app_set_mandat_charge_optimistic, app_conditions_affaire_ecrire),
--   INCHANGÉS. Cette table GARDE seulement la décision.
-- ⛔ Il ne touche ni app_ged_journal (sa contrainte d'objet reste telle quelle), ni app_ged_lecture, ni app_console_*.
--
-- ─── LES DROITS ───
-- ⛔ Une table neuve donne PAR DÉFAUT tous les droits à `authenticated` (pg_default_acl) : chaque rôle est nommé.
--   Lecture au MÊME périmètre que les lectures (lecteur global, ou bien du portefeuille). AUCUNE écriture directe.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · La descente de 07:45 recopiera cette table (vide au départ). Rien d'autre ne la lit.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_ged_m8_remplir_2026-11-13_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_ged_m8_remplir_2026-11-13_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_ged_lecture') is null then raise exception 'ARRET : morceau 6 absent'; end if;
  if to_regclass('public.app_ged_decision') is not null then raise exception 'ARRET : app_ged_decision existe deja -- patch deja applique ?'; end if;
  if exists (select 1 from pg_proc where proname = 'app_ged_decider' and pronamespace = 'public'::regnamespace) then
    raise exception 'ARRET : app_ged_decider existe deja';
  end if;
  if exists (select 1 from public.app_setting where key = 'ged_remplir') then raise exception 'ARRET : ged_remplir existe deja'; end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LES DÉCISIONS
create table public.app_ged_decision (
  id                 uuid primary key default gen_random_uuid(),
  hektor_annonce_id  text not null,
  lecture_id         uuid references public.app_ged_lecture (id) on delete set null,
  cle                text not null,
  champ              text not null,
  valeur             text not null,
  decision           text not null,
  detail             jsonb,
  decide_par         uuid not null,
  decide_le          timestamptz not null default now(),
  constraint app_ged_decision_decision check (decision in ('remplie', 'ignoree', 'echec')),
  constraint app_ged_decision_annonce_non_vide check (btrim(hektor_annonce_id) <> ''),
  constraint app_ged_decision_cle_non_vide check (btrim(cle) <> '')
);
create index app_ged_decision_annonce_idx on public.app_ged_decision (hektor_annonce_id, decide_le desc);

comment on table public.app_ged_decision is
  'GED morceau 8 (13/11/2026) : la décision humaine sur une proposition « remplir » (remplie, ignoree, echec), '
  'qui et quand. Journal : jamais modifiée ni effacée ; la plus récente fait foi. Écrite par app_ged_decider seule.';

-- ─────────────────────────────────────────────────────── ② LA PORTE D'ÉCRITURE
create function public.app_ged_decider(
  p_hektor_annonce_id text,
  p_lecture_id        uuid,
  p_cle               text,
  p_champ             text,
  p_valeur            text,
  p_decision          text,
  p_detail            jsonb
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_cran text;
  v_id   uuid;
begin
  -- GED morceau 8 (13/11/2026) : GARDER la décision. N'écrit QUE dans app_ged_decision.
  if not public.is_app_user_active() then
    raise exception '%', 'Compte inactif : la décision ne peut pas être écrite.' using errcode = '42501';
  end if;
  select lower(btrim(value)) into v_cran from public.app_setting where key = 'ged_remplir';
  if not (coalesce(v_cran, 'off') in ('on', 'true', '1', 'yes') or (v_cran = 'admin' and public.is_app_admin())) then
    raise exception '%', 'Remplir la fiche depuis un document n''est pas ouvert pour toi.' using errcode = '42501';
  end if;
  if coalesce(btrim(p_hektor_annonce_id), '') = '' or coalesce(btrim(p_cle), '') = '' or coalesce(btrim(p_champ), '') = '' or p_valeur is null then
    raise exception '%', 'Proposition incomplète.';
  end if;
  if coalesce(p_decision, '') not in ('remplie', 'ignoree', 'echec') then
    raise exception '%', 'Décision inconnue (remplie, ignoree ou echec).';
  end if;
  if not ((select public.is_app_global_reader())
          or p_hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))) then
    raise exception '%', 'Ce bien n''est pas dans ton périmètre.' using errcode = '42501';
  end if;
  if p_lecture_id is not null and not exists (select 1 from public.app_ged_lecture l where l.id = p_lecture_id and l.hektor_annonce_id = p_hektor_annonce_id) then
    raise exception '%', 'Lecture introuvable pour ce bien.';
  end if;

  insert into public.app_ged_decision (hektor_annonce_id, lecture_id, cle, champ, valeur, decision, detail, decide_par)
  values (btrim(p_hektor_annonce_id), p_lecture_id, btrim(p_cle), btrim(p_champ), p_valeur, p_decision, p_detail, auth.uid())
  returning id into v_id;
  return jsonb_build_object('ok', true, 'id', v_id);
end
$function$;

comment on function public.app_ged_decider(text, uuid, text, text, text, text, jsonb) is
  'GED morceau 8 (13/11/2026) : garde la décision « remplir / ignorer » d''une proposition (auteur = auth.uid()). '
  'Interrupteur ged_remplir, périmètre du bien. N''écrit que dans app_ged_decision.';

-- ─────────────────────────────────────────────────────── ③ LES DROITS
alter table public.app_ged_decision enable row level security;
revoke all on table public.app_ged_decision from public, anon, authenticated;
grant select on table public.app_ged_decision to authenticated;
create policy app_ged_decision_select_scope on public.app_ged_decision
  for select to authenticated
  using (
    (select public.is_app_global_reader())
    or hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))
  );
revoke all on function public.app_ged_decider(text, uuid, text, text, text, text, jsonb) from public, anon, authenticated;
grant execute on function public.app_ged_decider(text, uuid, text, text, text, text, jsonb) to authenticated;

-- ─────────────────────────────────────────────────────── ④ L'INTERRUPTEUR (ÉTEINT)
insert into public.app_setting (key, value, description, updated_at) values
  ('ged_remplir', 'off',
   'GED morceau 8 (13/11/2026) : proposer de REMPLIR une case vide de la fiche depuis un document lu (un clic par case). '
   'off / admin / on. Éteint = aucune proposition, rien ne s''écrit.',
   now());

commit;

-- ALLUMER pour Frédéric seul : update public.app_setting set value = 'admin', updated_at = now() where key = 'ged_remplir';
-- ÉTEINDRE                  : update public.app_setting set value = 'off',   updated_at = now() where key = 'ged_remplir';

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être VERT.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① la table existe, RLS active' as controle, count(*) as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from pg_class where oid = 'public.app_ged_decision'::regclass and relrowsecurity
union all
select '② authenticated : SELECT seulement', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants
 where table_name = 'app_ged_decision' and grantee in ('authenticated', 'anon', 'PUBLIC') and privilege_type <> 'SELECT'
union all
select '③ anon : aucun droit sur la table', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants where table_name = 'app_ged_decision' and grantee = 'anon'
union all
select '④ la porte : SECURITY DEFINER, fermée à anon', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_decider' and p.prosecdef and not has_function_privilege('anon', p.oid, 'execute')
     and has_function_privilege('authenticated', p.oid, 'execute')
union all
select '⑤ ged_remplir posé ÉTEINT', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from public.app_setting where key = 'ged_remplir' and value = 'off'
union all
select '⑥ la table est vide', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from public.app_ged_decision;
