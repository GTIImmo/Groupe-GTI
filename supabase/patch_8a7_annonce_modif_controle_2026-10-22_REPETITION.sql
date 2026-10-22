-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a-C — le contrôle au retour d'une modification d'annonce — TOUT EST ANNULÉ
--                                                                    22/10/2026
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … ». Elle pose LE VRAI PATCH, joue 14 essais
-- sur la VRAIE fiche de l'annonce d'essai 10000009 / 63331 (faux travaux, fausses relectures),
-- puis LE VRAI RETOUR ARRIÈRE. Rien ne reste.
-- Fichier GÉNÉRÉ (phase2/checks/gen_patch_8a7_annonce_modif_controle.py).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

DO $garde$
BEGIN
    IF to_regclass('public.app_annonce_saisie_modif') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la table app_annonce_saisie_modif existe deja. Rien n''est ecrit.';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname IN ('app_annonce_saisie_modif_job_trg', 'app_annonce_saisie_modif_juge_trg')) THEN
        RAISE EXCEPTION '%', 'ARRET : un des declencheurs existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regprocedure('public.app_annonce_verdict_naissance(jsonb,jsonb)') IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la piece 3 (app_annonce_verdict_naissance) n''est pas posee. Rien n''est ecrit.';
    END IF;
END
$garde$;

-- 0. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('annonce_retour_controle', 'off',
        'Chantier 8 / 8a-C 22/10/2026 : on = ce qui part chez Hektor quand on modifie une annonce est garde, puis compare a ce que Hektor rend (voir supabase/patch_8a7_annonce_modif_controle_2026-10-22.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- GARDER : la table à part
create table public.app_annonce_saisie_modif (
  job_id            uuid primary key,              -- le travail qui a porte la modification chez Hektor
  app_dossier_id    bigint not null,
  hektor_annonce_id text,
  saisie            jsonb not null,                -- nom Hektor -> valeur partie chez Hektor
  envoye_le         timestamptz not null,          -- debut du travail : AVANT l'ecriture chez Hektor
  ecrit_par         uuid,
  etat              text not null default 'attente' check (etat in ('attente', 'juge', 'remplacee')),
  verdict           jsonb,                         -- { nom: { envoye, relu, etat } }
  verdict_le        timestamptz,
  ecarts            integer,                       -- remplace + absent
  console_seule     integer,                       -- en attente du bloc console
  traite_le         timestamptz,
  traite_par        uuid,
  cree_le           timestamptz not null default now()
);
create index app_annonce_saisie_modif_ouvert on public.app_annonce_saisie_modif (app_dossier_id)
  where etat = 'attente' or (etat = 'juge' and console_seule > 0);
comment on table public.app_annonce_saisie_modif is
  'Chantier 8 / 8a-C (22/10/2026) : ce qui est parti chez Hektor a chaque modification d''annonce reussie, et son verdict au retour. Ecrite uniquement par les declencheurs app_annonce_saisie_modif_*.';
alter table public.app_annonce_saisie_modif enable row level security;
revoke all on public.app_annonce_saisie_modif from public, anon, authenticated;
grant select, insert, update, delete on public.app_annonce_saisie_modif to service_role;

-- La charge d'un travail -> le calque aux noms Hektor (seulement les noms que l'on sait LIRE)
create or replace function public.app_annonce_calque_modif(p jsonb)
 returns jsonb
 language plpgsql
 immutable
as $f$
declare
  noms constant text[] := array['codepublique', 'villepublique', 'ADRESSE_COMPL', 'adresse', 'immeuble', 'TRANSPORT', 'PROXIMITE', 'ENVIRONNEMENT', 'latitude', 'longitude', 'surfappart', 'nbpieces', 'NB_CHAMBRES', 'NB_SDB', 'SDB', 'NB_SE', 'SE', 'SDE', 'NB_WC', 'WC', 'SURF_CARREZ', 'SURF_SEJOUR', 'CUISINE', 'CUISINE_EQUIPEMENT', 'EXPOSITION', 'vuee', 'JARDIN', 'JARDIN-', 'SURFACE_JARDIN', 'MURS_MITOYENS', 'floorState', 'NB_NIVEAUX', 'ETAGE', 'DERNIER_ETAGE', 'NB_ETAGES', 'CAVE', 'SURFACE_CAVE', 'BALCON', 'NB_BALCON', 'SURFACE_BALCON', 'TERRASSE', 'NB_TERRASSE', 'SURFACE_TERRASSE', 'GARAGE_BOX', 'SURFACE_GARAGE', 'NB_PARK_INT', 'NB_PARK_EXT', 'PISCINE', 'PISCINE-', 'PISCINE_TYPE', 'PISCINE_NATURE', 'PISCINE_DETAILS', 'PISCINE_DIMENSIONS', 'PISCINE_TRAITEMENT', 'POOL_HOUSE', 'PISCINE_CHAUFFEE', 'PISCINE_COUVERTE', 'RESIDENCE', 'TYPE_RESIDENCE', 'surfterrain', 'terrain_constructible', 'terrain_surface_constructible', 'SHON', 'terrain_viabilise', 'terrain_raccordement_eau', 'terrain_raccordement_gaz', 'terrain_raccordement_electricite', 'terrain_raccordement_telephone', 'terrain_arbore', 'terrain_piscinable', 'ASCENSEUR', 'ACCES_HANDI', 'climatisation', 'climatisationspec', 'EAU', 'ASSAINISSEMENT', 'DISTRIBUTION_EAU', 'ENERGIE_EAU', 'cheminee', 'volets_elctriques', 'gardien', 'double_vitrage', 'triple_vitrage', 'cable', 'porte_blindee', 'interphone', 'visiophone', 'alarme', 'digicode', 'detecteur_fumee', 'ANNEE_CONS', 'ANNEE_CONSTRUCTION', 'etat_exterieur', 'ETAT_EXTERIEUR', 'etat_interieur', 'ETAT_INTERIEUR', 'dpe_date', 'dpe_non_concerne', 'dpe_vierge', 'isDpeAltitude', 'dpe_cons', 'DPE', 'dpe_ges', 'GES', 'valeurEnergieFinale', 'dpe_couts_min', 'dpe_couts_max', 'dpe_annee_reference', 'diagnostiqueur', 'syndic', 'diag_termites', 'diag_termites_date', 'diag_termites_commentaire', 'diag_amiante', 'diag_amiante_date', 'diag_amiante_commentaire', 'diag_electrique', 'diag_electrique_date', 'diag_electrique_commentaire', 'diag_loi_carrez', 'diag_loi_carrez_date', 'diag_loi_carrez_commentaire', 'diag_risques_nat_tech', 'diag_risques_nat_tech_date', 'diag_risques_nat_tech_commentaire', 'diag_plomb', 'diag_plomb_date', 'diag_plomb_commentaire', 'diag_gaz', 'diag_gaz_date', 'diag_gaz_commentaire', 'diag_assainissement', 'diag_assainissement_date', 'diag_assainissement_commentaire', 'copropriete', 'copropriete_lot', 'copropriete_nb_lot', 'copropriete_quote_part', 'montant_fonds_travaux', 'copropriete_plan_sauvegarde', 'copropriete_statut_syndicat', 'garantie_decennale', 'assurance_dommages_ouvrage', 'certificat_conformite', 'declaration_achevement_travaux', 'CLES', 'moyens_visite', 'prix', 'PRIXNETVENDEUR', '_selecterHonoraires2', '_tauxHonoraire2', '_pourcentHonoraire2', '_detailHonoraire2', '_selecterHonoraires3', '_tauxHonoraire3', '_pourcentHonoraire3', '_detailHonoraire3', 'masque', 'ESTIMATION_MONTANT', 'ESTIMATION_DATE', 'TRAVAUX', 'DEPOT_GARANTIE', 'TAXE_HABITATION', 'TAXE_FONCIERE', 'CHARGES', 'CHARGES_DETAIL', 'Loc_EstimationLoyer', 'Loc_ChargeLocative', 'Loc_RendementBrut', 'Loc_Occupation', 'NO_DOSSIER', 'dateenr', 'DISPO', 'DATE_LIBER', 'DATE_DISPO', 'titre', 'corps', 'formatChauff', 'typeChauff', 'energieChauff']::text[];
  correspondance constant jsonb := '{"prix": ["price"], "PRIXNETVENDEUR": ["net_seller_price"], "surfappart": ["surface"], "surfterrain": ["land_surface"], "SURFACE_GARAGE": ["garage_surface"], "nbpieces": ["room_count"], "NB_CHAMBRES": ["bedroom_count"], "NB_NIVEAUX": ["level_count"], "GARAGE_BOX": ["garage_count"], "JARDIN-": ["garden"], "PISCINE-": ["pool"], "EXPOSITION": ["exposure"], "vuee": ["view"], "NB_SDB": ["bathroom_count"], "NB_SE": ["shower_room_count"], "NB_WC": ["wc_count"], "SURF_CARREZ": ["carrez_surface"], "SURF_SEJOUR": ["living_surface"], "CUISINE": ["kitchen"], "etat_interieur": ["interior_state"], "etat_exterieur": ["exterior_state"], "NB_TERRASSE": ["terrace_count"], "NB_PARK_INT": ["parking_inside_count"], "NB_PARK_EXT": ["parking_outside_count"], "ANNEE_CONS": ["construction_year"], "dpe_cons": ["dpe_value"], "dpe_ges": ["ges_value"], "copropriete_nb_lot": ["copro_lots"], "copropriete_quote_part": ["copro_quote_part"], "montant_fonds_travaux": ["copro_works_fund"], "CHARGES": ["copro_charges"], "titre": ["title"], "corps": ["description"], "adresse": ["address"], "codeprive": ["postal_code"], "codepublique": ["postal_code"], "villeprivee": ["city"], "villepublique": ["city"], "immeuble": ["building"], "TRANSPORT": ["transport"], "PROXIMITE": ["proximity"], "ENVIRONNEMENT": ["environment"], "ETAGE": ["floor"], "TERRASSE": ["terrace"]}';
  out jsonb := '{}'::jsonb;
  k   text;
  a   text;
  v   text;
begin
  if jsonb_typeof(p) <> 'object' then return out; end if;
  -- 1. les cles « a plat », vers leur nom Hektor (premiere non vide)
  for k in select jsonb_object_keys(correspondance) loop
    v := null;
    for a in select jsonb_array_elements_text(correspondance->k) loop
      if jsonb_typeof(p->a) in ('string', 'number') then v := nullif(trim(p->>a), ''); end if;
      exit when v is not null;
    end loop;
    if v is not null then out := out || jsonb_build_object(k, v); end if;
  end loop;
  -- 2. les noms Hektor envoyes tels quels (charge, puis boite hektor_wizard_fields) : ils GAGNENT
  foreach k in array noms loop
    if jsonb_typeof(p->k) in ('string', 'number') and nullif(trim(p->>k), '') is not null then
      out := out || jsonb_build_object(k, trim(p->>k));
    end if;
    if jsonb_typeof(p->'hektor_wizard_fields'->k) in ('string', 'number') and nullif(trim(p->'hektor_wizard_fields'->>k), '') is not null then
      out := out || jsonb_build_object(k, trim(p->'hektor_wizard_fields'->>k));
    end if;
  end loop;
  return out;
end
$f$;

-- GARDER : quand un travail de modification d'annonce passe a « done » avec « updated »
create or replace function public.app_annonce_saisie_modif_job_trg()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_on   boolean;
  d_id   bigint;
  calque jsonb;
  avant  jsonb;
begin
  select lower(trim(coalesce(st.value, ''))) in ('on', '1', 'true', 'oui') into v_on
    from public.app_setting st where st.key = 'annonce_retour_controle';
  if not coalesce(v_on, false) then return null; end if;
  begin
    if coalesce(new.result_json->>'status', '') <> 'updated' then return null; end if;  -- held_conflict, etc.
    d_id := coalesce(new.app_dossier_id, nullif(new.payload_json->>'app_dossier_id', '')::bigint);
    if d_id is null then return null; end if;
    calque := public.app_annonce_calque_modif(new.payload_json);
    if calque = '{}'::jsonb then return null; end if;
    -- une saisie encore en attente : la nouvelle la COMPLETE, l'ancienne est « remplacee »
    select coalesce(jsonb_object_agg(e.key, e.value), '{}'::jsonb) into avant
      from public.app_annonce_saisie_modif s, jsonb_each(s.saisie) e
     where s.app_dossier_id = d_id and s.etat = 'attente';
    update public.app_annonce_saisie_modif set etat = 'remplacee'
     where app_dossier_id = d_id and etat = 'attente';
    insert into public.app_annonce_saisie_modif (job_id, app_dossier_id, hektor_annonce_id, saisie, envoye_le, ecrit_par)
    values (new.id, d_id, coalesce(new.hektor_annonce_id, new.payload_json->>'hektor_annonce_id'), avant || calque,
            coalesce(new.started_at, new.created_at), new.requested_by)
    on conflict (job_id) do nothing;
  exception when others then
    raise warning 'annonce_retour_controle : saisie non gardee pour le travail % (%)', new.id, sqlerrm;
  end;
  return null;
end
$f$;

create trigger app_annonce_saisie_modif_job_trg
  after update on public.app_console_job
  for each row
  when (new.status = 'done' and old.status is distinct from 'done' and new.job_type = 'update_hektor_annonce_fields')
  execute function public.app_annonce_saisie_modif_job_trg();

-- CONTRÔLER : a une ecriture de la fiche qui vient de HEKTOR et dont la date suit l'envoi
create or replace function public.app_annonce_saisie_modif_juge_trg()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_on boolean;
  s    record;
  j    jsonb;
  v    jsonb;
  k    text;
  rej  boolean;
begin
  select lower(trim(coalesce(st.value, ''))) in ('on', '1', 'true', 'oui') into v_on
    from public.app_setting st where st.key = 'annonce_retour_controle';
  if not coalesce(v_on, false) then return null; end if;
  -- une naissance (piece 2) n'est pas un retour de Hektor ; un calque repose (L3, l'ecran)
  -- ne change pas le source_hash : seule une fiche NEUVE de Hektor juge.
  if coalesce(new.source_hash, '') like 'c9e3:%' then return null; end if;
  if tg_op = 'UPDATE' and new.source_hash is not distinct from old.source_hash then return null; end if;
  begin
    for s in select * from public.app_annonce_saisie_modif
              where app_dossier_id = new.app_dossier_id
                and (etat = 'attente' or (etat = 'juge' and console_seule > 0)) loop
      if j is null then j := new.detail_payload_json::jsonb; end if;
      if s.etat = 'attente' then
        -- l'ANCIEN Hektor (date d'avant l'envoi) ne juge rien. 2 min de marge, heure de Paris.
        if coalesce(j->>'date_maj', '') < to_char((s.envoye_le - interval '2 minutes') at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS') then
          continue;
        end if;
        v := public.app_annonce_verdict_naissance(s.saisie, j);
      else
        -- les « console seule » : rejuges quand leur bloc est arrive
        v := s.verdict;
        rej := false;
        for k in select e.key from jsonb_each(s.verdict) e where e.value->>'etat' = 'console_seule' loop
          if public.app_annonce_porteur_present(j, k) then
            v := v || public.app_annonce_verdict_naissance(jsonb_build_object(k, s.saisie->>k), j);
            rej := true;
          end if;
        end loop;
        if not rej then continue; end if;
      end if;
      update public.app_annonce_saisie_modif set
        etat          = 'juge',
        verdict       = v,
        verdict_le    = coalesce(verdict_le, now()),
        ecarts        = (select count(*) from jsonb_each(v) e where e.value->>'etat' in ('remplace', 'absent')),
        console_seule = (select count(*) from jsonb_each(v) e where e.value->>'etat' = 'console_seule')
       where job_id = s.job_id;
    end loop;
  exception when others then
    raise warning 'annonce_retour_controle : verdict ignore pour % (%)', new.app_dossier_id, sqlerrm;
  end;
  return null;
end
$f$;

create trigger app_annonce_saisie_modif_juge_trg
  after insert or update on public.app_dossier_detail_current
  for each row execute function public.app_annonce_saisie_modif_juge_trg();

-- SIGNALER : une ligne par annonce ET par champ en ecart -- jamais « N sur M »
create view public.app_v_annonce_modif_ecarts
  with (security_invoker = true) as
select s.job_id, s.app_dossier_id, s.hektor_annonce_id, d.titre_bien, d.ville, d.commercial_nom,
       e.key as champ, e.value->>'envoye' as envoye, e.value->>'relu' as relu, e.value->>'etat' as etat,
       s.envoye_le, s.verdict_le, s.traite_le
  from public.app_annonce_saisie_modif s
  cross join lateral jsonb_each(coalesce(s.verdict, '{}'::jsonb)) e
  left join public.app_dossier_current d on d.app_dossier_id = s.app_dossier_id
 where s.etat = 'juge' and e.value->>'etat' in ('remplace', 'absent')
union all
select s.job_id, s.app_dossier_id, s.hektor_annonce_id, d.titre_bien, d.ville, d.commercial_nom,
       null, null, null, 'non_relu', s.envoye_le, s.verdict_le, s.traite_le
  from public.app_annonce_saisie_modif s
  left join public.app_dossier_current d on d.app_dossier_id = s.app_dossier_id
 where s.etat = 'attente' and s.envoye_le < now() - interval '24 hours';
revoke all on public.app_v_annonce_modif_ecarts from public, anon, authenticated;
grant select on public.app_v_annonce_modif_ecarts to service_role;

create or replace function public.app_annonce_modif_ecart_traiter(p_job_id uuid)
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
  update public.app_annonce_saisie_modif
     set traite_le = now(), traite_par = auth.uid()
   where job_id = p_job_id and traite_le is null;
  get diagnostics n = row_count;
  return jsonb_build_object('job_id', p_job_id, 'marque', n);
end
$f$;

revoke all on function public.app_annonce_calque_modif(jsonb) from public, anon, authenticated;
revoke all on function public.app_annonce_saisie_modif_job_trg() from public, anon, authenticated;
revoke all on function public.app_annonce_saisie_modif_juge_trg() from public, anon, authenticated;
revoke all on function public.app_annonce_modif_ecart_traiter(uuid) from public, anon;
grant execute on function public.app_annonce_modif_ecart_traiter(uuid) to authenticated;

DO $essai$
DECLARE
    did  bigint := 10000009;
    j0   jsonb;
    jn   jsonb;
    j1 uuid; j2 uuid; j3 uuid; j4 uuid; j5 uuid;
    n int;
    v jsonb;
    paris text;
    t text;
BEGIN
    select detail_payload_json::jsonb into j0 from public.app_dossier_detail_current where app_dossier_id = did;
    IF j0 IS NULL OR public.app_annonce_lecture_hektor(j0, 'copropriete') IS DISTINCT FROM 'OUI'
       OR NOT public.app_annonce_porteur_present(j0, 'TRANSPORT') THEN
        RAISE EXCEPTION '%', 'ARRET : la fiche d''essai 10000009 n''a pas la forme attendue (copropriete OUI, bloc secteur) -- la repetition ne prouverait rien.';
    END IF;
    paris := to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS');

    -- (1) ETEINT : un travail reussi ne garde rien (temoin inverse)
    update public.app_setting set value = 'off' where key = 'annonce_retour_controle';
    insert into public.app_console_job (job_type, status, app_dossier_id, hektor_annonce_id, payload_json, started_at)
    values ('update_hektor_annonce_fields', 'running', did, '63331', jsonb_build_object('app_dossier_id', did, 'immeuble', 'X'), now())
    returning id into j1;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j1;
    select count(*) into n from public.app_annonce_saisie_modif;
    insert into _m values (1, 'eteint : aucune saisie gardee', case when n = 0 then 'OK' else 'ECHEC ' || n end);
    update public.app_setting set value = 'on' where key = 'annonce_retour_controle';

    -- (2) held_conflict : rien
    insert into public.app_console_job (job_type, status, app_dossier_id, hektor_annonce_id, payload_json, started_at)
    values ('update_hektor_annonce_fields', 'running', did, '63331', jsonb_build_object('app_dossier_id', did, 'immeuble', 'X'), now())
    returning id into j2;
    update public.app_console_job set status = 'done', result_json = '{"status":"held_conflict"}'::jsonb, finished_at = now() where id = j2;
    select count(*) into n from public.app_annonce_saisie_modif;
    insert into _m values (2, 'un conflit retenu ne garde rien', case when n = 0 then 'OK' else 'ECHEC ' || n end);

    -- (3) reussi : le calque aux noms Hektor -- a plat traduit, Hektor tel quel, la boite, l'inconnu et le technique ecartes
    insert into public.app_console_job (job_type, status, app_dossier_id, hektor_annonce_id, payload_json, started_at)
    values ('update_hektor_annonce_fields', 'running', did, '63331',
            jsonb_build_object('app_dossier_id', did, 'hektor_annonce_id', '63331', 'from_pending', true, 'source', 'nego_app',
                               'base_snapshot', jsonb_build_object('_date_maj', '2026-10-22 12:02:11'),
                               'address', '8 Rue de l''Ondaine', 'floor', '2', 'copropriete', 'NON', 'immeuble', 'Residence Les Tilleuls',
                               'TRANSPORT', 'Gare SNCF a 400 m', 'champ_inconnu', 'Z',
                               'hektor_wizard_fields', jsonb_build_object('copropriete_nb_lot', '24')),
            now() - interval '10 seconds')
    returning id into j3;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j3;
    select saisie into v from public.app_annonce_saisie_modif where job_id = j3 and etat = 'attente';
    insert into _m values (3, 'reussi : calque aux noms Hektor (adresse, ETAGE, copropriete, immeuble, TRANSPORT, copropriete_nb_lot), sans inconnu ni technique',
        case when v->>'adresse' = '8 Rue de l''Ondaine' and v->>'ETAGE' = '2' and v->>'copropriete' = 'NON' and v->>'immeuble' = 'Residence Les Tilleuls'
                  and v->>'TRANSPORT' = 'Gare SNCF a 400 m' and v->>'copropriete_nb_lot' = '24'
                  and not v ? 'champ_inconnu' and not v ? 'base_snapshot' and not v ? 'from_pending' and not v ? 'source' and not v ? 'app_dossier_id'
                  and (select count(*) from jsonb_object_keys(v)) = 6
             then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (4) un calque repose par l'ecran ou L3 (source_hash INCHANGE) ne juge rien
    update public.app_dossier_detail_current set detail_payload_json = (j0 || jsonb_build_object('date_maj', paris))::text where app_dossier_id = did;
    select count(*) into n from public.app_annonce_saisie_modif where etat = 'juge';
    insert into _m values (4, 'une ecriture sans fiche neuve de Hektor (source_hash inchange) ne juge rien', case when n = 0 then 'OK' else 'ECHEC ' || n end);

    -- (5) une fiche de Hektor ANCIENNE (date d'avant l'envoi) ne juge rien
    update public.app_dossier_detail_current set source_hash = 'essai-8a7-ancien', detail_payload_json = (j0 || jsonb_build_object('date_maj', '2026-10-22 08:00:00'))::text where app_dossier_id = did;
    select count(*) into n from public.app_annonce_saisie_modif where etat = 'juge';
    insert into _m values (5, 'une fiche de Hektor plus ancienne que l''envoi ne juge rien', case when n = 0 then 'OK' else 'ECHEC ' || n end);

    -- (6) LE RETOUR, SANS le bloc secteur : copropriete remplace (Hektor dit OUI), TRANSPORT console_seule
    jn := (j0 - 'secteur_console_json') || jsonb_build_object('date_maj', paris);
    update public.app_dossier_detail_current set source_hash = 'essai-8a7-retour', detail_payload_json = jn::text where app_dossier_id = did;
    select verdict into v from public.app_annonce_saisie_modif where job_id = j3 and etat = 'juge';
    insert into _m values (6, 'le retour est juge : copropriete remplace, adresse et ETAGE identiques, immeuble et TRANSPORT console_seule',
        case when v->'copropriete'->>'etat' = 'remplace' and v->'copropriete'->>'relu' = 'OUI'
                  and v->'adresse'->>'etat' in ('identique', 'autre_forme') and v->'ETAGE'->>'etat' = 'identique'
                  and v->'TRANSPORT'->>'etat' = 'console_seule' and v->'immeuble'->>'etat' = 'console_seule'
                  and (select console_seule from public.app_annonce_saisie_modif where job_id = j3) = 2
             then 'OK' else 'ECHEC ' || coalesce(v::text, 'pas juge') end);

    -- (7) LE BLOC CONSOLE ARRIVE : les « console seule » sont rejuges, le reste n'est pas touche
    update public.app_dossier_detail_current set source_hash = 'essai-8a7-console', detail_payload_json = (j0 || jsonb_build_object('date_maj', paris))::text where app_dossier_id = did;
    select verdict into v from public.app_annonce_saisie_modif where job_id = j3;
    insert into _m values (7, 'le bloc console arrive : TRANSPORT et immeuble rejuges identiques, copropriete reste remplace',
        case when v->'TRANSPORT'->>'etat' = 'identique' and v->'immeuble'->>'etat' = 'identique' and v->'copropriete'->>'etat' = 'remplace'
                  and (select console_seule from public.app_annonce_saisie_modif where job_id = j3) = 0
             then 'OK' else 'ECHEC ' || coalesce(v::text, '') end);

    -- (8) la vue : une ligne par champ en ecart
    select count(*), string_agg(champ || '=' || etat, ',') into n, t from public.app_v_annonce_modif_ecarts where job_id = j3;
    insert into _m values (8, 'la vue : une ligne par champ en ecart (copropriete)', case when n = 1 and t = 'copropriete=remplace' then 'OK' else 'ECHEC ' || n || ' ' || coalesce(t, '') end);

    -- (9) deux envois avant le retour : le second COMPLETE le premier, qui est « remplace »
    insert into public.app_console_job (job_type, status, app_dossier_id, hektor_annonce_id, payload_json, started_at)
    values ('update_hektor_annonce_fields', 'running', did, '63331', jsonb_build_object('app_dossier_id', did, 'prix', '139000'), now())
    returning id into j4;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j4;
    insert into public.app_console_job (job_type, status, app_dossier_id, hektor_annonce_id, payload_json, started_at)
    values ('update_hektor_annonce_fields', 'running', did, '63331', jsonb_build_object('app_dossier_id', did, 'surface', '68'), now())
    returning id into j5;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j5;
    select saisie into v from public.app_annonce_saisie_modif where job_id = j5;
    insert into _m values (9, 'deux envois avant le retour : le second complete le premier (prix + surfappart)',
        case when v->>'prix' = '139000' and v->>'surfappart' = '68'
                  and (select etat from public.app_annonce_saisie_modif where job_id = j4) = 'remplacee' then 'OK' else 'ECHEC ' || coalesce(v::text, '') end);

    -- (10) une NAISSANCE (c9e3) ne juge rien
    update public.app_dossier_detail_current set source_hash = 'c9e3:essai', detail_payload_json = (j0 || jsonb_build_object('date_maj', paris))::text where app_dossier_id = did;
    select etat into t from public.app_annonce_saisie_modif where job_id = j5;
    insert into _m values (10, 'une fiche de naissance (c9e3) ne juge rien', case when t = 'attente' then 'OK' else 'ECHEC ' || coalesce(t, '') end);

    -- (11) une fiche ILLISIBLE ne bloque pas l'ecriture
    update public.app_dossier_detail_current set source_hash = 'essai-8a7-illisible', detail_payload_json = 'pas du json' where app_dossier_id = did;
    get diagnostics n = row_count;
    insert into _m values (11, 'une fiche illisible ne bloque PAS l''ecriture (warning seulement)', case when n = 1 then 'OK' else 'ECHEC ' || n end);

    -- (12) une autre annonce, sans saisie : rien
    update public.app_dossier_detail_current set source_hash = source_hash || '' where app_dossier_id = (select app_dossier_id from public.app_dossier_detail_current where app_dossier_id <> did limit 1);
    get diagnostics n = row_count;
    insert into _m values (12, 'une autre annonce : l''ecriture passe', case when n = 1 then 'OK' else 'ECHEC ' || n end);

    -- (13) « non_relu » apres 24 h
    update public.app_annonce_saisie_modif set envoye_le = now() - interval '30 hours' where job_id = j5;
    select count(*) into n from public.app_v_annonce_modif_ecarts where job_id = j5 and etat = 'non_relu';
    insert into _m values (13, 'rien n''est revenu en 24 h : une ligne « non_relu »', case when n = 1 then 'OK' else 'ECHEC ' || n end);

    -- (14) un travail d'un autre type (contact) ne garde rien ici
    select count(*) into n from public.app_annonce_saisie_modif;
    insert into public.app_console_job (job_type, status, app_dossier_id, payload_json, started_at)
    values ('update_hektor_contact', 'running', did, jsonb_build_object('app_dossier_id', did, 'immeuble', 'Y'), now())
    returning id into j1;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j1;
    insert into _m values (14, 'un travail de contact ne garde rien ici', case when (select count(*) from public.app_annonce_saisie_modif) = n then 'OK' else 'ECHEC' end);
END
$essai$;

drop trigger if exists app_annonce_saisie_modif_job_trg on public.app_console_job;
drop trigger if exists app_annonce_saisie_modif_juge_trg on public.app_dossier_detail_current;
drop view if exists public.app_v_annonce_modif_ecarts;
drop function if exists public.app_annonce_saisie_modif_job_trg();
drop function if exists public.app_annonce_saisie_modif_juge_trg();
drop function if exists public.app_annonce_modif_ecart_traiter(uuid);
drop function if exists public.app_annonce_calque_modif(jsonb);

DO $garde_saisie$
DECLARE
    n int;
    nom text := 'app_annonce_saisie_modif_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_annonce_saisie_modif') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_annonce_saisie_modif n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_annonce_saisie_modif' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_annonce_saisie_modif';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_annonce_saisie_modif rename to %I', nom);
        RAISE NOTICE '%', format('%s saisie(s) gardee(s) sous public.%s', n, nom);
    END IF;
END
$garde_saisie$;

delete from public.app_setting where key = 'annonce_retour_controle';

DO $fin$
DECLARE
    r text;
    ok int;
    total int;
BEGIN
    insert into _m values (15, 'le retour arriere a tout retire, la piece 3 intacte',
        case when to_regclass('public.app_annonce_saisie_modif') IS NULL
                  AND to_regclass('public.app_v_annonce_modif_ecarts') IS NULL
                  AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname IN ('app_annonce_saisie_modif_job_trg', 'app_annonce_saisie_modif_juge_trg'))
                  AND NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'annonce_retour_controle')
                  AND EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'app_annonce_saisie_naissance_trg')
             then 'OK' else 'ECHEC' end);
    select count(*) filter (where valeur = 'OK'), count(*), string_agg(n || ' ' || valeur || ' ' || cle, ' | ' order by n)
      into ok, total, r from _m;
    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s | %s', ok, total, r);
END
$fin$;
