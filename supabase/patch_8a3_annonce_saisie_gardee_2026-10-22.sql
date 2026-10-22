-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · PIÈCE 3 (8a, N.2) — LA SAISIE DE CRÉATION SURVIT AU RETOUR DE HEKTOR
--                                                                    22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (pièce 3)
-- Décision de Frédéric, 22/10 : « les quatre » — garder, contrôler, afficher, signaler.
--
-- LE DÉFAUT, mesuré le 22/10 sur l'essai 10000006 / 63330 : la pièce 2 range la saisie
-- DANS la fiche détaillée ; la relecture de Hektor REMPLACE cette fiche — la saisie part
-- avec. Ce que Hektor ne rend pas (le secteur, le diagnostiqueur, les honoraires
-- détaillés : la « console seule ») disparaît de l'écran ; et personne ne compare ce qui
-- est revenu à ce qui a été envoyé (N.2, cadrée le 28/09, jamais codée).
-- C'est la RÈGLE 2 — « Hektor confirme, il n'écrase pas » — qui n'était pas appliquée à
-- la création ; elle l'est à la modification (L3, 21/09) et au contact (3 champs).
--
-- CE QUE FAIT CE PATCH — ADDITIF, derrière l'interrupteur 'annonce_saisie_gardee' (off) :
--   A  GARDER     une table à part, app_annonce_saisie_naissance : une ligne par annonce
--                 née dans l'app, la saisie et le calque. LA RELECTURE NE LA TOUCHE JAMAIS.
--   B  CONTRÔLER  à la première fiche qui n'est plus la nôtre (celle de Hektor), un verdict
--                 champ par champ : identique · autre_forme · recalcule · remplace ·
--                 absent · console_seule. Les « console seule » sont rejugés quand la
--                 console passe.
--   C  AFFICHER   les champs « console seule » sont reposés dans le calque de la fiche :
--                 la valeur de Hektor s'il l'a rendue, sinon la nôtre. Une saisie encore en
--                 attente (L3) GAGNE toujours. Une modification ultérieure d'un de ces champs
--                 dans l'app met la saisie gardée à jour (la valeur la plus récente).
--   D  SIGNALER   une vue, une ligne par annonce ET par champ en écart (remplace, absent) ;
--                 une fonction pour marquer l'écart « vu » (admin) ; la sentinelle
--                 data.annonce_naissance_ecart dans monitoring/check_gti_health.py.
-- Tout passe par UN déclencheur sur app_dossier_detail_current : il voit TOUTES les portes
-- qui écrivent la fiche (la naissance, la relecture d'une annonce, le run de nuit, une
-- modification, L3) — leçon « une exclusion rangée à part doit être appelée par chaque porte ».
-- ⛔ Un échec dans le déclencheur ne peut JAMAIS empêcher une écriture de la fiche : il
--    s'avale (raise warning) et la ligne passe telle qu'elle est arrivée.
-- ⚠ Ce patch ne retouche AUCUNE fonction existante. Il ne vaut que pour les annonces nées
--    APRÈS son allumage (la ligne gardée naît avec la fiche de départ, pièce 2).
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'annonce_saisie_gardee';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'annonce_saisie_gardee';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_8a3_annonce_saisie_gardee_2026-10-22_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
    IF to_regclass('public.app_annonce_saisie_naissance') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la table app_annonce_saisie_naissance existe deja. Rien n''est ecrit.';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.app_dossier_detail_current'::regclass
                AND tgname = 'app_annonce_saisie_naissance_trg') THEN
        RAISE EXCEPTION '%', 'ARRET : le declencheur existe deja. Rien n''est ecrit.';
    END IF;
END
$garde$;

-- 0. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('annonce_saisie_gardee', 'off',
        'Chantier 8 / 8a piece 3 22/10/2026 : on = la saisie de creation d''une annonce est gardee a part, jugee au retour de Hektor, et les champs que Hektor ne rend pas restent affiches (voir supabase/patch_8a3_annonce_saisie_gardee_2026-10-22.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- A. LA TABLE À PART
create table public.app_annonce_saisie_naissance (
  app_dossier_id     bigint primary key,
  hektor_annonce_id  bigint,
  saisie             jsonb not null,          -- la saisie de l'ecran, sans le mandant
  calque             jsonb not null,          -- nom Hektor -> valeur, tel que la fiche le lit
  ecrit_le           timestamptz not null default now(),
  ecrit_par          uuid,
  verdict            jsonb,                   -- { champ: { envoye, relu, etat } }
  verdict_le         timestamptz,
  ecarts             integer,                 -- remplace + absent
  console_seule      integer,                 -- en attente de la console
  maj_le             timestamptz,
  traite_le          timestamptz,             -- un humain a vu les ecarts
  traite_par         uuid
);
comment on table public.app_annonce_saisie_naissance is
  'Chantier 8 / 8a piece 3 (22/10/2026) : la saisie de creation d''une annonce nee dans l''app, gardee A PART de la fiche detaillee (que la relecture de Hektor remplace), et son verdict au retour. Ecrite uniquement par le declencheur app_annonce_saisie_naissance_trg.';
alter table public.app_annonce_saisie_naissance enable row level security;
revoke all on public.app_annonce_saisie_naissance from public, anon, authenticated;
grant select, insert, update, delete on public.app_annonce_saisie_naissance to service_role;

-- Les champs que l'API de Hektor ne rend jamais (extract_hektor_missing_fields.js l. 24-36),
-- et le chauffage (son propre extracteur, extract_hektor_chauffage_only.js).
create or replace function public.app_annonce_champs_console()
 returns text[]
 language sql
 immutable
as $f$
  select array['immeuble','TRANSPORT','PROXIMITE','ENVIRONNEMENT',
               'diagnostiqueur','syndic',
               '_selecterHonoraires2','_tauxHonoraire2','_pourcentHonoraire2','_detailHonoraire2',
               '_selecterHonoraires3','_tauxHonoraire3','_pourcentHonoraire3','_detailHonoraire3',
               'Loc_EstimationLoyer','Loc_ChargeLocative','Loc_RendementBrut','Loc_Occupation',
               'formatChauff','typeChauff','energieChauff']::text[]
$f$;

-- un bloc de la fiche qui peut etre un objet, une liste, ou une CHAINE contenant du JSON
create or replace function public.app_annonce_bloc(j jsonb, cle text)
 returns jsonb
 language plpgsql
 immutable
as $f$
begin
  if j is null or not (j ? cle) then return null; end if;
  if jsonb_typeof(j->cle) in ('object', 'array') then return j->cle; end if;
  if jsonb_typeof(j->cle) = 'string' and nullif(trim(j->>cle), '') is not null then
    begin
      return (j->>cle)::jsonb;
    exception when others then
      return null;
    end;
  end if;
  return null;
end
$f$;

-- le bloc de la console qui porte ce champ est-il arrive ?
create or replace function public.app_annonce_porteur_present(j jsonb, n text)
 returns boolean
 language plpgsql
 immutable
as $f$
declare
  cle text;
  b   jsonb;
begin
  cle := case
    when n in ('immeuble','TRANSPORT','PROXIMITE','ENVIRONNEMENT') then 'secteur_console_json'
    when n in ('diagnostiqueur','syndic') then 'diagnostics_contacts_console_json'
    when n like '\_%Honoraire%' then 'honoraires_detail_console_json'
    when n like 'Loc\_%' then 'location_rendement_console_json'
    when n in ('formatChauff','typeChauff','energieChauff') then 'chauffage_console_json'
    else null end;
  if cle is null then return true; end if;   -- un champ de l'API : sa source est toujours la
  b := public.app_annonce_bloc(j, cle);
  -- ⚠ coalesce : un bloc ABSENT (cle a null) donne un jsonb_typeof NULL, donc une reponse
  --   « inconnue » -- et « not inconnu » fait sauter la condition. La repetition du 22/10
  --   l'a attrape : les 9 « console seule » de 63330 sortaient « absent », aucun repose.
  if cle = 'chauffage_console_json' then
    return coalesce(jsonb_typeof(b) = 'array' and jsonb_array_length(b) > 0, false);
  end if;
  return coalesce(jsonb_typeof(b) = 'object', false);
end
$f$;

-- B. LA LECTURE DE HEKTOR, champ par champ : la cible FIGEE (tableau des 173, 22/10).
--    Comme wizardDetailValue (App.tsx:2631) mais SANS le calque : on veut ce que Hektor dit.
create or replace function public.app_annonce_lecture_hektor(j jsonb, n text)
 returns text
 language plpgsql
 immutable
as $f$
declare
  v   text;
  raw jsonb;
  g   text;
  c   text;
  blk text;
  b   jsonb;
begin
  if j is null or n is null then return null; end if;
  -- 1. les noms a plat (le dictionnaire `mapped` de wizardDetailValue)
  v := case n
    when 'titre'          then nullif(trim(j->>'texte_principal_titre'), '')
    when 'corps'          then coalesce(nullif(trim(j->>'texte_principal_html'), ''), nullif(trim(j->>'corps_listing_html'), ''))
    when 'prix'           then nullif(trim(j->>'prix_publique'), '')
    when 'PRIXNETVENDEUR' then nullif(trim(j->>'prix_net_vendeur'), '')
    when 'surfappart'     then coalesce(nullif(trim(j->>'surface_habitable_detail'), ''), nullif(trim(j->>'surface'), ''))
    when 'surfterrain'    then nullif(trim(j->>'surface_terrain_detail'), '')
    when 'nbpieces'       then nullif(trim(j->>'nb_pieces'), '')
    when 'NB_CHAMBRES'    then nullif(trim(j->>'nb_chambres'), '')
    when 'codepublique'   then coalesce(nullif(trim(j->>'code_postal_public_listing'), ''), nullif(trim(j->>'code_postal_detail'), ''), nullif(trim(j->>'code_postal'), ''))
    when 'villepublique'  then coalesce(nullif(trim(j->>'ville_publique_listing'), ''), nullif(trim(j->>'ville_publique_detail'), ''), nullif(trim(j->>'ville_privee_detail'), ''))
    when 'adresse'        then coalesce(nullif(trim(j->>'adresse_privee_listing'), ''), nullif(trim(j->>'adresse_detail'), ''))
    when 'villeprivee'    then nullif(trim(j->>'ville_privee_detail'), '')
    when 'codeprive'      then coalesce(nullif(trim(j->>'code_postal_prive_detail'), ''), nullif(trim(j->>'code_postal'), ''))
    when 'latitude'       then nullif(trim(j->>'latitude_detail'), '')
    when 'longitude'      then nullif(trim(j->>'longitude_detail'), '')
    when 'dateenr'        then nullif(trim(j->>'date_enregistrement_annonce'), '')
    when 'diffusable'     then nullif(trim(j->>'diffusable'), '')
    else null end;
  if v is not null then return v; end if;
  -- 2. les 11 groupes bruts de l'API (hektorWizardRawDetailGroups), nom et nom +/- « - »
  raw := public.app_annonce_bloc(j, 'detail_raw_json');
  if jsonb_typeof(raw) = 'object' then
    foreach g in array array['mandat_infofi','mandat_mandatdispo','secteur','ag_interieur','ag_exterieur',
                             'terrain','equipements','diagnostiques','copropriete','construction_recente',
                             'organiser_visite'] loop
      foreach c in array array[n, case when right(n, 1) = '-' then left(n, -1) else n || '-' end] loop
        v := nullif(trim(raw->g->'props'->c->>'value'), '');
        if v is not null then return v; end if;
      end loop;
    end loop;
  end if;
  -- 3. les blocs de la console
  foreach blk in array array['secteur_console_json','diagnostics_contacts_console_json',
                             'honoraires_detail_console_json','location_rendement_console_json'] loop
    b := public.app_annonce_bloc(j, blk);
    if jsonb_typeof(b) = 'object' then
      v := nullif(trim(b->n->>'value'), '');
      if v is not null then return v; end if;
    end if;
  end loop;
  -- 4. le chauffage (1re entree)
  if n in ('formatChauff','typeChauff','energieChauff') then
    b := public.app_annonce_bloc(j, 'chauffage_console_json');
    if jsonb_typeof(b) = 'array' and jsonb_array_length(b) > 0 then
      v := nullif(trim(b->0->(case n when 'formatChauff' then 'format' when 'typeChauff' then 'type' else 'energie' end)->>'value'), '');
    end if;
  end if;
  return v;
end
$f$;

-- meme valeur sous une autre forme : une date jj-mm-aaaa / aaaa-mm-jj, un nombre « 150000 » / « 150000.00 »
create or replace function public.app_annonce_meme_valeur(a text, b text)
 returns boolean
 language plpgsql
 immutable
as $f$
begin
  if a is null or b is null then return false; end if;
  if lower(trim(a)) = lower(trim(b)) then return true; end if;
  if a ~ '^\d{2}[-/.]\d{2}[-/.]\d{4}$' and b ~ '^\d{4}-\d{2}-\d{2}'
     and substr(a, 7, 4) || '-' || substr(a, 4, 2) || '-' || substr(a, 1, 2) = left(b, 10) then
    return true;
  end if;
  if b ~ '^\d{2}[-/.]\d{2}[-/.]\d{4}$' and a ~ '^\d{4}-\d{2}-\d{2}'
     and substr(b, 7, 4) || '-' || substr(b, 4, 2) || '-' || substr(b, 1, 2) = left(a, 10) then
    return true;
  end if;
  if replace(trim(a), ',', '.') ~ '^-?\d+(\.\d+)?$' and replace(trim(b), ',', '.') ~ '^-?\d+(\.\d+)?$' then
    return replace(trim(a), ',', '.')::numeric = replace(trim(b), ',', '.')::numeric;
  end if;
  return false;
end
$f$;

create or replace function public.app_annonce_verdict_naissance(calque jsonb, j jsonb)
 returns jsonb
 language plpgsql
 immutable
as $f$
declare
  k    text;
  e    text;
  r    text;
  etat text;
  out  jsonb := '{}'::jsonb;
begin
  if jsonb_typeof(calque) <> 'object' then return out; end if;
  for k in select jsonb_object_keys(calque) loop
    if jsonb_typeof(calque->k) not in ('string', 'number') then continue; end if;
    e := nullif(trim(calque->>k), '');
    if e is null then continue; end if;
    r := public.app_annonce_lecture_hektor(j, k);
    etat := case
      when r is null and k = any(public.app_annonce_champs_console()) and not public.app_annonce_porteur_present(j, k) then 'console_seule'
      when r is null then 'absent'
      when r = e then 'identique'
      when k in ('latitude', 'longitude') then 'recalcule'
      when public.app_annonce_meme_valeur(e, r) then 'autre_forme'
      else 'remplace' end;
    out := out || jsonb_build_object(k, jsonb_build_object('envoye', e, 'relu', r, 'etat', etat));
  end loop;
  return out;
end
$f$;

-- A + B + C. LE DÉCLENCHEUR — il voit toutes les portes qui écrivent la fiche.
create or replace function public.app_annonce_saisie_naissance_trg()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_on    boolean;
  j       jsonb;
  s       public.app_annonce_saisie_naissance%rowtype;
  v       jsonb;
  ov      jsonb;
  k       text;
  val     text;
  reinj   jsonb := '{}'::jsonb;
  majcal  jsonb := '{}'::jsonb;
  rejuge  boolean := false;
  nouveau text;
begin
  select lower(trim(coalesce(st.value, ''))) in ('on', '1', 'true', 'oui') into v_on
    from public.app_setting st where st.key = 'annonce_saisie_gardee';
  if not coalesce(v_on, false) then return new; end if;

  begin
    -- A. LA NAISSANCE : la fiche de depart (piece 2) porte la saisie -> on la garde a part
    if coalesce(new.source_hash, '') like 'c9e3:%' then
      j := new.detail_payload_json::jsonb;
      if jsonb_typeof(j->'app_saisie_creation') = 'object' then
        insert into public.app_annonce_saisie_naissance (app_dossier_id, saisie, calque, ecrit_par)
        values (new.app_dossier_id, j->'app_saisie_creation',
                case when jsonb_typeof(j->'app_optimistic_overlay') = 'object' then j->'app_optimistic_overlay' else '{}'::jsonb end,
                auth.uid())
        on conflict (app_dossier_id) do nothing;
      end if;
      return new;
    end if;

    -- une annonce sans saisie gardee : on ne touche a rien (le cas de 99,9 % des ecritures)
    select * into s from public.app_annonce_saisie_naissance where app_dossier_id = new.app_dossier_id;
    if not found then return new; end if;

    j  := new.detail_payload_json::jsonb;
    ov := case when jsonb_typeof(j->'app_optimistic_overlay') = 'object' then j->'app_optimistic_overlay' else '{}'::jsonb end;

    -- C (bis). une MODIFICATION dans l'app d'un champ « console seule » : la saisie gardee
    --          prend la valeur la plus recente (sinon on reposerait l'ancienne).
    --          ⚠ Une valeur du calque EGALE a ce que Hektor rend n'est PAS une saisie : c'est
    --          nous qui l'y avons reposee (C). La prendre pour une saisie effacerait en silence
    --          un ecart « remplace » (defaut trouve a la relecture du patch, 22/10).
    foreach k in array public.app_annonce_champs_console() loop
      if ov ? k and jsonb_typeof(ov->k) in ('string', 'number')
         and nullif(trim(ov->>k), '') is not null
         and (s.calque->>k) is distinct from trim(ov->>k)
         and public.app_annonce_lecture_hektor(j, k) is distinct from trim(ov->>k) then
        majcal := majcal || jsonb_build_object(k, trim(ov->>k));
      end if;
    end loop;
    if majcal <> '{}'::jsonb then
      s.calque := s.calque || majcal;
    end if;

    -- B. LE VERDICT : la premiere fiche de Hektor, puis les « console seule » rejuges
    if s.verdict is null then
      v := public.app_annonce_verdict_naissance(s.calque, j);
      rejuge := true;
    else
      v := s.verdict;
      for k in select e.key from jsonb_each(s.verdict) e where e.value->>'etat' = 'console_seule'
               union
               select jsonb_object_keys(majcal) loop
        if public.app_annonce_porteur_present(j, k) or majcal ? k then
          v := v || public.app_annonce_verdict_naissance(jsonb_build_object(k, s.calque->>k), j);
          rejuge := true;
        end if;
      end loop;
    end if;
    if rejuge or majcal <> '{}'::jsonb then
      update public.app_annonce_saisie_naissance set
        calque            = s.calque,
        verdict           = v,
        verdict_le        = coalesce(verdict_le, now()),
        hektor_annonce_id = coalesce(new.hektor_annonce_id, hektor_annonce_id),
        ecarts            = (select count(*) from jsonb_each(v) e where e.value->>'etat' in ('remplace', 'absent')),
        console_seule     = (select count(*) from jsonb_each(v) e where e.value->>'etat' = 'console_seule'),
        maj_le            = now()
       where app_dossier_id = new.app_dossier_id;
    end if;

    -- C. AFFICHER : pour chaque champ « console seule » saisi, la valeur de Hektor s'il l'a
    --    rendue, sinon la notre tant que son bloc n'est pas arrive. Hektor vide -> rien.
    foreach k in array public.app_annonce_champs_console() loop
      if nullif(trim(coalesce(s.calque->>k, '')), '') is null then continue; end if;
      val := public.app_annonce_lecture_hektor(j, k);
      if val is null and not public.app_annonce_porteur_present(j, k) then
        val := trim(s.calque->>k);
      end if;
      if val is not null then
        reinj := reinj || jsonb_build_object(k, val);
      end if;
    end loop;
    if reinj <> '{}'::jsonb then
      -- une saisie deja dans le calque (en attente, L3) GAGNE : elle passe en dernier
      nouveau := (j || jsonb_build_object('app_optimistic_overlay', reinj || ov))::text;
    end if;
  exception when others then
    raise warning 'annonce_saisie_gardee : declencheur ignore pour % (%)', new.app_dossier_id, sqlerrm;
    return new;
  end;

  if nouveau is not null then
    new.detail_payload_json := nouveau;
  end if;
  return new;
end
$f$;

create trigger app_annonce_saisie_naissance_trg
  before insert or update on public.app_dossier_detail_current
  for each row execute function public.app_annonce_saisie_naissance_trg();

-- D. SIGNALER : une ligne par annonce ET par champ en ecart (jamais « N sur M »)
create view public.app_v_annonce_naissance_ecarts
  with (security_invoker = true) as
select s.app_dossier_id, s.hektor_annonce_id, d.titre_bien, d.ville, d.commercial_nom,
       e.key as champ, e.value->>'envoye' as envoye, e.value->>'relu' as relu, e.value->>'etat' as etat,
       s.verdict_le, s.traite_le
  from public.app_annonce_saisie_naissance s
  cross join lateral jsonb_each(coalesce(s.verdict, '{}'::jsonb)) e
  left join public.app_dossier_current d on d.app_dossier_id = s.app_dossier_id
 where e.value->>'etat' in ('remplace', 'absent');
revoke all on public.app_v_annonce_naissance_ecarts from public, anon, authenticated;
grant select on public.app_v_annonce_naissance_ecarts to service_role;

-- « vu » : un admin a regarde les ecarts de cette annonce -> la sentinelle se tait pour elle
create or replace function public.app_annonce_naissance_ecart_traiter(p_app_dossier_id bigint)
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
  update public.app_annonce_saisie_naissance
     set traite_le = now(), traite_par = auth.uid()
   where app_dossier_id = p_app_dossier_id and traite_le is null;
  get diagnostics n = row_count;
  return jsonb_build_object('app_dossier_id', p_app_dossier_id, 'marque', n);
end
$f$;

revoke all on function public.app_annonce_champs_console() from public, anon, authenticated;
revoke all on function public.app_annonce_bloc(jsonb, text) from public, anon, authenticated;
revoke all on function public.app_annonce_porteur_present(jsonb, text) from public, anon, authenticated;
revoke all on function public.app_annonce_lecture_hektor(jsonb, text) from public, anon, authenticated;
revoke all on function public.app_annonce_meme_valeur(text, text) from public, anon, authenticated;
revoke all on function public.app_annonce_verdict_naissance(jsonb, jsonb) from public, anon, authenticated;
revoke all on function public.app_annonce_saisie_naissance_trg() from public, anon, authenticated;
revoke all on function public.app_annonce_naissance_ecart_traiter(bigint) from public, anon;
grant execute on function public.app_annonce_naissance_ecart_traiter(bigint) to authenticated;

-- LES CONTROLES
SELECT 1 AS "#", 'interrupteur pose, ETEINT' AS controle,
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'annonce_saisie_gardee') = 'off' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la table existe, vide, fermee a anon et authenticated',
       CASE WHEN (SELECT count(*) FROM public.app_annonce_saisie_naissance) = 0
             AND NOT has_table_privilege('anon', 'public.app_annonce_saisie_naissance', 'SELECT')
             AND NOT has_table_privilege('authenticated', 'public.app_annonce_saisie_naissance', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'le declencheur est pose, un seul, sur la fiche detaillee',
       CASE WHEN (SELECT count(*) FROM pg_trigger WHERE tgrelid = 'public.app_dossier_detail_current'::regclass AND NOT tgisinternal) = 1 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'la creation d''annonce n''est PAS retouchee (a5e70b57)',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure), chr(13), '')) = 'a5e70b5734876f74ecd0083681a1ebe8' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la fonction de naissance n''est PAS retouchee (944db16b)',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure), chr(13), '')) = '944db16babc10031b567eb535f74be8b' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 6, 'le marquage « vu » est ouvert aux connectes, ferme a anon',
       CASE WHEN has_function_privilege('authenticated', 'public.app_annonce_naissance_ecart_traiter(bigint)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_annonce_naissance_ecart_traiter(bigint)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
