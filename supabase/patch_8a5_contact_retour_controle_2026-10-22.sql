-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · 8a-B — LE CONTRÔLE AU RETOUR D'UNE MODIFICATION DE CONTACT      22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (« 8a, fin — LA MODIFICATION DE CONTACT »)
--
-- LE DÉFAUT (audit du 22/10, prouvé sur 605030) : une modification de contact part chez
-- Hektor ; la relecture qui suit REMPLACE notre ligne par celle de Hektor. Si Hektor n'a
-- pas gardé un champ (une ville sans code postal, le 08/10), notre valeur disparaît EN
-- SILENCE : personne ne compare ce qui revient à ce qui est parti. C'est N.2 pour le
-- contact — la pièce 3 l'a fait pour la création d'annonce ce matin.
--
-- CE QUE FAIT CE PATCH — ADDITIF, derrière l'interrupteur 'contact_retour_controle' (off) :
--   GARDER    quand un travail de modification de contact réussit (« updated »), ce qui
--             est PARTI chez Hektor est gardé à part, dans app_contact_saisie_modif —
--             les 10 champs qui ont une colonne et que Hektor rend (les 3 propres à l'app,
--             naissance / lieu / situation, sont déjà réinjectés : ils ne se jugent pas).
--   CONTRÔLER à la première écriture du pipeline (relecture ou nuit) dont la date Hektor est
--             POSTÉRIEURE à l'envoi, un verdict champ par champ : identique · autre_forme
--             (casse, espaces, accents, téléphone) · remplace · absent. Une écriture plus
--             ancienne que l'envoi (l'ancien Hektor) ne juge RIEN.
--   SIGNALER  une vue, une ligne par contact ET par champ en écart (remplace, absent), plus
--             une ligne « non_relu » si rien n'est revenu en 24 h ; un marquage « vu »
--             (admin) ; la sentinelle data.contact_modif_ecart (check_gti_health.py).
--   ⚠ Il NE REMET RIEN : la valeur de Hektor reste affichée (règle 2, « Hektor confirme ») ;
--     l'écart est dit, il ne se corrige pas tout seul.
-- Deux déclencheurs, qui ne bloquent JAMAIS l'écriture qui les porte (une erreur devient
-- un WARNING) : sur app_console_job (seulement quand un travail de contact passe à
-- « done »), sur app_contact_current (seulement quand refreshed_at change, et s'il existe
-- une saisie en attente pour ce contact — le cas rare).
-- ⚠ Aucune fonction existante n'est retouchée.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'contact_retour_controle';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'contact_retour_controle';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_8a5_contact_retour_controle_2026-10-22_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
    IF to_regclass('public.app_contact_saisie_modif') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la table app_contact_saisie_modif existe deja. Rien n''est ecrit.';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname IN ('app_contact_saisie_modif_job_trg', 'app_contact_saisie_modif_juge_trg')) THEN
        RAISE EXCEPTION '%', 'ARRET : un des declencheurs existe deja. Rien n''est ecrit.';
    END IF;
END
$garde$;

-- 0. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('contact_retour_controle', 'off',
        'Chantier 8 / 8a-B 22/10/2026 : on = ce qui part chez Hektor quand on modifie un contact est garde, puis compare a ce que Hektor rend (voir supabase/patch_8a5_contact_retour_controle_2026-10-22.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- GARDER : la table à part
create table public.app_contact_saisie_modif (
  job_id            uuid primary key,              -- le travail qui a porte la modification chez Hektor
  job_type          text not null,
  hektor_contact_id text not null,                 -- NOTRE cle (app_contact_current.hektor_contact_id)
  hektor_target_id  text,                          -- le numero de Hektor
  saisie            jsonb not null,                -- colonne -> valeur partie chez Hektor
  envoye_le         timestamptz not null,          -- debut du travail : AVANT l'ecriture chez Hektor
  ecrit_par         uuid,
  etat              text not null default 'attente' check (etat in ('attente', 'juge', 'remplacee')),
  verdict           jsonb,                         -- { colonne: { envoye, relu, etat } }
  verdict_le        timestamptz,
  ecarts            integer,                       -- remplace + absent
  traite_le         timestamptz,                   -- un humain a vu les ecarts
  traite_par        uuid,
  cree_le           timestamptz not null default now()
);
create index app_contact_saisie_modif_attente on public.app_contact_saisie_modif (hektor_contact_id) where etat = 'attente';
comment on table public.app_contact_saisie_modif is
  'Chantier 8 / 8a-B (22/10/2026) : ce qui est parti chez Hektor a chaque modification de contact reussie, et son verdict au retour. Ecrite uniquement par les declencheurs app_contact_saisie_modif_*.';
alter table public.app_contact_saisie_modif enable row level security;
revoke all on public.app_contact_saisie_modif from public, anon, authenticated;
grant select, insert, update, delete on public.app_contact_saisie_modif to service_role;

-- La charge d'un travail -> les 10 colonnes jugees (memes alias que app_edit_contact_optimistic
-- et que la porte du mandant). Une valeur vide n'est pas une saisie.
create or replace function public.app_contact_champs_modif(p jsonb)
 returns jsonb
 language sql
 immutable
as $f$
  select case when jsonb_typeof(p) <> 'object' then '{}'::jsonb else jsonb_strip_nulls(jsonb_build_object(
    'nom',             nullif(trim(coalesce(p->>'last_name', p->>'nom', '')), ''),
    'prenom',          nullif(trim(coalesce(p->>'first_name', p->>'prenom', '')), ''),
    'civilite',        nullif(trim(coalesce(p->>'civility', p->>'civilite', '')), ''),
    'email',           nullif(trim(coalesce(p->>'email', '')), ''),
    'phone_primary',   nullif(trim(coalesce(p->>'phone', p->>'telephone', p->>'mobile', '')), ''),
    'phone_secondary', nullif(trim(coalesce(p->>'phone_secondary', p->>'telephone2', p->>'phoneSecondary', '')), ''),
    'adresse',         nullif(trim(coalesce(p->>'address', p->>'adresse', '')), ''),
    'code_postal',     nullif(trim(coalesce(p->>'postal_code', p->>'code_postal', '')), ''),
    'ville',           nullif(trim(coalesce(p->>'city', p->>'ville', '')), ''),
    'commentaires',    nullif(trim(coalesce(p->>'comments', p->>'commentaires', '')), ''))) end
$f$;

-- la meme valeur sous une autre forme : casse, espaces, accents, un telephone ecrit autrement
create or replace function public.app_contact_meme_valeur(a text, b text)
 returns boolean
 language plpgsql
 immutable
as $f$
declare
  na text;
  nb text;
begin
  if a is null or b is null then return false; end if;
  na := translate(lower(regexp_replace(trim(a), '\s+', ' ', 'g')), 'àâäáãéèêëíìîïóòôöõúùûüçñ', 'aaaaaeeeeiiiiooooouuuucn');
  nb := translate(lower(regexp_replace(trim(b), '\s+', ' ', 'g')), 'àâäáãéèêëíìîïóòôöõúùûüçñ', 'aaaaaeeeeiiiiooooouuuucn');
  if na = nb then return true; end if;
  if replace(na, '-', ' ') = replace(nb, '-', ' ') then return true; end if;
  if a ~ '^[0-9 .+()-]+$' and b ~ '^[0-9 .+()-]+$'
     and regexp_replace(a, '[^0-9]', '', 'g') <> ''
     and regexp_replace(a, '[^0-9]', '', 'g') = regexp_replace(b, '[^0-9]', '', 'g') then
    return true;
  end if;
  return false;
end
$f$;

create or replace function public.app_contact_verdict_modif(saisie jsonb, c jsonb)
 returns jsonb
 language plpgsql
 immutable
as $f$
declare
  k    text;
  e    text;
  r    text;
  out  jsonb := '{}'::jsonb;
begin
  for k in select jsonb_object_keys(saisie) loop
    e := nullif(trim(saisie->>k), '');
    if e is null then continue; end if;
    r := nullif(trim(c->>k), '');
    out := out || jsonb_build_object(k, jsonb_build_object('envoye', e, 'relu', r, 'etat',
      case when r is null then 'absent'
           when r = e then 'identique'
           when public.app_contact_meme_valeur(e, r) then 'autre_forme'
           else 'remplace' end));
  end loop;
  return out;
end
$f$;

-- GARDER : quand un travail de modification de contact passe a « done » avec « updated »
create or replace function public.app_contact_saisie_modif_job_trg()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_on     boolean;
  ident    text;
  k_id     text;
  k_target text;
  champs   jsonb;
  avant    jsonb;
begin
  select lower(trim(coalesce(st.value, ''))) in ('on', '1', 'true', 'oui') into v_on
    from public.app_setting st where st.key = 'contact_retour_controle';
  if not coalesce(v_on, false) then return null; end if;
  begin
    if coalesce(new.result_json->>'status', '') <> 'updated' then return null; end if;  -- held_conflict, etc.
    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', '')), '');
    if ident is null then return null; end if;
    select c.hektor_contact_id, c.hektor_target_id into k_id, k_target
      from public.app_contact_current c
     where c.hektor_contact_id = ident or c.hektor_target_id = ident
     order by (c.hektor_contact_id = ident) desc
     limit 1;
    if k_id is null then return null; end if;
    champs := public.app_contact_champs_modif(new.payload_json);
    if champs = '{}'::jsonb then return null; end if;
    -- une saisie encore en attente pour ce contact : la nouvelle la COMPLETE (rien n'est
    -- perdu), et l'ancienne est marquee « remplacee ». La plus recente gagne champ par champ.
    select coalesce(jsonb_object_agg(e.key, e.value), '{}'::jsonb) into avant
      from public.app_contact_saisie_modif s, jsonb_each(s.saisie) e
     where s.hektor_contact_id = k_id and s.etat = 'attente';
    update public.app_contact_saisie_modif set etat = 'remplacee'
     where hektor_contact_id = k_id and etat = 'attente';
    insert into public.app_contact_saisie_modif (job_id, job_type, hektor_contact_id, hektor_target_id, saisie, envoye_le, ecrit_par)
    values (new.id, new.job_type, k_id, k_target, avant || champs, coalesce(new.started_at, new.created_at), new.requested_by)
    on conflict (job_id) do nothing;
  exception when others then
    raise warning 'contact_retour_controle : saisie non gardee pour le travail % (%)', new.id, sqlerrm;
  end;
  return null;
end
$f$;

create trigger app_contact_saisie_modif_job_trg
  after update on public.app_console_job
  for each row
  when (new.status = 'done' and old.status is distinct from 'done'
        and new.job_type in ('update_hektor_contact', 'update_hektor_mandant_contact'))
  execute function public.app_contact_saisie_modif_job_trg();

-- CONTRÔLER : a la premiere ecriture du pipeline dont la date Hektor suit l'envoi
create or replace function public.app_contact_saisie_modif_juge_trg()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_on boolean;
  s    record;
  v    jsonb;
begin
  select lower(trim(coalesce(st.value, ''))) in ('on', '1', 'true', 'oui') into v_on
    from public.app_setting st where st.key = 'contact_retour_controle';
  if not coalesce(v_on, false) then return null; end if;
  begin
    for s in select * from public.app_contact_saisie_modif
              where hektor_contact_id = new.hektor_contact_id and etat = 'attente' loop
      -- une fiche plus ancienne que l'envoi porte l'ANCIEN Hektor : elle ne juge rien.
      -- (2 minutes de marge pour l'horloge de Hektor ; date_maj est l'heure de Paris.)
      if coalesce(new.date_maj, '') < to_char((s.envoye_le - interval '2 minutes') at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS') then
        continue;
      end if;
      v := public.app_contact_verdict_modif(s.saisie, to_jsonb(new));
      update public.app_contact_saisie_modif set
        etat       = 'juge',
        verdict    = v,
        verdict_le = now(),
        ecarts     = (select count(*) from jsonb_each(v) e where e.value->>'etat' in ('remplace', 'absent'))
       where job_id = s.job_id;
    end loop;
  exception when others then
    raise warning 'contact_retour_controle : verdict ignore pour % (%)', new.hektor_contact_id, sqlerrm;
  end;
  return null;
end
$f$;

create trigger app_contact_saisie_modif_juge_trg
  after update on public.app_contact_current
  for each row
  when (new.refreshed_at is distinct from old.refreshed_at)
  execute function public.app_contact_saisie_modif_juge_trg();

-- SIGNALER : une ligne par contact ET par champ en ecart -- jamais « N sur M »
create view public.app_v_contact_modif_ecarts
  with (security_invoker = true) as
select s.job_id, s.hektor_contact_id, s.hektor_target_id, c.nom, c.prenom, c.negociateur_email,
       e.key as champ, e.value->>'envoye' as envoye, e.value->>'relu' as relu, e.value->>'etat' as etat,
       s.envoye_le, s.verdict_le, s.traite_le
  from public.app_contact_saisie_modif s
  cross join lateral jsonb_each(coalesce(s.verdict, '{}'::jsonb)) e
  left join public.app_contact_current c on c.hektor_contact_id = s.hektor_contact_id
 where s.etat = 'juge' and e.value->>'etat' in ('remplace', 'absent')
union all
select s.job_id, s.hektor_contact_id, s.hektor_target_id, c.nom, c.prenom, c.negociateur_email,
       null, null, null, 'non_relu', s.envoye_le, s.verdict_le, s.traite_le
  from public.app_contact_saisie_modif s
  left join public.app_contact_current c on c.hektor_contact_id = s.hektor_contact_id
 where s.etat = 'attente' and s.envoye_le < now() - interval '24 hours';
revoke all on public.app_v_contact_modif_ecarts from public, anon, authenticated;
grant select on public.app_v_contact_modif_ecarts to service_role;

-- « vu » : un admin a regarde -> la sentinelle se tait pour ce travail
create or replace function public.app_contact_modif_ecart_traiter(p_job_id uuid)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  n int;
begin
  if coalesce(public.app_console_current_role(), '') <> 'admin' then
    raise exception 'admin_requis' using errcode = '42501';
  end if;
  update public.app_contact_saisie_modif
     set traite_le = now(), traite_par = auth.uid()
   where job_id = p_job_id and traite_le is null;
  get diagnostics n = row_count;
  return jsonb_build_object('job_id', p_job_id, 'marque', n);
end
$f$;

revoke all on function public.app_contact_champs_modif(jsonb) from public, anon, authenticated;
revoke all on function public.app_contact_meme_valeur(text, text) from public, anon, authenticated;
revoke all on function public.app_contact_verdict_modif(jsonb, jsonb) from public, anon, authenticated;
revoke all on function public.app_contact_saisie_modif_job_trg() from public, anon, authenticated;
revoke all on function public.app_contact_saisie_modif_juge_trg() from public, anon, authenticated;
revoke all on function public.app_contact_modif_ecart_traiter(uuid) from public, anon;
grant execute on function public.app_contact_modif_ecart_traiter(uuid) to authenticated;

-- LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'interrupteur pose, ETEINT' AS controle,
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'contact_retour_controle') = 'off' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la table existe, vide, fermee a anon et authenticated',
       CASE WHEN (SELECT count(*) FROM public.app_contact_saisie_modif) = 0
             AND NOT has_table_privilege('anon', 'public.app_contact_saisie_modif', 'SELECT')
             AND NOT has_table_privilege('authenticated', 'public.app_contact_saisie_modif', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les deux declencheurs sont poses',
       CASE WHEN (SELECT count(*) FROM pg_trigger WHERE tgname IN ('app_contact_saisie_modif_job_trg', 'app_contact_saisie_modif_juge_trg')) = 2 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'la modification de contact n''est PAS retouchee (79d39e0e ou eb93494b si 8a-A est pose)',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_edit_contact_optimistic(text,jsonb,integer)'::regprocedure), chr(13), ''))
                 IN ('79d39e0e506d8afd3224fe20624598b3', 'eb93494b0856706f1f0426da7571d306') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la vue est fermee a anon et authenticated',
       CASE WHEN NOT has_table_privilege('anon', 'public.app_v_contact_modif_ecarts', 'SELECT')
             AND NOT has_table_privilege('authenticated', 'public.app_v_contact_modif_ecarts', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 6, 'le marquage « vu » est ouvert aux connectes, ferme a anon',
       CASE WHEN has_function_privilege('authenticated', 'public.app_contact_modif_ecart_traiter(uuid)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_contact_modif_ecart_traiter(uuid)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
