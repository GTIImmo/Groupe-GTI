-- ═══════════════════════════════════════════════════════════════════════════
-- UNE SUPPRESSION ORDONNEE PAR L'APP DISPARAIT PARTOUT          16/09/2026
-- Chantier C.19-d, tache 3.5 -- la suite de 3.4.
-- ═══════════════════════════════════════════════════════════════════════════
--
-- DEMANDE DE FREDERIC, 07/09 : « si suppression, soit compromis soit vente, la
-- ligne doit ENTIEREMENT DISPARAITRE de mon serveur et de mon apps ».
--
-- ⚠ ET ON DISTINGUE DEUX CAS, PARCE QU'ILS N'ONT PAS LA MEME VERITE :
--
--   ① HEKTOR A SUPPRIME DANS SON COIN. Le balayage de nuit le decouvre APRES
--      COUP (« [miroir] compromis : 10 588 chez Hektor, 10 598 au miroir -> 10
--      retirees », run du 16/09). On ne sait pas POURQUOI la ligne a disparu --
--      une fausse manoeuvre ? Effacer chez nous aussi la perdrait pour de bon,
--      exactement comme les annonces 62815, 62825 et 62855 le 19/08.
--      ➡ LA LIGNE RESTE, marquee `present_in_hektor = false`. Inchange.
--
--   ② L'APP A ORDONNE LA SUPPRESSION. La, on sait quelle ligne, et le worker a
--      la PREUVE que Hektor l'a effacee (il relit par l'API et exige `trouve =
--      false`). Rien a deviner.
--      ➡ LA LIGNE PART DES QUATRE ENDROITS. C'est ce que cette table permet.
--
-- POURQUOI UN JOURNAL, ET PAS UN SIMPLE DELETE
-- --------------------------------------------
-- ⚠ SUPPRIMER SEULEMENT DANS SUPABASE NE TIENDRAIT PAS UNE NUIT. Le push du
--   registre fait `SELECT * FROM app_affaire_ledger` en local puis upsert : la
--   ligne locale RECREERAIT la ligne en ligne au run suivant. Le serveur est
--   maitre de ce registre -- il faut donc qu'il apprenne la suppression.
--   Le journal est ce qu'il lit pour s'aligner.
--
-- ⭐ ET IL REPOND A LA QUESTION QUE FREDERIC A POSEE LE 16/09 : « on garde une
--   ligne dans un journal des suppressions, pour pouvoir dire un jour qui a
--   supprime quoi, et quand ? ». Oui : c'est exactement cette table.
--
-- ⚠ ELLE NE S'EFFACE JAMAIS. Une suppression qu'on oublie ne se distingue pas
--   d'une suppression qui n'a pas eu lieu.
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.app_affaire_supprimee (
    app_affaire_id     bigint PRIMARY KEY,
    hektor_annonce_id  bigint,
    kind               text,
    hektor_affaire_id  text,
    -- Ce que Hektor a repondu, pour qu'une suppression contestee soit relisible.
    preuve             text,
    -- 'geste_app' aujourd'hui. La colonne existe pour le jour ou une autre
    -- origine apparaitra -- on saura alors les distinguer sans deviner.
    origine            text NOT NULL DEFAULT 'geste_app',
    supprime_le        timestamptz NOT NULL DEFAULT now(),
    supprime_par       text,
    -- Passe a `true` quand le serveur a retire sa propre ligne. Tant que c'est
    -- faux, le registre local porte encore la ligne : le journal dit donc aussi
    -- CE QUI RESTE A FAIRE.
    serveur_aligne     boolean NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS app_affaire_supprimee_a_faire_idx
    ON public.app_affaire_supprimee (supprime_le)
    WHERE serveur_aligne = false;

COMMENT ON TABLE public.app_affaire_supprimee IS
    'LE JOURNAL DES SUPPRESSIONS ORDONNEES PAR L''APP. Il sert a DEUX choses : '
    'dire qui a supprime quoi et quand (il ne s''efface jamais), et apprendre au '
    'serveur local qu''il doit retirer sa propre ligne -- sans quoi son push la '
    'recreerait la nuit suivante. Ne concerne PAS les suppressions faites chez '
    'Hektor, que le balayage decouvre apres coup et dont la ligne est CONSERVEE, '
    'marquee present_in_hektor = false.';

COMMENT ON COLUMN public.app_affaire_supprimee.serveur_aligne IS
    'false = le registre local porte encore la ligne. C''est la liste de travail '
    'que `affaire_ledger.py` lit avant de pousser.';

ALTER TABLE public.app_affaire_supprimee ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies
                  WHERE schemaname = 'public' AND tablename = 'app_affaire_supprimee'
                    AND policyname = 'app_affaire_supprimee_read') THEN
    CREATE POLICY app_affaire_supprimee_read ON public.app_affaire_supprimee
      FOR SELECT TO authenticated USING (true);
  END IF;
END
$$;

-- ⚠ L'ECRITURE EST RESERVEE AU SERVICE : c'est le worker qui inscrit, apres la
--   preuve, et le serveur qui coche `serveur_aligne`. Personne d'autre.
GRANT ALL    ON TABLE public.app_affaire_supprimee TO service_role;
GRANT SELECT ON TABLE public.app_affaire_supprimee TO authenticated;
