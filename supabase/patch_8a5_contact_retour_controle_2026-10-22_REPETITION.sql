-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a-B — le contrôle au retour d'une modification de contact — TOUT EST ANNULÉ
--                                                                    22/10/2026
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … ».
-- Elle pose LE VRAI PATCH, joue 15 essais sur le contact d'essai 20000007 (de faux travaux
-- et de fausses relectures, dans la même transaction), puis LE VRAI RETOUR ARRIÈRE.
-- Rien ne reste : ni objet, ni interrupteur, ni travail, ni fiche modifiée.
-- Fichier GÉNÉRÉ (phase2/checks/gen_patch_8a5_contact_retour_controle.py) : ne pas le retoucher à la main.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

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

DO $essai$
DECLARE
    sub  text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    cid  text := '20000007';
    tgt  text;
    j1 uuid; j2 uuid; j3 uuid; j4 uuid; j5 uuid; j6 uuid;
    n int;
    v jsonb;
    t text;
    paris text;
BEGIN
    IF NOT EXISTS (select 1 from public.app_contact_current where hektor_contact_id = cid) THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai 20000007 n''existe plus -- la repetition ne prouverait rien.';
    END IF;
    select hektor_target_id into tgt from public.app_contact_current where hektor_contact_id = cid;

    -- (1) ETEINT : un travail reussi ne garde rien (le temoin inverse)
    update public.app_setting set value = 'off' where key = 'contact_retour_controle';
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('update_hektor_contact', 'running', jsonb_build_object('hektor_contact_id', cid, 'from_pending', true, 'last_name', 'ESSAI 8A BIS', 'city', 'Saint-Étienne'), now())
    returning id into j1;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j1;
    select count(*) into n from public.app_contact_saisie_modif;
    insert into _m values (1, 'eteint : aucune saisie gardee', case when n = 0 then 'OK' else 'ECHEC ' || n end);

    update public.app_setting set value = 'on' where key = 'contact_retour_controle';

    -- (2) ALLUME : un travail « held_conflict » ne garde rien
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('update_hektor_contact', 'running', jsonb_build_object('hektor_contact_id', cid, 'last_name', 'X'), now())
    returning id into j2;
    update public.app_console_job set status = 'done', result_json = '{"status":"held_conflict"}'::jsonb, finished_at = now() where id = j2;
    select count(*) into n from public.app_contact_saisie_modif;
    insert into _m values (2, 'un conflit retenu (held_conflict) ne garde rien', case when n = 0 then 'OK' else 'ECHEC ' || n end);

    -- (3) ALLUME : un travail reussi garde les 10 colonnes, sans les 3 propres a l'app, par NOTRE cle
    insert into public.app_console_job (job_type, status, payload_json, started_at, requested_by)
    values ('update_hektor_contact', 'running',
            jsonb_build_object('hektor_contact_id', cid, 'from_pending', true,
                               'last_name', 'ESSAI 8A BIS', 'first_name', 'Relecture', 'civility', 'M.',
                               'phone', '06 00 00 25 08', 'city', 'Saint-Étienne', 'postal_code', '',
                               'address', '3 rue de la Chaine', 'comments', 'Commentaire B',
                               'birth_date', '1980-01-01', 'company_name', 'SOCIETE X'),
            now() - interval '10 seconds', sub::uuid)
    returning id into j3;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j3;
    select saisie into v from public.app_contact_saisie_modif where job_id = j3 and etat = 'attente' and hektor_contact_id = cid;
    insert into _m values (3, 'reussi : la saisie est gardee par notre cle, 7 colonnes (code postal vide, naissance et societe exclus)',
        case when v is not null and (select count(*) from jsonb_object_keys(v)) = 7
                  and v->>'ville' = 'Saint-Étienne' and not v ? 'code_postal' and not v ? 'birth_date' and not v ? 'company_name'
                  and v->>'civilite' = 'M.' and v->>'commentaires' = 'Commentaire B'
             then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (4) le meme travail, la porte du mandant (numero HEKTOR dans la charge, « civilite ») : retrouve notre cle
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('update_hektor_mandant_contact', 'running',
            jsonb_build_object('hektor_contact_id', tgt, 'contact_id', tgt, 'civilite', 'Mme.', 'email', 'essai.8ab@example.invalid'),
            now() - interval '5 seconds')
    returning id into j4;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j4;
    select saisie into v from public.app_contact_saisie_modif where job_id = j4;
    insert into _m values (4, 'porte du mandant (numero Hektor) : meme contact, la nouvelle saisie COMPLETE l''ancienne, qui est « remplacee »',
        case when v is not null and v->>'civilite' = 'Mme.' and v->>'email' = 'essai.8ab@example.invalid' and v->>'ville' = 'Saint-Étienne'
                  and (select etat from public.app_contact_saisie_modif where job_id = j3) = 'remplacee'
                  and (select hektor_contact_id from public.app_contact_saisie_modif where job_id = j4) = cid
             then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (5) une ecriture de l'ECRAN (refreshed_at inchange) ne juge rien
    update public.app_contact_current set ville = 'Saint-Étienne' where hektor_contact_id = cid;
    select count(*) into n from public.app_contact_saisie_modif where etat = 'juge';
    insert into _m values (5, 'une ecriture de l''ecran (refreshed_at inchange) ne juge rien', case when n = 0 then 'OK' else 'ECHEC ' || n end);

    -- (6) une ecriture du pipeline qui porte l'ANCIEN Hektor (date_maj d'avant l'envoi) ne juge rien
    update public.app_contact_current set refreshed_at = now() + interval '1 second', date_maj = '2026-10-21 18:48:06', ville = null
     where hektor_contact_id = cid;
    select count(*) into n from public.app_contact_saisie_modif where etat = 'juge';
    insert into _m values (6, 'le pipeline avec l''ANCIEN Hektor (date d''avant l''envoi) ne juge rien', case when n = 0 then 'OK' else 'ECHEC ' || n end);

    -- (7) LE RETOUR : Hektor a perdu la ville, mis le prenom en minuscules, ecrit le telephone autrement,
    --     change le commentaire, garde l'e-mail et la civilite
    paris := to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS');
    update public.app_contact_current set refreshed_at = now() + interval '2 seconds', date_maj = paris,
           nom = 'ESSAI 8A BIS', prenom = 'relecture', civilite = 'Mme.', email = 'essai.8ab@example.invalid',
           phone_primary = '0600002508', ville = null, adresse = '3 rue de la Chaine', commentaires = 'Commentaire Hektor'
     where hektor_contact_id = cid;
    select verdict into v from public.app_contact_saisie_modif where job_id = j4 and etat = 'juge';
    insert into _m values (7, 'le retour est juge : ville absent, prenom et telephone autre_forme, commentaire remplace, le reste identique',
        case when v->'ville'->>'etat' = 'absent' and v->'prenom'->>'etat' = 'autre_forme' and v->'phone_primary'->>'etat' = 'autre_forme'
                  and v->'commentaires'->>'etat' = 'remplace' and v->'nom'->>'etat' = 'identique' and v->'email'->>'etat' = 'identique'
                  and v->'civilite'->>'etat' = 'identique' and v->'adresse'->>'etat' = 'identique'
                  and (select ecarts from public.app_contact_saisie_modif where job_id = j4) = 2
             then 'OK' else 'ECHEC ' || coalesce(v::text, 'pas juge') end);

    -- (8) la vue : une ligne par CHAMP en ecart (2), pas la saisie « remplacee »
    select count(*) into n from public.app_v_contact_modif_ecarts where job_id in (j3, j4);
    select string_agg(champ || '=' || etat, ',' order by champ) into t from public.app_v_contact_modif_ecarts where job_id in (j3, j4);
    insert into _m values (8, 'la vue : une ligne par champ en ecart (commentaires, ville)', case when n = 2 and t = 'commentaires=remplace,ville=absent' then 'OK' else 'ECHEC ' || n || ' ' || coalesce(t, '') end);

    -- (9) un second retour ne rejuge pas (le verdict est pose une fois)
    update public.app_contact_current set refreshed_at = now() + interval '3 seconds', ville = 'Saint-Étienne' where hektor_contact_id = cid;
    select verdict into v from public.app_contact_saisie_modif where job_id = j4;
    insert into _m values (9, 'un second retour ne rejuge pas', case when v->'ville'->>'etat' = 'absent' then 'OK' else 'ECHEC ' || coalesce(v::text, '') end);

    -- (10) « non_relu » : une saisie en attente depuis plus de 24 h apparait dans la vue
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('update_hektor_contact', 'running', jsonb_build_object('hektor_contact_id', cid, 'last_name', 'ESSAI 8A BIS'), now() - interval '30 hours')
    returning id into j5;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j5;
    select count(*) into n from public.app_v_contact_modif_ecarts where job_id = j5 and etat = 'non_relu';
    insert into _m values (10, 'rien n''est revenu en 24 h : une ligne « non_relu »', case when n = 1 then 'OK' else 'ECHEC ' || n end);

    -- (11) « vu » : refuse a un non-admin, accepte pour un admin, et la sentinelle se tait
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);
    v := public.app_contact_modif_ecart_traiter(j4);
    select count(*) into n from public.app_v_contact_modif_ecarts where job_id = j4 and traite_le is null;
    insert into _m values (11, 'un admin marque « vu » : la ligne sort de ce que la sentinelle compte', case when (v->>'marque')::int = 1 and n = 0 then 'OK' else 'ECHEC ' || v::text || ' ' || n end);

    -- (12) un autre contact, sans saisie : son ecriture passe telle quelle
    update public.app_contact_current set refreshed_at = refreshed_at + interval '1 second'
     where hektor_contact_id = (select hektor_contact_id from public.app_contact_current where hektor_contact_id <> cid limit 1);
    get diagnostics n = row_count;
    insert into _m values (12, 'un autre contact, sans saisie : l''ecriture passe', case when n = 1 then 'OK' else 'ECHEC ' || n end);

    -- (13) une saisie ILLISIBLE : l'ecriture de la fiche passe quand meme (warning seulement)
    insert into public.app_contact_saisie_modif (job_id, job_type, hektor_contact_id, saisie, envoye_le)
    values (gen_random_uuid(), 'update_hektor_contact', cid, '[1,2]'::jsonb, now() - interval '1 minute')
    returning job_id into j6;
    update public.app_contact_current set refreshed_at = now() + interval '4 seconds', date_maj = paris where hektor_contact_id = cid;
    get diagnostics n = row_count;
    insert into _m values (13, 'une saisie illisible ne bloque PAS l''ecriture de la fiche', case when n = 1 then 'OK' else 'ECHEC ' || n end);
    delete from public.app_contact_saisie_modif where job_id = j6;

    -- (14) un travail d'un autre type (annonce) ne declenche rien
    select count(*) into n from public.app_contact_saisie_modif;
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('update_hektor_annonce_fields', 'running', jsonb_build_object('hektor_contact_id', cid, 'last_name', 'Z'), now())
    returning id into j6;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j6;
    insert into _m values (14, 'un travail d''annonce ne garde rien', case when (select count(*) from public.app_contact_saisie_modif) = n then 'OK' else 'ECHEC' end);

    -- (15) la meme valeur sous une autre forme
    insert into _m values (15, 'autre forme : Saint-Etienne / Saint-Étienne, FIRMINY / Firminy, 06 47.91.70.39 / 0647917039 ; et 42700 / 42000 NON',
        case when public.app_contact_meme_valeur('Saint-Etienne', 'Saint-Étienne') and public.app_contact_meme_valeur('FIRMINY', 'Firminy')
                  and public.app_contact_meme_valeur('06 47.91.70.39', '0647917039') and not public.app_contact_meme_valeur('42700', '42000')
                  and not public.app_contact_meme_valeur('Saint-Étienne', null)
             then 'OK' else 'ECHEC' end);
END
$essai$;

-- LE VRAI RETOUR ARRIÈRE
drop trigger if exists app_contact_saisie_modif_job_trg on public.app_console_job;
drop trigger if exists app_contact_saisie_modif_juge_trg on public.app_contact_current;
drop view if exists public.app_v_contact_modif_ecarts;
drop function if exists public.app_contact_saisie_modif_job_trg();
drop function if exists public.app_contact_saisie_modif_juge_trg();
drop function if exists public.app_contact_modif_ecart_traiter(uuid);
drop function if exists public.app_contact_verdict_modif(jsonb, jsonb);
drop function if exists public.app_contact_meme_valeur(text, text);
drop function if exists public.app_contact_champs_modif(jsonb);

DO $garde_saisie$
DECLARE
    n int;
    nom text := 'app_contact_saisie_modif_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_contact_saisie_modif') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_contact_saisie_modif n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_contact_saisie_modif' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_contact_saisie_modif';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_contact_saisie_modif rename to %I', nom);
        RAISE NOTICE '%', format('%s saisie(s) gardee(s) sous public.%s', n, nom);
    END IF;
END
$garde_saisie$;

delete from public.app_setting where key = 'contact_retour_controle';

DO $fin$
DECLARE
    r text;
    ok int;
    total int;
BEGIN
    insert into _m values (16, 'le retour arriere a tout retire',
        case when to_regclass('public.app_contact_saisie_modif') IS NULL
                  AND to_regclass('public.app_v_contact_modif_ecarts') IS NULL
                  AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname IN ('app_contact_saisie_modif_job_trg', 'app_contact_saisie_modif_juge_trg'))
                  AND NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_retour_controle')
             then 'OK' else 'ECHEC' end);
    select count(*) filter (where valeur = 'OK'), count(*), string_agg(n || ' ' || valeur || ' ' || cle, ' | ' order by n)
      into ok, total, r from _m;
    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s | %s', ok, total, r);
END
$fin$;
