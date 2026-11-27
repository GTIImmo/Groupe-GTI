-- ═══════════════════════════════════════════════════════════════════════════
-- INVERSE — RECRUTEMENT E2 (écrire à plusieurs candidats)                                   24/11/2026
-- Remet public.rec_candidats() EXACTEMENT comme R6 l'a posée (texte recopié par programme depuis
-- patch_recrutement_ecran_2026-11-24.sql) et retire public.rec_emails_du_jour(). Ne touche à rien d'autre.
-- ⚠ L'écran (E2) lit les 3 clés en plus : après cet inverse, l'envoi groupé ne voit plus « déjà écrit » ni la source.
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
               'corrige', k.carnet is not null))
        from recrutement.fiche f
        left join recrutement.suivi s on s.reseau = f.reseau and s.identifiant = f.identifiant
        left join recrutement.entreprise e on e.siren = f.siren
        left join lateral (select jsonb_object_agg(c.champ, c.valeur) carnet
                             from recrutement.correction c
                            where c.reseau = f.reseau and c.identifiant = f.identifiant) k on true), '[]'::jsonb));
end $$;

drop function if exists public.rec_emails_du_jour();

-- Le retour arrière ne juge que SA part
DO $$
BEGIN
  IF to_regprocedure('public.rec_emails_du_jour()') IS NOT NULL THEN
    RAISE EXCEPTION 'rec_emails_du_jour est toujours là';
  END IF;
  IF position('dernier_email' in pg_get_functiondef('public.rec_candidats()'::regprocedure)) > 0 THEN
    RAISE EXCEPTION 'rec_candidats porte encore les clés de E2';
  END IF;
END $$;

COMMIT;
