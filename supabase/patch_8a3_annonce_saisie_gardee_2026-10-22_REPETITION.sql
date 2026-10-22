-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a PIÈCE 3 — garder, contrôler, afficher, signaler — TOUT EST ANNULÉ
--                                                                    22/10/2026
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … ».
-- Elle rejoue, sur la VRAIE fiche de 10000006 / 63330 et sur sa photo de naissance
-- (essai_8a2b_naissance_20261021) : la naissance, le retour de Hektor, l'arrivée de la
-- console, une modification dans l'app, la garde anti-masquage, l'interrupteur éteint,
-- une autre annonce (intacte), une fiche illisible (l'écriture passe), une VRAIE
-- création, la vue des écarts et le marquage « vu » ; puis le vrai retour arrière.
-- ⚠ Une séquence ne revient pas en arrière : 1 numéro d'annonce de l'app consommé.
-- Fichier GÉNÉRÉ (gen_repetition_8a3.py) : ne pas le retoucher à la main.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

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


update public.app_setting set value = 'on', updated_at = now() where key = 'annonce_saisie_gardee';

DO $essai$
DECLARE
  naissance jsonb;
  hk        jsonb;
  hk_hash   text;
  s         public.app_annonce_saisie_naissance%rowtype;
  d         jsonb;
  t         text;
  autre     text;
  autre2    text;
  v_uid     uuid;
  v_job     public.app_console_job;
  v_id      bigint;
  t9        text := '?';
  t8        text := '?';
  t10a int; t10b int; t10c text;
BEGIN
  select detail into naissance from public.essai_8a2b_naissance_20261021;
  select detail_payload_json::jsonb, source_hash into hk, hk_hash from public.app_dossier_detail_current where app_dossier_id = 10000006;
  if naissance is null or hk is null then raise exception 'ESSAI IMPOSSIBLE : photo de naissance ou fiche 10000006 introuvable'; end if;

  -- T1 LA NAISSANCE
  update public.app_dossier_detail_current set source_hash = 'c9e3:repetition-8a3', detail_payload_json = naissance::text where app_dossier_id = 10000006;
  select * into s from public.app_annonce_saisie_naissance where app_dossier_id = 10000006;
  insert into _m values (1, 'T1_saisie_gardee_et_champs_du_calque',
     case when s.app_dossier_id is null then 'NON' else 'oui / ' || (select count(*) from jsonb_object_keys(s.calque)) end);

  -- T2 LE RETOUR DE HEKTOR (sa vraie fiche du 21/10)
  update public.app_dossier_detail_current set source_hash = hk_hash, detail_payload_json = hk::text where app_dossier_id = 10000006;
  select * into s from public.app_annonce_saisie_naissance where app_dossier_id = 10000006;
  select detail_payload_json::jsonb into d from public.app_dossier_detail_current where app_dossier_id = 10000006;
  insert into _m values
   (2, 'T2_verdict_par_etat', (select string_agg(etat || '=' || nb, ' ' order by etat) from (select e.value->>'etat' as etat, count(*) nb from jsonb_each(s.verdict) e group by 1) x)),
   (3, 'T2_ecarts_et_console_seule', s.ecarts || ' / ' || s.console_seule),
   (4, 'T2_les_ecarts_nommes', (select string_agg(e.key || ':' || (e.value->>'etat'), ', ' order by e.key) from jsonb_each(s.verdict) e where e.value->>'etat' in ('remplace','absent'))),
   (5, 'T2_reposes_dans_le_calque', (select count(*) from jsonb_object_keys(coalesce(d->'app_optimistic_overlay','{}'::jsonb))) || ' / TRANSPORT=' || coalesce(d->'app_optimistic_overlay'->>'TRANSPORT','NULL')),
   (6, 'T2_le_reste_de_la_fiche_intact', case when (d - 'app_optimistic_overlay') = (hk - 'app_optimistic_overlay') then 'oui' else 'NON' end);

  -- T3 LA CONSOLE PASSE : Hektor dit Tram (autre), PROXIMITE vide, ENVIRONNEMENT identique
  update public.app_dossier_detail_current
     set detail_payload_json = (hk || jsonb_build_object('secteur_console_json',
           '{"TRANSPORT":{"value":"Tram"},"PROXIMITE":{"value":""},"ENVIRONNEMENT":{"value":"Calme, residentiel"},"immeuble":{"value":""}}'))::text
   where app_dossier_id = 10000006;
  select * into s from public.app_annonce_saisie_naissance where app_dossier_id = 10000006;
  select detail_payload_json::jsonb into d from public.app_dossier_detail_current where app_dossier_id = 10000006;
  insert into _m values
   (7, 'T3_verdict_secteur', (select string_agg(k || ':' || (s.verdict->k->>'etat'), ', ' order by k) from unnest(array['TRANSPORT','PROXIMITE','ENVIRONNEMENT']) k)),
   (8, 'T3_calque_secteur', coalesce(d->'app_optimistic_overlay'->>'TRANSPORT','NULL') || ' / ' || coalesce(d->'app_optimistic_overlay'->>'PROXIMITE','NULL') || ' / ' || coalesce(d->'app_optimistic_overlay'->>'ENVIRONNEMENT','NULL')),
   (9, 'T3_ecarts', s.ecarts::text);

  -- T4 UNE MODIFICATION DANS L'APP d'un champ console (diagnostiqueur), puis une relecture
  update public.app_dossier_detail_current
     set detail_payload_json = (d || jsonb_build_object('app_optimistic_overlay', coalesce(d->'app_optimistic_overlay','{}'::jsonb) || '{"diagnostiqueur":"Cabinet X"}'::jsonb))::text
   where app_dossier_id = 10000006;
  update public.app_dossier_detail_current
     set detail_payload_json = (hk || jsonb_build_object('secteur_console_json',
           '{"TRANSPORT":{"value":"Tram"},"PROXIMITE":{"value":""},"ENVIRONNEMENT":{"value":"Calme, residentiel"},"immeuble":{"value":""}}'))::text
   where app_dossier_id = 10000006;
  select * into s from public.app_annonce_saisie_naissance where app_dossier_id = 10000006;
  select detail_payload_json::jsonb into d from public.app_dossier_detail_current where app_dossier_id = 10000006;
  insert into _m values
   (10, 'T4_saisie_gardee_suit_la_modification', coalesce(s.calque->>'diagnostiqueur','NULL')),
   (11, 'T4_apres_relecture_le_calque_montre', coalesce(d->'app_optimistic_overlay'->>'diagnostiqueur','NULL'));

  -- T5 LA GARDE ANTI-MASQUAGE : le calque porte la valeur de Hektor (Tram) -> pas une saisie
  update public.app_dossier_detail_current set detail_payload_json = d::text where app_dossier_id = 10000006;
  select * into s from public.app_annonce_saisie_naissance where app_dossier_id = 10000006;
  insert into _m values (12, 'T5_TRANSPORT_reste_un_ecart', coalesce(s.verdict->'TRANSPORT'->>'etat','NULL') || ' / saisie=' || coalesce(s.calque->>'TRANSPORT','NULL'));

  -- T6 L'INTERRUPTEUR ETEINT : la relecture passe telle quelle, la saisie gardee ne bouge pas
  update public.app_setting set value = 'off' where key = 'annonce_saisie_gardee';
  t := (select maj_le::text from public.app_annonce_saisie_naissance where app_dossier_id = 10000006);
  update public.app_dossier_detail_current set detail_payload_json = hk::text where app_dossier_id = 10000006;
  select detail_payload_json::jsonb into d from public.app_dossier_detail_current where app_dossier_id = 10000006;
  insert into _m values (13, 'T6_eteint_fiche_telle_quelle_et_saisie_immobile',
     case when d = hk then 'fiche=oui' else 'fiche=NON' end || ' / ' ||
     case when (select maj_le::text from public.app_annonce_saisie_naissance where app_dossier_id = 10000006) is not distinct from t then 'saisie=oui' else 'saisie=NON' end);
  update public.app_setting set value = 'on' where key = 'annonce_saisie_gardee';

  -- T7 UNE AUTRE ANNONCE (sans saisie gardee) : intacte a l'octet
  select detail_payload_json into autre from public.app_dossier_detail_current where app_dossier_id = 10000001;
  update public.app_dossier_detail_current set refreshed_at = refreshed_at where app_dossier_id = 10000001;
  select detail_payload_json into autre2 from public.app_dossier_detail_current where app_dossier_id = 10000001;
  insert into _m values (14, 'T7_autre_annonce_intacte', case when autre is not distinct from autre2 then 'oui' else 'NON' end ||
     ' / sans saisie=' || case when exists (select 1 from public.app_annonce_saisie_naissance where app_dossier_id = 10000001) then 'NON' else 'oui' end);

  -- T8 UNE FICHE ILLISIBLE : le declencheur avale, l'ecriture passe
  begin
    update public.app_dossier_detail_current set detail_payload_json = 'pas du json' where app_dossier_id = 10000006;
    t8 := (select case when detail_payload_json = 'pas du json' then 'ecriture passee' else 'MODIFIEE' end from public.app_dossier_detail_current where app_dossier_id = 10000006);
  exception when others then
    t8 := 'BLOQUEE : ' || sqlerrm;
  end;
  insert into _m values (15, 'T8_fiche_illisible', t8);
  update public.app_dossier_detail_current set detail_payload_json = hk::text where app_dossier_id = 10000006;

  -- T9 UNE VRAIE CREATION (les deux interrupteurs allumes) : la saisie est gardee, avec son auteur
  select id into v_uid from public.app_user_profile
   where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1;
  perform set_config('request.jwt.claims', json_build_object('sub', v_uid::text, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_uid::text, true);
  begin
    v_job := public.app_create_annonce_job_optimistic(gen_random_uuid(),
               '{"titre_bien":"ESSAI 8A3","prix":"99000","ville":"Firminy","code_postal":"42700","statut_annonce":"Estimation"}'::jsonb,
               '{"title":"ESSAI 8A3","price":"99000","city":"Firminy","postal_code":"42700","hektor_id_type":"1","hektor_user_label":"Emmanuelle PEREIRA","agence_nom":"Groupe GTI Firminy","hektor_wizard_fields":{"TRANSPORT":"Gare a 5 min","NB_SDB":"1"},"initial_mandant":{"last_name":"NE PAS COPIER"}}'::jsonb, 18);
    v_id := (v_job.payload_json->>'app_dossier_id')::bigint;
    select * into s from public.app_annonce_saisie_naissance where app_dossier_id = v_id;
    t9 := case when s.app_dossier_id is null then 'PAS GARDEE'
               else 'gardee / TRANSPORT=' || coalesce(s.calque->>'TRANSPORT','NULL')
                    || ' / auteur=' || case when s.ecrit_par = v_uid then 'Frederic' else coalesce(s.ecrit_par::text,'NULL') end
                    || ' / mandant=' || case when s.saisie ? 'initial_mandant' then 'PRESENT' else 'absent' end end;
  exception when others then
    t9 := 'ERREUR : ' || sqlerrm;
  end;
  insert into _m values (16, 'T9_vraie_creation', t9);

  -- T10 D : la vue (une ligne par champ en ecart) et le marquage « vu » par un admin
  t10a := (select count(*) from public.app_v_annonce_naissance_ecarts where app_dossier_id = 10000006);
  t10c := (public.app_annonce_naissance_ecart_traiter(10000006))->>'marque';
  t10b := (select count(*) from public.app_annonce_saisie_naissance where ecarts > 0 and traite_le is null and app_dossier_id = 10000006);
  insert into _m values (17, 'T10_vue_lignes_en_ecart / marque / reste_a_signaler', t10a || ' / ' || t10c || ' / ' || t10b);
END
$essai$;

insert into _m values (18, 'droits_table_anon_authenticated',
  case when has_table_privilege('anon', 'public.app_annonce_saisie_naissance', 'SELECT') or has_table_privilege('authenticated', 'public.app_annonce_saisie_naissance', 'SELECT')
       or has_table_privilege('authenticated', 'public.app_v_annonce_naissance_ecarts', 'SELECT') then 'OUVERTS' else 'fermes' end);

-- ── LE VRAI RETOUR ARRIÈRE ──


drop trigger if exists app_annonce_saisie_naissance_trg on public.app_dossier_detail_current;
drop view if exists public.app_v_annonce_naissance_ecarts;
drop function if exists public.app_annonce_saisie_naissance_trg();
drop function if exists public.app_annonce_naissance_ecart_traiter(bigint);
drop function if exists public.app_annonce_verdict_naissance(jsonb, jsonb);
drop function if exists public.app_annonce_meme_valeur(text, text);
drop function if exists public.app_annonce_lecture_hektor(jsonb, text);
drop function if exists public.app_annonce_porteur_present(jsonb, text);
drop function if exists public.app_annonce_bloc(jsonb, text);
drop function if exists public.app_annonce_champs_console();

DO $garde_saisie$
DECLARE
    n int;
    nom text := 'app_annonce_saisie_naissance_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_annonce_saisie_naissance') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_annonce_saisie_naissance n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_annonce_saisie_naissance' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_annonce_saisie_naissance';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_annonce_saisie_naissance rename to %I', nom);
        RAISE NOTICE '%', format('%s saisie(s) gardee(s) sous public.%s', n, nom);
    END IF;
END
$garde_saisie$;

delete from public.app_setting where key = 'annonce_saisie_gardee';


insert into _m values
 (19, 'retour_declencheur_fonctions_interrupteur',
   case when not exists (select 1 from pg_trigger where tgrelid = 'public.app_dossier_detail_current'::regclass and not tgisinternal)
         and to_regprocedure('public.app_annonce_lecture_hektor(jsonb,text)') is null
         and not exists (select 1 from public.app_setting where key = 'annonce_saisie_gardee') then 'retires' else 'RESTES' end),
 (20, 'retour_saisies_non_perdues', coalesce((select relname from pg_class where relname like 'app_annonce_saisie_naissance_avant_inverse_%' limit 1), 'AUCUNE COPIE')),
 (21, 'creation_et_naissance_non_retouchees',
   case when md5(replace(pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure), chr(13), '')) = 'a5e70b5734876f74ecd0083681a1ebe8'
         and md5(replace(pg_get_functiondef('public.app_annonce_corps_de_naissance(jsonb)'::regprocedure), chr(13), '')) = '944db16babc10031b567eb535f74be8b' then 'oui' else 'NON' end);

DO $fin$
BEGIN
  RAISE EXCEPTION '%', (select 'ESSAI ANNULE -- ' || string_agg(lpad(n::text, 2, '0') || ' ' || cle || '=' || coalesce(valeur, 'NULL'), ' | ' order by n) from _m);
END
$fin$;

ROLLBACK;
