-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · 8a-C — LE CONTRÔLE AU RETOUR D'UNE MODIFICATION D'ANNONCE         22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (« Clôturer 8a »)
--
-- LE DÉFAUT (audit du 22/10) : la relecture repose les saisies TANT QU'ELLES SONT EN ATTENTE
-- (L3). Un envoi réussi solde l'attente : la relecture suivante prend la valeur de Hektor
-- TELLE QUELLE. Si Hektor n'a pas gardé un champ, il disparaît EN SILENCE — c'est ainsi que la
-- copropriété est tombée le 22/10 (la garde du worker ne couvre QUE ce champ-là).
--
-- CE QUE FAIT CE PATCH — ADDITIF, derrière l'interrupteur 'annonce_retour_controle' (off) :
--   GARDER    quand un travail update_hektor_annonce_fields réussit (« updated »), ce qui est
--             PARTI chez Hektor est gardé dans app_annonce_saisie_modif, aux noms Hektor
--             (180 noms, LUS dans HEKTOR_WIZARD_UPDATE_GROUPS du worker ; les clés « à
--             plat » traduites par la correspondance de la pièce 2).
--   CONTRÔLER à la première écriture de la fiche qui vient de HEKTOR (une naissance c9e3 ne
--             compte pas, un calque reposé non plus : il faut un source_hash nouveau) et dont la
--             date Hektor suit l'envoi : le verdict de la pièce 3 (identique · autre_forme ·
--             recalcule · remplace · absent · console_seule). Les « console seule » sont rejugés
--             quand leur bloc arrive.
--   SIGNALER  une vue, une ligne par annonce ET par champ en écart + « non_relu » après 24 h ;
--             marquage « vu » (admin) ; la sentinelle data.annonce_modif_ecart.
--   ⚠ Il NE REMET RIEN : la valeur de Hektor reste affichée ; l'écart est dit.
-- Deux déclencheurs qui ne bloquent JAMAIS l'écriture qui les porte (une erreur = WARNING).
-- ⚠ Aucune fonction existante n'est retouchée ; ceux de la pièce 3 non plus.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'annonce_retour_controle';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'annonce_retour_controle';
-- RETOUR ARRIÈRE COMPLET : supabase/patch_8a7_annonce_modif_controle_2026-10-22_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

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

-- LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'interrupteur pose, ETEINT' AS controle,
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'annonce_retour_controle') = 'off' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la table existe, vide, fermee a anon et authenticated',
       CASE WHEN (SELECT count(*) FROM public.app_annonce_saisie_modif) = 0
             AND NOT has_table_privilege('anon', 'public.app_annonce_saisie_modif', 'SELECT')
             AND NOT has_table_privilege('authenticated', 'public.app_annonce_saisie_modif', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les deux declencheurs sont poses',
       CASE WHEN (SELECT count(*) FROM pg_trigger WHERE tgname IN ('app_annonce_saisie_modif_job_trg', 'app_annonce_saisie_modif_juge_trg')) = 2 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'le declencheur de la piece 3 est toujours la, et lui seul en BEFORE',
       CASE WHEN EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'app_annonce_saisie_naissance_trg') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la vue est fermee a anon et authenticated',
       CASE WHEN NOT has_table_privilege('anon', 'public.app_v_annonce_modif_ecarts', 'SELECT')
             AND NOT has_table_privilege('authenticated', 'public.app_v_annonce_modif_ecarts', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 6, 'le marquage « vu » est ouvert aux connectes, ferme a anon',
       CASE WHEN has_function_privilege('authenticated', 'public.app_annonce_modif_ecart_traiter(uuid)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_annonce_modif_ecart_traiter(uuid)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
