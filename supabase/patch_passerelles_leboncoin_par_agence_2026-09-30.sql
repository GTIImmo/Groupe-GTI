-- ═══════════════════════════════════════════════════════════════════════════════
-- LA BASCULE LEBONCOIN : UNE PASSERELLE PAR AGENCE            30/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage de service. Aucun deploiement. 17 lignes UPDATE.
--
-- ─── CE QUI S'EST PASSE ─────────────────────────────────────────────────────────
-- Hektor a bascule LeBonCoin AUJOURD'HUI, entre le run de nuit (04:21) et 16h45.
-- Le regroupement d'agences est supprime : les 9 passerelles groupees sont
-- remplacees par 17 individuelles (45 a 61), une par agence.
-- Seule la n° 35 survit, avec 3 annonces residuelles -- elle se vide.
--
-- Notre carte de routage pointe donc sur des numeros MORTS pour les 17 agences.
-- Tant qu'elle n'est pas corrigee, un clic « diffuser » part dans le vide.
--
-- ⚠ ET CE N'ETAIT PAS UNE SURPRISE TOTALE : la n° 37 (Montbrison + Saint-Just)
--   etait deja morte depuis le 03/04, renumerotee 44. Personne ne l'a vu pendant
--   SIX MOIS -- 1 795 annonces routees dans le vide. C'etait le premier cas d'une
--   serie qui vient de se produire en entier.
--
-- ─── D'OU VIENNENT CES 17 NUMEROS : HEKTOR LES A DITS, ON NE LES A PAS DEDUITS ──
-- `GET /Api/Annonce/ListPasserelles/?idAnnonce=<temoin>` rend la configuration
-- portails de L'AGENCE du bien : numero ET identifiant du portail.
-- Un appel par agence, le 30/09 vers 17h15 :
--     17 agences interrogees · 17 repondues · 0 muette
--     17 numeros DISTINCTS · 17 identifiants DISTINCTS
--     -> « un numero par agence » n'est pas une hypothese, c'est mesure
--
-- ⚠ DEUX PIEGES PAYES AVANT D'OBTENIR CE RELEVE :
--   ① ListPasserelles n'ouvre que sur un bien DIFFUSABLE. Un temoin pris au
--      hasard rend `data: []` -- 18 agences sur 19 ont d'abord repondu vide, ce
--      qui ressemblait a « pas de passerelle » et n'etait qu'un mauvais temoin.
--   ② LE TEMOIN NE DOIT PAS VENIR DE LEBONCOIN, sinon la reponse est fabriquee
--      par la question. Chaque temoin est un bien diffuse sur un AUTRE portail.
--
-- ⭐ FREDERIC AVAIT RAISON : Firminy et Saint-Etienne partageaient la n° 39.
--    Ils ont desormais 48 et 49. Verifie, agence par agence.
--
-- ─── CE QUI NE BOUGE PAS ────────────────────────────────────────────────────────
-- `bienicidirect` : les 17 lignes sont JUSTES, verifiees une par une par le meme
-- appel. Ce patch n'y touche pas. Les flux reseau (etreproprio 19, paper 20,
-- superimmo 21) ne sont pas dans cette carte et n'y entrent pas ici.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- Les anciens numeros sont ecrits dans la colonne `note` de chaque ligne
-- corrigee (« LBC 2026-09-30 : etait NN »). Pour revenir, relire cette note.
-- Mais revenir n'aurait aucun sens : les anciens numeros n'existent plus.
--
-- ─── LE CONTROLE, APRES ─────────────────────────────────────────────────────────
--     python phase2/checks/passerelle_par_agence.py --par-agence
--   doit rendre « lignes de carte a corriger : 0 » et sortir en code 0.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- Le releve du 30/09/2026 17h15, tel que Hektor l'a rendu.
-- L'identifiant est garde pour la trace : c'est le compte LeBonCoin de l'agence.
CREATE TEMP TABLE releve_lbc (agence text, numero text, identifiant text) ON COMMIT DROP;
INSERT INTO releve_lbc (agence, numero, identifiant) VALUES
  ('Groupe GTI Ambert',                  '45', '285776'),
  ('Groupe GTI COURPIERE',               '46', '496094'),
  ('Groupe GTI ANNONAY',                 '47', '285501'),
  ('Groupe GTI Firminy',                 '48', '122698'),
  ('Groupe GTI Saint-Etienne',           '49', '496104'),
  ('Groupe GTI Montbrison',              '50', '285958'),
  ('Groupe GTI Saint-Just-Saint-Rambert','51', '496110'),
  ('Groupe GTI Dunières',                '52', '496111'),
  ('Groupe GTI Tence',                   '53', '285755'),
  ('Groupe GTI BRIOUDE',                 '54', '285965'),
  ('Groupe GTI Issoire',                 '55', '496066'),
  ('Groupe GTI Craponne-sur-Arzon',      '56', '285991'),
  ('Groupe GTI Saint-Bonnet-le-Château', '57', '496075'),
  ('Groupe GTI Monistrol sur Loire',     '58', '285821'),
  ('Groupe GTI Saint-Didier-en-Velay',   '59', '496092'),
  ('Groupe Gti Le Puy en Velay',         '60', '285699'),
  ('Groupe GTI Yssingeaux',              '61', '496125');

-- ⛔ GARDE-FOU 1 : le releve doit couvrir EXACTEMENT les agences de la carte.
--   Un nom qui ne tombe pas en face (accent, casse, agence creee depuis) ferait
--   un UPDATE silencieux sur zero ligne -- et on croirait avoir repare.
DO $$
DECLARE manquantes text; intruses text;
BEGIN
  SELECT string_agg(t.agence_nom, ', ') INTO manquantes
    FROM public.app_diffusion_agency_target t
   WHERE t.portal_key = 'leboncoinDirect' AND COALESCE(t.is_active,1) = 1
     AND NOT EXISTS (SELECT 1 FROM releve_lbc r WHERE r.agence = t.agence_nom);
  SELECT string_agg(r.agence, ', ') INTO intruses
    FROM releve_lbc r
   WHERE NOT EXISTS (SELECT 1 FROM public.app_diffusion_agency_target t
                      WHERE t.agence_nom = r.agence AND t.portal_key = 'leboncoinDirect');
  IF manquantes IS NOT NULL THEN
    RAISE EXCEPTION 'Agences de la carte absentes du releve : %', manquantes;
  END IF;
  IF intruses IS NOT NULL THEN
    RAISE EXCEPTION 'Agences du releve absentes de la carte : %', intruses;
  END IF;
END $$;

-- ⛔ GARDE-FOU 2 : un numero ne sert qu'UNE agence. C'est tout l'objet de la
--   bascule ; si deux agences recevaient le meme, le releve serait faux.
DO $$
DECLARE doublons text;
BEGIN
  SELECT string_agg(numero, ', ') INTO doublons
    FROM (SELECT numero FROM releve_lbc GROUP BY numero HAVING count(*) > 1) d;
  IF doublons IS NOT NULL THEN
    RAISE EXCEPTION 'Numeros partages par plusieurs agences : %', doublons;
  END IF;
END $$;

-- LA CORRECTION. L'ancien numero part dans `note` : la trace vit avec la ligne.
UPDATE public.app_diffusion_agency_target t
   SET hektor_broadcast_id = r.numero,
       note = 'Flux par agence (LeBonCoin ' || r.identifiant || '). '
              || 'Bascule du 30/09/2026 : etait ' || t.hektor_broadcast_id
              || ', releve chez Hektor par ListPasserelles.',
       updated_at = now()
  FROM releve_lbc r
 WHERE t.agence_nom = r.agence
   AND t.portal_key = 'leboncoinDirect'
   AND t.hektor_broadcast_id IS DISTINCT FROM r.numero;

-- ⛔ GARDE-FOU 3 : apres l'ecriture, la carte doit etre EXACTEMENT le releve.
DO $$
DECLARE restes int; distincts int;
BEGIN
  SELECT count(*) INTO restes
    FROM public.app_diffusion_agency_target t JOIN releve_lbc r ON r.agence = t.agence_nom
   WHERE t.portal_key = 'leboncoinDirect' AND t.hektor_broadcast_id <> r.numero;
  IF restes > 0 THEN
    RAISE EXCEPTION 'Apres correction, % ligne(s) ne correspondent toujours pas', restes;
  END IF;
  SELECT count(DISTINCT hektor_broadcast_id) INTO distincts
    FROM public.app_diffusion_agency_target
   WHERE portal_key = 'leboncoinDirect' AND COALESCE(is_active,1) = 1;
  IF distincts <> 17 THEN
    RAISE EXCEPTION 'Attendu 17 numeros LeBonCoin distincts, trouve %', distincts;
  END IF;
END $$;

-- ─── ET LE DERNIER RESTE, QUI PASSE AVANT LA CARTE ──────────────────────────────
-- ⚠ `app_diffusion_target` porte des cibles PAR BIEN, et `_run_apply` les lit
--   EN PREMIER : si un bien en a, la carte des agences n'est meme pas consultee.
--   Corriger la carte sans corriger celles-ci laisserait une porte ouverte.
--
-- 5 lignes leboncoinDirect y subsistent, des essais d'avril/mai :
--     4 sur des biens qui ne sont plus au parc, toutes en `disabled` -> inoffensives
--     1 SUR UN BIEN VIVANT : V670062151 (Tence), passerelle 43, etat « enabled »
--       -> elle enverrait ce bien sur une passerelle MORTE, malgre la carte corrigee
--
-- On ne touche QUE les lignes dont l'agence est connue ET le numero perime.
UPDATE public.app_diffusion_target t
   SET hektor_broadcast_id = r.numero,
       updated_at = now()
  FROM public.app_dossiers_current d, releve_lbc r
 WHERE d.app_dossier_id = t.app_dossier_id
   AND r.agence = d.agence_nom
   AND t.portal_key = 'leboncoinDirect'
   AND t.hektor_broadcast_id IS DISTINCT FROM r.numero;

-- ⛔ GARDE-FOU 4 : plus aucune cible VIVANTE ne doit pointer hors du releve.
DO $$
DECLARE restants text;
BEGIN
  SELECT string_agg(d.numero_dossier || ' (n° ' || t.hektor_broadcast_id || ')', ', ')
    INTO restants
    FROM public.app_diffusion_target t
    JOIN public.app_dossiers_current d ON d.app_dossier_id = t.app_dossier_id
   WHERE t.portal_key = 'leboncoinDirect'
     AND t.hektor_broadcast_id NOT IN (SELECT numero FROM releve_lbc);
  IF restants IS NOT NULL THEN
    RAISE EXCEPTION 'Cibles par bien encore sur une passerelle perimee : %', restants;
  END IF;
END $$;

COMMIT;

-- ─── A LIRE APRES LE COMMIT (doit rendre 17 lignes, toutes differentes) ────────
-- SELECT agence_nom, hektor_broadcast_id, note
--   FROM public.app_diffusion_agency_target
--  WHERE portal_key = 'leboncoinDirect' ORDER BY hektor_broadcast_id::int;
