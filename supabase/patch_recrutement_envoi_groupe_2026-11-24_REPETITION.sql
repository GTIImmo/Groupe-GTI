-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — RECRUTEMENT E2 (écrire à plusieurs candidats)                                24/11/2026
-- Rejoue le corps du patch (recopié par programme), se fait passer pour un administrateur puis pour un
-- non-administrateur, vérifie 7 points, et LÈVE VOLONTAIREMENT UNE EXCEPTION à la fin : tout est annulé.
-- Message attendu : « RÉPÉTITION VERTE : 7 contrôles sur 7 ». ⛔ Aucune validation de transaction dans ce fichier.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

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
               'corrige', k.carnet is not null,
               -- E2 (24/11) : les trois clés de l'envoi groupé
               'source_contact', f.source_contact,
               'info_donnee_le', s.info_donnee_le,
               'dernier_email', (select max(v.quand) from recrutement.evenement v
                                  where v.reseau = f.reseau and v.identifiant = f.identifiant and v.type = 'email')))
        from recrutement.fiche f
        left join recrutement.suivi s on s.reseau = f.reseau and s.identifiant = f.identifiant
        left join recrutement.entreprise e on e.siren = f.siren
        left join lateral (select jsonb_object_agg(c.champ, c.valeur) carnet
                             from recrutement.correction c
                            where c.reseau = f.reseau and c.identifiant = f.identifiant) k on true), '[]'::jsonb));
end $$;

create or replace function public.rec_emails_du_jour()
returns integer language plpgsql stable security definer set search_path to 'public' as $$
begin
  perform recrutement.exiger_admin();
  return (select count(*) from recrutement.evenement v
           where v.type = 'email' and v.par = auth.uid()
             and (v.quand at time zone 'Europe/Paris')::date = (now() at time zone 'Europe/Paris')::date);
end $$;

-- ⛔ `revoke ... from public` NE FERME PAS authenticated : on nomme les rôles (exiger_admin refuse les non-admins).
revoke all on function public.rec_emails_du_jour() from public, anon;
grant execute on function public.rec_emails_du_jour() to authenticated;

DO $$
DECLARE
  v_admin uuid; v_autre uuid; j jsonb; c jsonb; n integer; n_fiches integer; k integer := 0;
BEGIN
  SELECT id INTO v_admin FROM public.app_user_profile WHERE role::text = 'admin' AND is_active ORDER BY id LIMIT 1;
  SELECT id INTO v_autre FROM public.app_user_profile WHERE role::text <> 'admin' AND is_active ORDER BY id LIMIT 1;
  SELECT count(*) INTO n_fiches FROM recrutement.fiche;
  -- EN ADMINISTRATEUR
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  PERFORM set_config('request.jwt.claim.sub', v_admin::text, true);
  EXECUTE 'set local role authenticated';
  j := public.rec_candidats();
  n := jsonb_array_length(j->'candidats');
  IF n <> n_fiches THEN RAISE EXCEPTION 'ROUGE 1 : % candidats pour % fiches', n, n_fiches; END IF; k := k + 1;
  c := j->'candidats'->0;
  IF NOT (c ? 'source_contact' AND c ? 'info_donnee_le' AND c ? 'dernier_email') THEN RAISE EXCEPTION 'ROUGE 2 : une clé de E2 manque'; END IF; k := k + 1;
  IF (SELECT count(*) FROM jsonb_object_keys(c)) <> 41 OR NOT (c ? 'etape' AND c ? 'corrige' AND c ? 'opposition' AND c ? 'email') THEN
    RAISE EXCEPTION 'ROUGE 3 : % clés au lieu de 41 (38 de R6 + 3), ou une clé de R6 a disparu', (SELECT count(*) FROM jsonb_object_keys(c)); END IF; k := k + 1;
  EXECUTE 'reset role';
  IF (SELECT count(*) FROM jsonb_array_elements(j->'candidats') x WHERE x->>'dernier_email' IS NOT NULL)
     <> (SELECT count(*) FROM (SELECT DISTINCT reseau, identifiant FROM recrutement.evenement WHERE type = 'email') d) THEN
    RAISE EXCEPTION 'ROUGE 4 : « dernier e-mail » ne colle pas aux e-mails du fil'; END IF; k := k + 1;
  n := (SELECT count(*) FROM recrutement.evenement WHERE type = 'email' AND par = v_admin
          AND (quand AT TIME ZONE 'Europe/Paris')::date = (now() AT TIME ZONE 'Europe/Paris')::date);
  EXECUTE 'set local role authenticated';
  IF public.rec_emails_du_jour() <> n THEN RAISE EXCEPTION 'ROUGE 5 : le compte du jour ne colle pas (%)', n; END IF; k := k + 1;
  -- EN NON-ADMINISTRATEUR : refusé
  EXECUTE 'reset role';
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_autre, 'role', 'authenticated')::text, true);
  PERFORM set_config('request.jwt.claim.sub', v_autre::text, true);
  EXECUTE 'set local role authenticated';
  BEGIN PERFORM public.rec_emails_du_jour(); RAISE EXCEPTION 'ROUGE 6 : un non-administrateur lit le compte du jour';
  EXCEPTION WHEN insufficient_privilege THEN k := k + 1; END;
  BEGIN PERFORM public.rec_candidats(); RAISE EXCEPTION 'ROUGE 7 : un non-administrateur lit la liste';
  EXCEPTION WHEN insufficient_privilege THEN k := k + 1; END;
  EXECUTE 'reset role';
  RAISE EXCEPTION 'RÉPÉTITION VERTE : % contrôles sur 7 (tout est annulé, rien n''a été écrit)', k;
END $$;

ROLLBACK;
