-- ═══════════════════════════════════════════════════════════════════════════
-- RECRUTEMENT — R6 : CE QUE L'ÉCRAN ÉCRIT ET LIT                                             24/11/2026
-- Chantier à part : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md, §14 (R6, sa conception
-- écrite avant de coder) ; maquettes validées : notice/maquettes_recrutement/.
-- Suppose R3 posé (patch_recrutement_schema_2026-11-24.sql). Répétition : _REPETITION.sql ; retour : _INVERSE.sql.
--
-- CE QUE POSE CE PATCH (et rien d'autre) :
--   1. 4 tables dans le schéma « recrutement » :
--        agence_gti  nos 17 agences et leur position (envoyées par la montée)
--        suivi       le parcours d'une fiche (6 étapes), son statut, sa prochaine action, qui la suit
--        evenement   le fil des échanges (appel, note, e-mail, rendez-vous, étape, correction...)
--        retrait     ce qui RESTE d'une personne qui ne veut plus être contactée (nom, SIREN, date) ;
--                    une personne EFFACÉE ne laisse aucune ligne lisible, seulement ses empreintes
--   2. la clé de nom et les empreintes, IDENTIQUES à celles du collecteur Python (vérifié le 24/11 sur
--      12 noms pièges et sur les 4 natures d'empreinte) : une personne retirée dans l'app ne revient
--      jamais à la collecte ;
--   3. les fonctions de l'écran, public.rec_*, ADMINISTRATEURS SEULEMENT (is_app_admin, sinon 42501).
-- ⛔ RIEN N'EST ÉCRIT CHEZ HEKTOR. Aucune table hors du schéma « recrutement » n'est touchée.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $$
BEGIN
  IF to_regclass('recrutement.fiche') IS NULL THEN
    RAISE EXCEPTION 'le schéma recrutement (R3) n''est pas posé : rien n''a été fait';
  END IF;
  IF to_regclass('recrutement.suivi') IS NOT NULL THEN
    RAISE EXCEPTION 'recrutement.suivi existe déjà : patch déjà posé ? (rien n''a été fait)';
  END IF;
END $$;

-- ── 1. LES TABLES ────────────────────────────────────────────────────────────────────────────────────
create table recrutement.agence_gti (
    nom          text             primary key,
    departement  text             not null check (departement in ('07', '42', '43', '63')),
    lat          double precision not null,
    lon          double precision not null,
    monte_le     timestamptz      not null default now()
);

create table recrutement.suivi (
    reseau            text        not null,
    identifiant       text        not null,
    -- 0 = rien ; 1 Repérée · 2 Contactée · 3 Rendez-vous · 4 Proposition · 5 Contrat signé · 6 Accès ouvert
    etape             smallint    not null default 1 check (etape between 0 and 6),
    statut            text        check (statut is null or statut in ('pas_interesse', 'a_verifier', 'a_trancher')),
    reprise_le        date,
    info_donnee_le    timestamptz,                 -- « C'est fait, je l'ai informée » (RGPD, au 1er contact)
    prochaine_action  text,
    prochaine_le      date,
    suivi_par         uuid,
    agence_envisagee  text,
    archive           boolean     not null default false,   -- « retirée de ma liste »
    archive_le        timestamptz,
    modifie_le        timestamptz not null default now(),
    modifie_par       uuid,
    primary key (reseau, identifiant),
    foreign key (reseau, identifiant) references recrutement.fiche (reseau, identifiant) on delete cascade
);

create table recrutement.evenement (
    id           bigint      generated always as identity primary key,
    reseau       text        not null,
    identifiant  text        not null,
    quand        timestamptz not null default now(),
    type         text        not null check (type in ('appel', 'note', 'email', 'rdv', 'etape', 'correction',
                                                      'ajout', 'retrait', 'info')),
    resultat     text        check (resultat is null or resultat in ('messagerie', 'pas_disponible', 'interesse',
                                                                     'pas_interesse')),
    texte        text,
    rdv_le       timestamptz,
    par          uuid,
    foreign key (reseau, identifiant) references recrutement.fiche (reseau, identifiant) on delete cascade
);
create index evenement_par_fiche on recrutement.evenement (reseau, identifiant, quand desc);

create table recrutement.retrait (
    id           bigint      generated always as identity primary key,
    niveau       text        not null check (niveau in ('ne_plus_contacter', 'effacer')),
    nom_affiche  text,
    siren        text,
    qui          text        not null check (qui in ('elle_meme', 'notre_decision')),
    demande_le   date        not null,
    pose_le      timestamptz not null default now(),
    pose_par     uuid,
    -- ⛔ une personne EFFACÉE ne laisse rien de lisible
    constraint retrait_efface_sans_nom check (niveau = 'ne_plus_contacter' or (nom_affiche is null and siren is null))
);

alter table recrutement.agence_gti enable row level security;
alter table recrutement.suivi      enable row level security;
alter table recrutement.evenement  enable row level security;
alter table recrutement.retrait    enable row level security;
revoke all on recrutement.agence_gti, recrutement.suivi, recrutement.evenement, recrutement.retrait
  from public, anon, authenticated;
-- le robot envoie les agences (et ne voit ni le suivi, ni le fil, ni les retraits)
grant select, insert, update on recrutement.agence_gti to recrutement_robot;
create policy robot_agence_gti on recrutement.agence_gti for all to recrutement_robot using (true) with check (true);

-- ── 2. LA CLÉ DE NOM ET LES EMPREINTES (identiques au collecteur Python) ─────────────────────────────
-- Python : sans_accents (NFD, sans les marques Mn) -> minuscules -> [^a-z0-9]+ devient « - » -> mots triés.
create or replace function recrutement.cle_nom(p_prenom text, p_nom text)
returns text language sql immutable set search_path to 'pg_catalog' as $$
  select string_agg(m, '-' order by m collate "C")
    from unnest(string_to_array(
           btrim(regexp_replace(
             lower(regexp_replace(normalize(coalesce(p_prenom, '') || ' ' || coalesce(p_nom, ''), NFD),
                                  '[̀-ͯ᪰-᫿᷀-᷿⃐-⃿︠-︯]', '', 'g')),
             '[^a-z0-9]+', '-', 'g'), '-'), '-')) m
   where m <> ''
$$;

create or replace function recrutement.empreinte(p_texte text)
returns text language sql immutable set search_path to 'pg_catalog' as $$
  select encode(sha256(convert_to(p_texte, 'UTF8')), 'hex')
$$;

-- Les empreintes d'une personne (nature, empreinte) — comme empreintes_personne() en Python.
create or replace function recrutement.empreintes(p_siren text, p_telephone text, p_email text,
                                                  p_prenom text, p_nom text, p_departement text)
returns table (nature text, empreinte text) language sql immutable set search_path to 'pg_catalog' as $$
  select 'siren', recrutement.empreinte('siren:' || regexp_replace(p_siren, '\D', '', 'g'))
   where coalesce(p_siren, '') <> ''
  union all
  select 'telephone', recrutement.empreinte('tel:' || regexp_replace(p_telephone, '\D', '', 'g'))
   where coalesce(p_telephone, '') <> ''
  union all
  select 'email', recrutement.empreinte('email:' || lower(regexp_replace(p_email, '^\s+|\s+$', '', 'g')))
   where coalesce(p_email, '') <> ''
  union all
  select 'nom', recrutement.empreinte('nom:' || recrutement.cle_nom(p_prenom, p_nom) || ':' || p_departement)
   where coalesce(p_nom, '') <> '' and coalesce(p_departement, '') <> ''
$$;

-- La valeur que l'écran montre : celle du carnet si un humain l'a corrigée, sinon celle de l'annuaire.
create or replace function recrutement.valeur(p_carnet jsonb, p_champ text, p_annuaire text)
returns text language sql immutable set search_path to 'pg_catalog' as $$
  select case when p_carnet ? p_champ then p_carnet ->> p_champ else p_annuaire end
$$;

revoke all on function recrutement.cle_nom(text, text), recrutement.empreinte(text),
                       recrutement.empreintes(text, text, text, text, text, text),
                       recrutement.valeur(jsonb, text, text) from public, anon, authenticated;

-- La garde commune : administrateur, sinon 42501.
create or replace function recrutement.exiger_admin()
returns void language plpgsql stable security definer set search_path to 'public' as $$
begin
  if not public.is_app_admin() then
    raise exception 'Réservé aux administrateurs' using errcode = '42501';
  end if;
end $$;
revoke all on function recrutement.exiger_admin() from public, anon, authenticated;

-- ── 3. LES FONCTIONS DE L'ÉCRAN (administrateurs seulement) ──────────────────────────────────────────

-- 3a. Toute la liste, en un appel (le filtre et le tri se font dans le navigateur).
create or replace function public.rec_candidats()
returns jsonb language plpgsql stable security definer set search_path to 'public' as $$
begin
  perform recrutement.exiger_admin();
  return jsonb_build_object(
    'etat', public.rec_etat_collecte(),
    'agences', coalesce((select jsonb_agg(jsonb_build_object('nom', a.nom, 'departement', a.departement,
                                                             'lat', a.lat, 'lon', a.lon) order by a.nom)
                           from recrutement.agence_gti a), '[]'::jsonb),
    'candidats', coalesce((
      select jsonb_agg(jsonb_build_object(
               'reseau', f.reseau, 'identifiant', f.identifiant, 'origine', f.origine,
               'prenom', recrutement.valeur(k.carnet, 'prenom', f.prenom),
               'nom', recrutement.valeur(k.carnet, 'nom', f.nom),
               'fonction', recrutement.valeur(k.carnet, 'fonction', f.fonction),
               'agence', recrutement.valeur(k.carnet, 'agence', f.agence),
               'commune', recrutement.valeur(k.carnet, 'commune', f.commune),
               'code_postal', recrutement.valeur(k.carnet, 'code_postal', f.code_postal),
               'departement', f.departement, 'lat', f.lat, 'lon', f.lon,
               'agence_gti_proche', f.agence_gti_proche, 'distance_km', f.distance_km,
               'telephone', recrutement.valeur(k.carnet, 'telephone', f.telephone),
               'email', recrutement.valeur(k.carnet, 'email', f.email),
               'siren', f.siren, 'nb_annonces', f.nb_annonces, 'nb_avis', f.nb_avis, 'note_avis', f.note_avis,
               'distinction', f.distinction, 'desactive', f.desactive,
               'etat_suivi', f.etat_suivi, 'etat_depuis', f.etat_depuis, 'motif_depart', f.motif_depart,
               'premiere_vue', f.premiere_vue, 'url', f.url,
               'entreprise_creee_le', e.date_creation, 'entreprise_etat', e.etat,
               'opposition', coalesce(e.opposition, false),
               'etape', coalesce(s.etape, 1), 'statut', s.statut, 'reprise_le', s.reprise_le,
               'prochaine_action', s.prochaine_action, 'prochaine_le', s.prochaine_le,
               'suivi_par', s.suivi_par, 'archive', coalesce(s.archive, false),
               'corrige', k.carnet is not null))
        from recrutement.fiche f
        left join recrutement.suivi s on s.reseau = f.reseau and s.identifiant = f.identifiant
        left join recrutement.entreprise e on e.siren = f.siren
        left join lateral (select jsonb_object_agg(c.champ, c.valeur) carnet
                             from recrutement.correction c
                            where c.reseau = f.reseau and c.identifiant = f.identifiant) k on true), '[]'::jsonb));
end $$;

-- 3b. Une fiche, avec son entreprise, son suivi, son fil, son carnet et ses autres fiches (même SIREN).
create or replace function public.rec_candidat(p_reseau text, p_identifiant text)
returns jsonb language plpgsql stable security definer set search_path to 'public' as $$
declare
  f recrutement.fiche;
begin
  perform recrutement.exiger_admin();
  select * into f from recrutement.fiche where reseau = p_reseau and identifiant = p_identifiant;
  if not found then
    raise exception 'fiche introuvable' using errcode = 'P0002';
  end if;
  return jsonb_build_object(
    'fiche', to_jsonb(f),
    'entreprise', (select to_jsonb(e) from recrutement.entreprise e where e.siren = f.siren),
    'suivi', (select to_jsonb(s) from recrutement.suivi s where s.reseau = f.reseau and s.identifiant = f.identifiant),
    'carnet', coalesce((select jsonb_agg(jsonb_build_object('champ', c.champ, 'valeur', c.valeur, 'le', c.le,
                                                            'par', p.display_name) order by c.le desc)
                          from recrutement.correction c left join public.app_user_profile p on p.id = c.par
                         where c.reseau = f.reseau and c.identifiant = f.identifiant), '[]'::jsonb),
    'fil', coalesce((select jsonb_agg(jsonb_build_object('id', v.id, 'quand', v.quand, 'type', v.type,
                                                         'resultat', v.resultat, 'texte', v.texte, 'rdv_le', v.rdv_le,
                                                         'par', p.display_name) order by v.quand desc)
                       from recrutement.evenement v left join public.app_user_profile p on p.id = v.par
                      where v.reseau = f.reseau and v.identifiant = f.identifiant), '[]'::jsonb),
    'autres', coalesce((select jsonb_agg(jsonb_build_object('reseau', o.reseau, 'identifiant', o.identifiant,
                                                            'url', o.url, 'etat_suivi', o.etat_suivi))
                          from recrutement.fiche o
                         where f.siren is not null and o.siren = f.siren
                           and (o.reseau, o.identifiant) <> (f.reseau, f.identifiant)), '[]'::jsonb),
    'suivi_par_nom', (select p.display_name from recrutement.suivi s join public.app_user_profile p on p.id = s.suivi_par
                       where s.reseau = f.reseau and s.identifiant = f.identifiant));
end $$;

-- 3c. Noter dans le fil (appel, note, e-mail, rendez-vous). Une fiche notée entre dans le suivi.
create or replace function public.rec_noter(p_reseau text, p_identifiant text, p_type text, p_texte text,
                                            p_resultat text default null, p_rdv_le timestamptz default null)
returns bigint language plpgsql volatile security definer set search_path to 'public' as $$
declare
  v_id bigint;
begin
  perform recrutement.exiger_admin();
  if p_type not in ('appel', 'note', 'email', 'rdv') then
    raise exception 'type de note inconnu : %', p_type using errcode = '22023';
  end if;
  insert into recrutement.suivi (reseau, identifiant, modifie_par) values (p_reseau, p_identifiant, auth.uid())
  on conflict (reseau, identifiant) do nothing;
  insert into recrutement.evenement (reseau, identifiant, type, resultat, texte, rdv_le, par)
  values (p_reseau, p_identifiant, p_type, p_resultat, nullif(btrim(p_texte), ''), p_rdv_le, auth.uid())
  returning id into v_id;
  -- un appel « pas intéressée » le dit aussi au suivi (on pourra reprendre plus tard)
  if p_type = 'appel' and p_resultat = 'pas_interesse' then
    update recrutement.suivi set statut = 'pas_interesse', modifie_le = now(), modifie_par = auth.uid()
     where reseau = p_reseau and identifiant = p_identifiant;
  end if;
  return v_id;
end $$;

-- 3d. Marquer une étape du parcours (cliquer l'étape n = les étapes 1..n sont faites).
create or replace function public.rec_etape(p_reseau text, p_identifiant text, p_etape integer)
returns void language plpgsql volatile security definer set search_path to 'public' as $$
declare
  noms constant text[] := array['Repérée', 'Contactée', 'Rendez-vous', 'Proposition', 'Contrat signé', 'Accès ouvert'];
begin
  perform recrutement.exiger_admin();
  if p_etape not between 0 and 6 then
    raise exception 'étape hors bornes : %', p_etape using errcode = '22023';
  end if;
  insert into recrutement.suivi (reseau, identifiant, etape, modifie_par)
  values (p_reseau, p_identifiant, p_etape, auth.uid())
  on conflict (reseau, identifiant) do update set etape = excluded.etape, modifie_le = now(), modifie_par = auth.uid();
  insert into recrutement.evenement (reseau, identifiant, type, texte, par)
  values (p_reseau, p_identifiant, 'etape',
          case when p_etape = 0 then 'parcours remis à zéro' else 'étape : ' || noms[p_etape] end, auth.uid());
end $$;

-- 3e. Mettre à jour le suivi (statut, prochaine action, qui suit, agence envisagée, archive, info donnée).
create or replace function public.rec_suivi_maj(p_reseau text, p_identifiant text, p_champs jsonb)
returns void language plpgsql volatile security definer set search_path to 'public' as $$
declare
  inconnus text[];
begin
  perform recrutement.exiger_admin();
  select array_agg(k) into inconnus from jsonb_object_keys(p_champs) k
   where k not in ('statut', 'reprise_le', 'prochaine_action', 'prochaine_le', 'suivi_par', 'agence_envisagee',
                   'archive', 'info_donnee');
  if inconnus is not null then
    raise exception 'champs refusés : %', inconnus using errcode = '22023';
  end if;
  insert into recrutement.suivi (reseau, identifiant, modifie_par) values (p_reseau, p_identifiant, auth.uid())
  on conflict (reseau, identifiant) do nothing;
  update recrutement.suivi s set
    statut           = case when p_champs ? 'statut' then p_champs ->> 'statut' else s.statut end,
    reprise_le       = case when p_champs ? 'reprise_le' then (p_champs ->> 'reprise_le')::date else s.reprise_le end,
    prochaine_action = case when p_champs ? 'prochaine_action' then nullif(btrim(p_champs ->> 'prochaine_action'), '') else s.prochaine_action end,
    prochaine_le     = case when p_champs ? 'prochaine_le' then (p_champs ->> 'prochaine_le')::date else s.prochaine_le end,
    suivi_par        = case when p_champs ? 'suivi_par' then (p_champs ->> 'suivi_par')::uuid else s.suivi_par end,
    agence_envisagee = case when p_champs ? 'agence_envisagee' then p_champs ->> 'agence_envisagee' else s.agence_envisagee end,
    archive          = case when p_champs ? 'archive' then (p_champs ->> 'archive')::boolean else s.archive end,
    archive_le       = case when p_champs ? 'archive' then (case when (p_champs ->> 'archive')::boolean then now() end) else s.archive_le end,
    info_donnee_le   = case when p_champs ? 'info_donnee' then (case when (p_champs ->> 'info_donnee')::boolean then now() end) else s.info_donnee_le end,
    modifie_le = now(), modifie_par = auth.uid()
   where s.reseau = p_reseau and s.identifiant = p_identifiant;
  if p_champs ? 'info_donnee' and (p_champs ->> 'info_donnee')::boolean then
    insert into recrutement.evenement (reseau, identifiant, type, texte, par)
    values (p_reseau, p_identifiant, 'info', 'informée de la source de ses coordonnées et de son droit de refus', auth.uid());
  end if;
  if p_champs ? 'archive' then
    insert into recrutement.evenement (reseau, identifiant, type, texte, par)
    values (p_reseau, p_identifiant, 'retrait',
            case when (p_champs ->> 'archive')::boolean then 'retirée de ma liste' else 'remise dans ma liste' end, auth.uid());
  end if;
end $$;

-- 3f. Corriger un champ (le carnet). p_valeur NULL et p_revenir = vrai : revenir à la valeur de l'annuaire.
create or replace function public.rec_corriger(p_reseau text, p_identifiant text, p_champ text, p_valeur text,
                                               p_revenir boolean default false)
returns void language plpgsql volatile security definer set search_path to 'public' as $$
begin
  perform recrutement.exiger_admin();
  if p_revenir then
    delete from recrutement.correction where reseau = p_reseau and identifiant = p_identifiant and champ = p_champ;
  else
    insert into recrutement.correction (reseau, identifiant, champ, valeur, par)
    values (p_reseau, p_identifiant, p_champ, nullif(btrim(p_valeur), ''), auth.uid())
    on conflict (reseau, identifiant, champ) do update set valeur = excluded.valeur, par = auth.uid(), le = now();
  end if;
  insert into recrutement.evenement (reseau, identifiant, type, texte, par)
  values (p_reseau, p_identifiant, 'correction',
          case when p_revenir then p_champ || ' : retour à la valeur de l''annuaire' else p_champ || ' corrigé' end, auth.uid());
end $$;

-- 3g. Les doublons possibles d'une personne qu'on va ajouter (et si elle est sur la liste « ne plus contacter »).
create or replace function public.rec_doublons(p_prenom text, p_nom text, p_telephone text, p_email text,
                                               p_siren text, p_departement text)
returns jsonb language plpgsql stable security definer set search_path to 'public' as $$
declare
  cle text := recrutement.cle_nom(p_prenom, p_nom);
begin
  perform recrutement.exiger_admin();
  return jsonb_build_object(
    'sur_liste_noire', exists (select 1 from recrutement.empreintes(p_siren, p_telephone, p_email, p_prenom, p_nom, p_departement) x
                                 join recrutement.liste_noire n on n.empreinte = x.empreinte),
    'fiches', coalesce((select jsonb_agg(jsonb_build_object('reseau', f.reseau, 'identifiant', f.identifiant,
                                                            'prenom', f.prenom, 'nom', f.nom, 'commune', f.commune))
                          from recrutement.fiche f
                         where (cle is not null and recrutement.cle_nom(f.prenom, f.nom) = cle)
                            or (coalesce(p_siren, '') <> '' and f.siren = regexp_replace(p_siren, '\D', '', 'g'))
                            or (coalesce(p_telephone, '') <> '' and regexp_replace(f.telephone, '\D', '', 'g') = regexp_replace(p_telephone, '\D', '', 'g'))
                            or (coalesce(p_email, '') <> '' and lower(f.email) = lower(btrim(p_email)))), '[]'::jsonb));
end $$;

-- 3h. Ajouter un candidat à la main (origine « saisie »). Refusé s'il est sur la liste « ne plus contacter ».
create or replace function public.rec_ajouter(p jsonb)
returns jsonb language plpgsql volatile security definer set search_path to 'public' as $$
declare
  v_id text := gen_random_uuid()::text;
  v_etape smallint := coalesce((p ->> 'etape')::smallint, 1);
begin
  perform recrutement.exiger_admin();
  if coalesce(btrim(p ->> 'nom'), '') = '' then
    raise exception 'le nom est obligatoire' using errcode = '22023';
  end if;
  if (coalesce(p ->> 'telephone', '') <> '' or coalesce(p ->> 'email', '') <> '') and coalesce(btrim(p ->> 'source_contact'), '') = '' then
    raise exception 'une coordonnée doit dire d''où elle vient' using errcode = '22023';
  end if;
  if exists (select 1 from recrutement.empreintes(p ->> 'siren', p ->> 'telephone', p ->> 'email', p ->> 'prenom', p ->> 'nom', p ->> 'departement') x
               join recrutement.liste_noire n on n.empreinte = x.empreinte) then
    raise exception 'cette personne a demandé à ne plus être contactée' using errcode = '42501';
  end if;
  insert into recrutement.fiche (reseau, identifiant, origine, prenom, nom, fonction, agence, commune, code_postal,
                                 departement, lat, lon, agence_gti_proche, distance_km, telephone, email, source_contact, siren)
  values ('saisie', v_id, 'saisie', nullif(btrim(p ->> 'prenom'), ''), btrim(p ->> 'nom'), nullif(p ->> 'fonction', ''),
          nullif(p ->> 'agence', ''), nullif(p ->> 'commune', ''), nullif(p ->> 'code_postal', ''), nullif(p ->> 'departement', ''),
          (p ->> 'lat')::double precision, (p ->> 'lon')::double precision, nullif(p ->> 'agence_gti_proche', ''),
          (p ->> 'distance_km')::numeric, nullif(btrim(p ->> 'telephone'), ''), nullif(lower(btrim(p ->> 'email')), ''),
          nullif(btrim(p ->> 'source_contact'), ''), nullif(regexp_replace(coalesce(p ->> 'siren', ''), '\D', '', 'g'), ''));
  insert into recrutement.suivi (reseau, identifiant, etape, statut, prochaine_action, prochaine_le, agence_envisagee, modifie_par)
  values ('saisie', v_id, v_etape, nullif(p ->> 'statut', ''), nullif(p ->> 'prochaine_action', ''),
          (p ->> 'prochaine_le')::date, nullif(p ->> 'agence_envisagee', ''), auth.uid());
  insert into recrutement.evenement (reseau, identifiant, type, texte, par)
  values ('saisie', v_id, 'ajout', 'ajoutée à la main' || coalesce(' : ' || nullif(btrim(p ->> 'source_contact'), ''), ''), auth.uid());
  return jsonb_build_object('reseau', 'saisie', 'identifiant', v_id);
end $$;

-- 3i. Retirer : « archiver » (de ma liste), « ne_plus_contacter » (reste : nom, SIREN, date), « effacer » (rien).
--     Les deux derniers posent ses empreintes sur la liste noire et effacent TOUTES ses fiches (même SIREN,
--     même téléphone, même e-mail, même nom dans le même département), avec leur fil et leur carnet.
create or replace function public.rec_retirer(p_reseau text, p_identifiant text, p_niveau text,
                                              p_qui text default 'elle_meme', p_demande_le date default current_date)
returns jsonb language plpgsql volatile security definer set search_path to 'public' as $$
declare
  f recrutement.fiche;
  v_tel text; v_mail text;
  v_emp text[]; v_nat text[];
  n_fiches integer := 0;
begin
  perform recrutement.exiger_admin();
  if p_niveau not in ('archiver', 'ne_plus_contacter', 'effacer') then
    raise exception 'niveau inconnu : %', p_niveau using errcode = '22023';
  end if;
  select * into f from recrutement.fiche where reseau = p_reseau and identifiant = p_identifiant;
  if not found then
    raise exception 'fiche introuvable' using errcode = 'P0002';
  end if;
  if p_niveau = 'archiver' then
    perform public.rec_suivi_maj(p_reseau, p_identifiant, jsonb_build_object('archive', true));
    return jsonb_build_object('niveau', 'archiver', 'fiches_effacees', 0);
  end if;
  -- les coordonnées du carnet comptent aussi (un numéro corrigé est aussi le sien)
  select valeur into v_tel from recrutement.correction where reseau = p_reseau and identifiant = p_identifiant and champ = 'telephone';
  select valeur into v_mail from recrutement.correction where reseau = p_reseau and identifiant = p_identifiant and champ = 'email';
  -- (des tableaux, pas une table temporaire : la fonction peut être appelée deux fois dans une transaction)
  select array_agg(d.empreinte order by d.empreinte), array_agg(d.nature order by d.empreinte)
    into v_emp, v_nat
    from (select distinct x.nature, x.empreinte
            from (select * from recrutement.empreintes(f.siren, f.telephone, f.email, f.prenom, f.nom, f.departement)
                  union all select * from recrutement.empreintes(null, v_tel, v_mail, null, null, null)) x) d;
  if v_emp is null then
    raise exception 'aucune empreinte possible pour cette fiche (ni SIREN, ni coordonnée, ni nom + département)' using errcode = '22023';
  end if;
  insert into recrutement.liste_noire (empreinte, nature, niveau, demande_le, pose_par)
  select e, n, p_niveau, p_demande_le, auth.uid() from unnest(v_emp, v_nat) as u(e, n)
  on conflict (empreinte) do update set niveau = case when excluded.niveau = 'effacer' then 'effacer' else recrutement.liste_noire.niveau end;
  insert into recrutement.retrait (niveau, nom_affiche, siren, qui, demande_le, pose_par)
  values (p_niveau,
          case when p_niveau = 'ne_plus_contacter' then btrim(coalesce(f.prenom, '') || ' ' || coalesce(f.nom, '')) end,
          case when p_niveau = 'ne_plus_contacter' then f.siren end,
          p_qui, p_demande_le, auth.uid());
  -- toutes ses fiches : celles dont UNE empreinte est sur la liste
  with cibles as (
    select o.reseau, o.identifiant
      from recrutement.fiche o
     where exists (select 1 from recrutement.empreintes(o.siren, o.telephone, o.email, o.prenom, o.nom, o.departement) y
                    where y.empreinte = any (v_emp))
        or (o.reseau, o.identifiant) = (f.reseau, f.identifiant))
  delete from recrutement.fiche o using cibles c where o.reseau = c.reseau and o.identifiant = c.identifiant;
  get diagnostics n_fiches = row_count;
  delete from recrutement.entreprise e where e.siren = f.siren and not exists (select 1 from recrutement.fiche o where o.siren = e.siren);
  return jsonb_build_object('niveau', p_niveau, 'fiches_effacees', n_fiches, 'empreintes', coalesce(array_length(v_emp, 1), 0));
end $$;

-- ── 4. LES DROITS DES FONCTIONS ──────────────────────────────────────────────────────────────────────
-- ⛔ `revoke ... from public` NE FERME PAS authenticated : on nomme les rôles. authenticated GARDE le droit
--   d'appeler (un administrateur est authenticated) ; c'est exiger_admin() qui refuse les autres.
revoke all on function public.rec_candidats(), public.rec_candidat(text, text),
                       public.rec_noter(text, text, text, text, text, timestamptz),
                       public.rec_etape(text, text, integer), public.rec_suivi_maj(text, text, jsonb),
                       public.rec_corriger(text, text, text, text, boolean),
                       public.rec_doublons(text, text, text, text, text, text),
                       public.rec_ajouter(jsonb), public.rec_retirer(text, text, text, text, date)
  from public, anon;
grant execute on function public.rec_candidats(), public.rec_candidat(text, text),
                          public.rec_noter(text, text, text, text, text, timestamptz),
                          public.rec_etape(text, text, integer), public.rec_suivi_maj(text, text, jsonb),
                          public.rec_corriger(text, text, text, text, boolean),
                          public.rec_doublons(text, text, text, text, text, text),
                          public.rec_ajouter(jsonb), public.rec_retirer(text, text, text, text, date)
  to authenticated;

COMMIT;
