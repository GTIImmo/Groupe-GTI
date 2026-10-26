-- Les parties d'UNE ligne du registre `l` (une transaction). Utilisé par la fonction de recalcul et par les essais.
-- Une liste peut être une LISTE, un OBJET SEUL (une offre) ou rien : les trois formes (mémoire « liste OU objet seul »).
    SELECT l.app_affaire_id,
           'acquereur'::text AS role,
           x.ord::int AS rang,
           CASE WHEN (x.v ->> 'app_contact_id') ~ '^[0-9]+$' THEN (x.v ->> 'app_contact_id')::bigint END AS app_contact_id,
           nullif(btrim(coalesce(x.v ->> 'id', '')), '') AS hektor_contact_id,
           (x.ord = 1) AS est_principal,
           (btrim(coalesce(x.v ->> 'nom', '')) = '') AS fiche_sans_nom,
           coalesce(l.present_in_hektor, false) AS transaction_presente
      FROM jsonb_array_elements(CASE jsonb_typeof(l.acquereurs_json)
                                     WHEN 'array'  THEN l.acquereurs_json
                                     WHEN 'object' THEN jsonb_build_array(l.acquereurs_json)
                                     ELSE '[]'::jsonb END) WITH ORDINALITY x(v, ord)
     WHERE jsonb_typeof(x.v) = 'object'
    UNION ALL
    -- le principal par ses colonnes, quand la liste est vide (642 listes vides, dont certaines avec un principal)
    SELECT l.app_affaire_id, 'acquereur', 1, l.app_contact_id, nullif(btrim(coalesce(l.hektor_acquereur_id, '')), ''),
           true, false, coalesce(l.present_in_hektor, false)
     WHERE (l.app_contact_id IS NOT NULL OR nullif(btrim(coalesce(l.hektor_acquereur_id, '')), '') IS NOT NULL)
       AND (CASE jsonb_typeof(l.acquereurs_json) WHEN 'array' THEN jsonb_array_length(l.acquereurs_json)
                                                  WHEN 'object' THEN 1 ELSE 0 END) = 0
    UNION ALL
    SELECT l.app_affaire_id, 'vendeur', x.ord::int,
           CASE WHEN (x.v ->> 'app_contact_id') ~ '^[0-9]+$' THEN (x.v ->> 'app_contact_id')::bigint END,
           nullif(btrim(coalesce(x.v ->> 'id', '')), ''),
           false, (btrim(coalesce(x.v ->> 'nom', '')) = ''), coalesce(l.present_in_hektor, false)
      FROM jsonb_array_elements(CASE jsonb_typeof(l.mandants_json)
                                     WHEN 'array'  THEN l.mandants_json
                                     WHEN 'object' THEN jsonb_build_array(l.mandants_json)
                                     ELSE '[]'::jsonb END) WITH ORDINALITY x(v, ord)
     WHERE jsonb_typeof(x.v) = 'object'
    UNION ALL
    -- les notaires : colonnes à NOTRE numéro (pièce 3) ; celui de Hektor retrouvé par l'annuaire.
    -- ⛔ LA CONVERSION EST PROTÉGÉE PAR UN CASE, ET C'EST INDISPENSABLE : la fonction est DÉPLIÉE dans la requête
    --   (pas de search_path fixé), et Postgres n'évalue pas le WHERE avant la conversion -- une colonne vide faisait
    --   « invalid input syntax for type bigint » DANS LE DÉCLENCHEUR (essai du 26/10, 13:25, transaction annulée).
    SELECT l.app_affaire_id, 'notaire_acquereur', 1, CASE WHEN coalesce(l.notaire_acquereur_id, '') ~ '^[0-9]+$' THEN l.notaire_acquereur_id::bigint END,
           (SELECT c.hektor_target_id FROM public.app_contact_current c WHERE c.hektor_contact_id = l.notaire_acquereur_id),
           false, false, coalesce(l.present_in_hektor, false)
     WHERE coalesce(l.notaire_acquereur_id, '') ~ '^[0-9]+$'
    UNION ALL
    SELECT l.app_affaire_id, 'notaire_vendeur', 1, CASE WHEN coalesce(l.notaire_mandant_id, '') ~ '^[0-9]+$' THEN l.notaire_mandant_id::bigint END,
           (SELECT c.hektor_target_id FROM public.app_contact_current c WHERE c.hektor_contact_id = l.notaire_mandant_id),
           false, false, coalesce(l.present_in_hektor, false)
     WHERE coalesce(l.notaire_mandant_id, '') ~ '^[0-9]+$'
