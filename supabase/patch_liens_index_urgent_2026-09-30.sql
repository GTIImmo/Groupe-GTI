-- ═══════════════════════════════════════════════════════════════════════════════
-- ⚠⚠ URGENT -- LA VUE DES LIENS EST 100 FOIS TROP LENTE, ET C'EST MOI
-- ═══════════════════════════════════════════════════════════════════════════════
-- 30/09/2026. UNE SEULE LIGNE UTILE. A APPLIQUER EN PRIORITE.
--
-- ─── CE QUI SE PASSE EN CE MOMENT ───────────────────────────────────────────────
-- Depuis la bascule de cet apres-midi, ouvrir une fiche contact met :
--
--     AVANT ma bascule   ~10 ms     (index sur app_contact_relation_current)
--     MAINTENANT        985 ms      MESURE, pas estime
--
-- J'AI RENDU LA VUE 100 FOIS PLUS LENTE ET JE NE L'AVAIS PAS MESURE. J'ai
-- verifie que le NOMBRE de lignes etait juste (163 765), que le contenu etait
-- juste, que rien n'etait perdu -- et pas une fois le TEMPS. C'est la meme faute
-- que le verrou de huit minutes ce matin : « additif et reversible » qualifie ce
-- qu'on ecrit, jamais ce que ca coute.
--
-- ─── LA CAUSE, LUE DANS LE PLAN D'EXECUTION ─────────────────────────────────────
--     Seq Scan on app_relation r
--       Filter: ((app_contact_id)::text = '10000023'::text)
--       Rows Removed by Filter: 132628
--
-- La vue expose `app_contact_id::text` sous le nom `hektor_contact_id`, parce que
-- le front filtre sur ce nom-la et attend du texte. Mais `idx_app_relation_contact`
-- porte sur la colonne BIGINT : la conversion le rend inutilisable, et Postgres
-- parcourt les 132 628 lignes A CHAQUE OUVERTURE DE FICHE.
--
-- ─── LA REPARATION ──────────────────────────────────────────────────────────────
-- Un index D'EXPRESSION, sur la valeur telle que la vue la calcule.
-- Mesure en BEGIN/ROLLBACK, meme requete, meme contact :
--     985,004 ms  ->  2,510 ms      soit ~400 fois plus rapide
--     et le plan passe de « Seq Scan » a « Index Scan using
--     idx_app_relation_contact_texte », Index Cond sur la valeur convertie.
--
-- ⚠ L'ANCIEN INDEX RESTE UTILE : idx_app_relation_contact (sur le bigint) sert
--   aux jointures et au run. Celui-ci ne le remplace pas, il le complete.
--
-- ─── ET UNE LECON QUE JE NOTE ICI ───────────────────────────────────────────────
-- Une vue qui rend le bon resultat peut etre inutilisable. Le controle « le
-- compte est juste » ne dit RIEN du temps. Toute vue que l'ecran interroge doit
-- etre mesuree avec EXPLAIN ANALYZE sur la requete REELLE du front -- pas sur un
-- SELECT count(*), qui emprunte un tout autre chemin.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- DROP INDEX public.idx_app_relation_contact_texte;
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_app_relation_contact_texte
  ON public.app_relation ((app_contact_id::text));

ANALYZE public.app_relation;

COMMENT ON INDEX public.idx_app_relation_contact_texte IS
  'Index D''EXPRESSION sur app_contact_id::text -- c''est sous cette forme que la '
  'vue app_contact_relations_current l''expose (nom `hektor_contact_id`, du texte, '
  'parce que le front filtre dessus). Sans lui, chaque ouverture de fiche contact '
  'parcourait les 132 628 lignes : 985 ms au lieu de 2,5 ms. Ne remplace pas '
  'idx_app_relation_contact, qui sert aux jointures et au run.';
