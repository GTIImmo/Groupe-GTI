-- ═══════════════════════════════════════════════════════════════════════════
-- RECRUTEMENT E2 — ÉCRIRE À PLUSIEURS CANDIDATS : ce que la liste doit savoir                24/11/2026
-- Proposition et maquette validées : notice/RECRUTEMENT_EMAILS_AUDIT_ET_PROPOSITION_2026-11-24.md (§2 B), planches 2-3.
-- Suppose R3 et R6 posés. Répétition : _REPETITION.sql ; retour : _INVERSE.sql (remet rec_candidats de R6 À L'IDENTIQUE).
--
-- CE QUE POSE CE PATCH (et rien d'autre) :
--   1. public.rec_candidats() rend 3 clés de plus par candidat, sans rien changer aux autres :
--        source_contact  d'où vient sa coordonnée (pour le bloc d'information RGPD de SON e-mail)
--        info_donnee_le  la date où elle a été informée (sinon le bloc complet est dû)
--        dernier_email   le dernier e-mail noté dans son fil (« déjà écrit il y a moins de 30 jours »)
--   2. public.rec_emails_du_jour() : combien d'e-mails l'administrateur connecté a notés AUJOURD'HUI (heure de Paris)
--      — le plafond de 40 par jour et par expéditeur.
-- Les deux : administrateurs seulement (exiger_admin, sinon 42501). ⛔ Rien chez Hektor, aucune table touchée.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $$
BEGIN
  IF to_regclass('recrutement.evenement') IS NULL THEN
    RAISE EXCEPTION 'le patch de l''écran (R6) n''est pas posé : rien n''a été fait';
  END IF;
  IF to_regprocedure('public.rec_emails_du_jour()') IS NOT NULL THEN
    RAISE EXCEPTION 'patch déjà posé ? (rien n''a été fait)';
  END IF;
END $$;

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
BEGIN
  IF to_regprocedure('public.rec_emails_du_jour()') IS NULL OR to_regprocedure('public.rec_candidats()') IS NULL THEN
    RAISE EXCEPTION 'une fonction manque : rien n''a été fait';
  END IF;
  IF has_function_privilege('anon', 'public.rec_emails_du_jour()', 'EXECUTE')
     OR has_function_privilege('anon', 'public.rec_candidats()', 'EXECUTE') THEN
    RAISE EXCEPTION 'anon pourrait appeler une fonction du recrutement : rien n''a été fait';
  END IF;
END $$;

COMMIT;
