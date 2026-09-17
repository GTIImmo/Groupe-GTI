-- ═══════════════════════════════════════════════════════════════════════════════
-- 1.4 : L'ACQUEREUR PERDU EN SILENCE -- ON LE CONSTATE, ON LE DIT          17/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- LE DEFAUT (liste, tache 1.4, mesure cinq fois) : on envoie deux acquereurs, Hektor
-- en garde un, SANS erreur, SANS message. Le registre recopie ensuite SA liste
-- (reporterAuRegistre, 16/09) : la personne disparait de l'ecran, et personne ne
-- sait qu'elle a ete demandee.
--
-- LA METHODE ARBITREE LE 03/09 : « constater », pas « predire ». Relire apres
-- l'envoi, comparer demande / garde -- aucune hypothese sur la cause, qui n'est
-- toujours pas prouvee. Le worker relit DEJA les personnes (16/09) : la
-- comparaison ne coute aucune requete chez Hektor.
--
-- ─── CETTE TABLE ───
-- Une ligne par personne DEMANDEE et NON GARDEE, sur une transaction. Elle porte un
-- bandeau dans la modale jusqu'a ce qu'elle soit fermee :
--     par le worker   un envoi suivant montre que Hektor l'a gardee
--                     (ferme_motif = 'gardee_au_renvoi'), ou l'ecran a reaffirme
--                     une liste qui ne la contient plus ('retiree_par_l_app') ;
--     a la main       le negociateur a vu, et decide ('ferme_a_la_main').
-- ⚠ ON NE SUPPRIME JAMAIS : une ligne fermee dit encore qu'il y a eu un refus.
--
-- ─── LA CLE DE LA TRANSACTION : (kind, hektor_affaire_id) ───
-- Pas app_affaire_id : il peut porter plusieurs transactions successives
-- (1001352 : 50084 puis 50086, constate le 17/09). Le numero d'app est recopie
-- pour la lecture et les droits, il n'identifie pas.
--
-- ⚠ UNE SEULE LIGNE OUVERTE par (transaction, role, personne) : l'index unique
--   partiel. Un second refus identique ne double pas le bandeau.
--
-- RETOUR ARRIERE :
--     DROP FUNCTION public.app_affaire_personne_ecart_fermer(bigint);
--     DROP TABLE public.app_affaire_personne_ecart;
--   Le worker ecrit en best-effort : sans la table, il journalise et continue.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.app_affaire_personne_ecart (
    id                 bigserial PRIMARY KEY,
    kind               text NOT NULL,
    hektor_affaire_id  text NOT NULL,
    app_affaire_id     bigint,
    app_dossier_id     bigint,
    hektor_annonce_id  bigint,
    role               text NOT NULL CHECK (role IN ('acquereur', 'mandant')),
    contact_id         text NOT NULL,
    -- Recopie au constat : la personne n'est PLUS sur la transaction, donc le
    -- registre ne peut plus donner son nom.
    contact_nom        text,
    job_id             uuid,
    constate_le        timestamptz NOT NULL DEFAULT now(),
    ferme_le           timestamptz,
    ferme_par          text,
    ferme_motif        text
);

CREATE UNIQUE INDEX IF NOT EXISTS app_affaire_personne_ecart_ouvert_uidx
    ON public.app_affaire_personne_ecart (kind, hektor_affaire_id, role, contact_id)
    WHERE ferme_le IS NULL;

COMMENT ON TABLE public.app_affaire_personne_ecart IS
    'PERSONNES DEMANDEES A HEKTOR ET NON GARDEES (tache 1.4). Ecrite par le worker '
    'apres la relecture d''une creation ou d''une modification de transaction. Une '
    'ligne ouverte = un bandeau dans la modale. Jamais supprimee, seulement fermee.';

ALTER TABLE public.app_affaire_personne_ecart ENABLE ROW LEVEL SECURITY;

-- Lecture pour tout compte connecte, ecriture par le worker (service_role) et par
-- la fonction de fermeture seule -- meme patron que app_affaire_note.
DROP POLICY IF EXISTS app_affaire_personne_ecart_read ON public.app_affaire_personne_ecart;
CREATE POLICY app_affaire_personne_ecart_read ON public.app_affaire_personne_ecart
    FOR SELECT TO authenticated USING (true);

GRANT SELECT ON TABLE public.app_affaire_personne_ecart TO authenticated;
GRANT ALL    ON TABLE public.app_affaire_personne_ecart TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.app_affaire_personne_ecart_id_seq TO service_role;

-- ═══ FERMER UN BANDEAU, A LA MAIN ═══
-- ⚠ LES MEMES GARDES que app_affaire_note_ecrire, dans le meme ordre, adaptees a
--   une ligne qui peut ne plus avoir d'affaire au registre (transaction supprimee
--   depuis) : les droits se jugent alors sur le dossier recopie.
CREATE OR REPLACE FUNCTION public.app_affaire_personne_ecart_fermer(target_id bigint)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
DECLARE
  e app_affaire_personne_ecart%rowtype;
BEGIN
  SELECT * INTO e FROM app_affaire_personne_ecart WHERE id = target_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'ecart_not_found' USING errcode = '22023';
  END IF;
  IF NOT public.is_app_admin() THEN
    RAISE EXCEPTION 'not_allowed' USING errcode = '42501';
  END IF;
  IF NOT public.app_console_can_access_dossier(e.app_dossier_id, e.hektor_annonce_id::text) THEN
    RAISE EXCEPTION 'dossier_not_allowed' USING errcode = '42501';
  END IF;
  -- Deja fermee : on ne reecrit ni la date ni l'auteur de la premiere fermeture.
  IF e.ferme_le IS NOT NULL THEN
    RETURN jsonb_build_object('ok', true, 'id', target_id, 'deja_fermee', true);
  END IF;
  UPDATE app_affaire_personne_ecart
     SET ferme_le = now(),
         ferme_par = coalesce(auth.uid()::text, 'app'),
         ferme_motif = 'ferme_a_la_main'
   WHERE id = target_id;
  RETURN jsonb_build_object('ok', true, 'id', target_id);
END
$function$;

REVOKE ALL ON FUNCTION public.app_affaire_personne_ecart_fermer(bigint) FROM public, anon;
GRANT EXECUTE ON FUNCTION public.app_affaire_personne_ecart_fermer(bigint) TO authenticated, service_role;

COMMENT ON FUNCTION public.app_affaire_personne_ecart_fermer(bigint) IS
    'Ferme a la main le bandeau « Hektor n''a pas garde cette personne ». Ne '
    'supprime rien et n''envoie RIEN chez Hektor.';
