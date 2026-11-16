-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — MORCEAU 10 (lot 10a) : JUGER LES LIGNES « À REGARDER »          16/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.20. « Vas y » de Frédéric (16/11).
--
-- ─── CE QUE CE PATCH POSE ───
--   ① app_ged_jugement   LE JUGEMENT d'un humain sur une ligne « À regarder » : le bien, la règle (P9, N2…), la ligne
--                        (clé = règle + texte), son texte et son niveau tels qu'affichés, le verdict (vrai / faux /
--                        deja_su), un commentaire facultatif, QUI et QUAND. Une ligne ne se modifie ni ne s'efface :
--                        c'est le journal ; le jugement le plus récent d'une ligne fait foi.
--   ② app_ged_juger()    la seule porte d'écriture : compte actif, interrupteur ged_propositions ouvert POUR
--                        L'APPELANT (le même que les lignes « À regarder »), bien dans son périmètre ; l'auteur est
--                        auth.uid(), jamais un paramètre.
--   Pas d'interrupteur neuf : ged_propositions (déjà en « admin » depuis le 12/11) ouvre les lignes ET leur jugement.
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Il n'écrit RIEN sur la fiche, ni chez Hektor : un jugement est une MESURE (2 semaines, puis décision règle par
--   règle : garder, resserrer, retirer). Il ne touche ni app_ged_decision, ni app_ged_lecture, ni app_ged_valeur.
--
-- ─── LES DROITS ───
-- ⛔ Une table neuve donne PAR DÉFAUT tous les droits à `authenticated` (pg_default_acl) : chaque rôle est nommé.
--   Lecture au MÊME périmètre que les décisions (lecteur global, ou bien du portefeuille). AUCUNE écriture directe.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · La descente de 07:45 recopiera cette table (vide au départ) ; ses TEXTES portent des noms, comme app_ged_valeur.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_ged_m10_jugement_2026-11-16_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_ged_m10_jugement_2026-11-16_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_ged_decision') is null then raise exception 'ARRET : morceau 8 absent'; end if;
  if to_regclass('public.app_ged_jugement') is not null then raise exception 'ARRET : app_ged_jugement existe deja -- patch deja applique ?'; end if;
  if exists (select 1 from pg_proc where proname = 'app_ged_juger' and pronamespace = 'public'::regnamespace) then
    raise exception 'ARRET : app_ged_juger existe deja';
  end if;
  if not exists (select 1 from public.app_setting where key = 'ged_propositions') then raise exception 'ARRET : ged_propositions absent'; end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LES JUGEMENTS
create table public.app_ged_jugement (
  id                 uuid primary key default gen_random_uuid(),
  hektor_annonce_id  text not null,
  regle              text not null,
  cle                text not null,
  texte              text not null,
  niveau             text not null,
  verdict            text not null,
  commentaire        text,
  juge_par           uuid not null,
  juge_le            timestamptz not null default now(),
  constraint app_ged_jugement_verdict check (verdict in ('vrai', 'faux', 'deja_su')),
  constraint app_ged_jugement_niveau check (niveau in ('alerte', 'piece', 'info')),
  constraint app_ged_jugement_annonce_non_vide check (btrim(hektor_annonce_id) <> ''),
  constraint app_ged_jugement_cle_non_vide check (btrim(cle) <> ''),
  constraint app_ged_jugement_regle_non_vide check (btrim(regle) <> ''),
  constraint app_ged_jugement_commentaire_court check (commentaire is null or length(commentaire) <= 500)
);
create index app_ged_jugement_annonce_idx on public.app_ged_jugement (hektor_annonce_id, juge_le desc);
create index app_ged_jugement_regle_idx on public.app_ged_jugement (regle, juge_le desc);

comment on table public.app_ged_jugement is
  'GED morceau 10 (16/11/2026) : le jugement humain (vrai / faux / deja_su) d''une ligne « À regarder », qui et quand. '
  'Journal : jamais modifié ni effacé ; le plus récent d''une ligne fait foi. Écrit par app_ged_juger seule.';

-- ─────────────────────────────────────────────────────── ② LA PORTE D'ÉCRITURE
create function public.app_ged_juger(
  p_hektor_annonce_id text,
  p_regle             text,
  p_cle               text,
  p_texte             text,
  p_niveau            text,
  p_verdict           text,
  p_commentaire       text
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_cran text;
  v_id   uuid;
begin
  -- GED morceau 10 (16/11/2026) : GARDER le jugement d'une ligne. N'écrit QUE dans app_ged_jugement.
  if not public.is_app_user_active() then
    raise exception '%', 'Compte inactif : le jugement ne peut pas être écrit.' using errcode = '42501';
  end if;
  select lower(btrim(value)) into v_cran from public.app_setting where key = 'ged_propositions';
  if not (coalesce(v_cran, 'off') in ('on', 'true', '1', 'yes') or (v_cran = 'admin' and public.is_app_admin())) then
    raise exception '%', 'Les lignes « À regarder » ne sont pas ouvertes pour toi.' using errcode = '42501';
  end if;
  if coalesce(btrim(p_hektor_annonce_id), '') = '' or coalesce(btrim(p_regle), '') = '' or coalesce(btrim(p_cle), '') = ''
     or coalesce(btrim(p_texte), '') = '' then
    raise exception '%', 'Ligne incomplète.';
  end if;
  if coalesce(p_verdict, '') not in ('vrai', 'faux', 'deja_su') then
    raise exception '%', 'Verdict inconnu (vrai, faux ou deja_su).';
  end if;
  if coalesce(p_niveau, '') not in ('alerte', 'piece', 'info') then
    raise exception '%', 'Niveau inconnu (alerte, piece ou info).';
  end if;
  if not ((select public.is_app_global_reader())
          or p_hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))) then
    raise exception '%', 'Ce bien n''est pas dans ton périmètre.' using errcode = '42501';
  end if;

  insert into public.app_ged_jugement (hektor_annonce_id, regle, cle, texte, niveau, verdict, commentaire, juge_par)
  values (btrim(p_hektor_annonce_id), btrim(p_regle), btrim(p_cle), left(p_texte, 1000), p_niveau, p_verdict,
          nullif(left(btrim(coalesce(p_commentaire, '')), 500), ''), auth.uid())
  returning id into v_id;
  return jsonb_build_object('ok', true, 'id', v_id);
end
$function$;

comment on function public.app_ged_juger(text, text, text, text, text, text, text) is
  'GED morceau 10 (16/11/2026) : garde le jugement (vrai / faux / deja_su) d''une ligne « À regarder » (auteur = '
  'auth.uid()). Interrupteur ged_propositions, périmètre du bien. N''écrit que dans app_ged_jugement.';

-- ─────────────────────────────────────────────────────── ③ LES DROITS
alter table public.app_ged_jugement enable row level security;
revoke all on table public.app_ged_jugement from public, anon, authenticated;
grant select on table public.app_ged_jugement to authenticated;
create policy app_ged_jugement_select_scope on public.app_ged_jugement
  for select to authenticated
  using (
    (select public.is_app_global_reader())
    or hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))
  );
revoke all on function public.app_ged_juger(text, text, text, text, text, text, text) from public, anon, authenticated;
grant execute on function public.app_ged_juger(text, text, text, text, text, text, text) to authenticated;

commit;

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être VERT.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① la table existe, RLS active' as controle, count(*) as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from pg_class where oid = 'public.app_ged_jugement'::regclass and relrowsecurity
union all
select '② authenticated : SELECT seulement', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants
 where table_name = 'app_ged_jugement' and grantee in ('authenticated', 'anon', 'PUBLIC') and privilege_type <> 'SELECT'
union all
select '③ anon : aucun droit sur la table', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants where table_name = 'app_ged_jugement' and grantee = 'anon'
union all
select '④ la porte : SECURITY DEFINER, fermée à anon', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_proc p where p.proname = 'app_ged_juger' and p.prosecdef and not has_function_privilege('anon', p.oid, 'execute')
     and has_function_privilege('authenticated', p.oid, 'execute')
union all
select '⑤ ged_propositions inchangé (toujours « admin »)', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from public.app_setting where key = 'ged_propositions' and value = 'admin'
union all
select '⑥ la table est vide', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from public.app_ged_jugement;
