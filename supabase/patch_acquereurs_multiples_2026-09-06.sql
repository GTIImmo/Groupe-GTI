-- ═══════════════════════════════════════════════════════════════════════════════
-- 2.5 + 2.6 — L'ACQUEREUR SE DESIGNE, ET ILS PEUVENT ETRE PLUSIEURS   06/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de ce qui est deploye (migrations
-- status_optimistic_nomme_ses_acquereurs et status_optimistic_ecrit_les_acquereurs).
--
-- ─── LE TROU COMBLE ICI ───
-- Le RPC ecrivait hektor_acquereur_id et app_contact_id, mais NI acquereur_json
-- NI acquereurs_json. Une transaction creee depuis l'app restait donc ANONYME a
-- l'ecran jusqu'au run de nuit -- alors que 1.8 (05/09) venait justement de faire
-- en sorte que la rubrique Affaires les nomme TOUS. L'ecran aurait propose de
-- choisir plusieurs acquereurs, puis n'en aurait affiche aucun.
--
-- ⚠ ON N'INVENTE AUCUN NOM : les fiches viennent de app_contact_current, par leur
--   identifiant Hektor. Un contact inconnu ne produit pas de ligne.
-- ⚠ LE RUN REPREND LA MAIN : les deux colonnes sont dans son ON CONFLICT DO
--   UPDATE. Ce qu'on ecrit ici ne vaut que pour la fenetre d'attente.
-- ⚠ LE PRINCIPAL RESTE EN TETE : buyer_contact_id, celui que le worker envoie a
--   Hektor. La liste ne le remplace pas, elle l'entoure.
--
-- AMPLEUR MESUREE LE 04/09 : 1 811 compromis sur 10 581 (17,1 %) et 566 ventes
-- sur 7 609 (7,4 %) portent plusieurs acquereurs. Un couple qui achete est la
-- norme, pas le cas limite.

create or replace function public.app_acquereurs_json(p_ids text[])
returns jsonb
language sql
stable
security definer
set search_path to 'public'
as $function$
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        c.hektor_contact_id,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      )
      order by array_position(p_ids, c.hektor_contact_id)
    ),
    '[]'::jsonb)
  from app_contact_current c
  where c.hektor_contact_id = any(p_ids);
$function$;

comment on function public.app_acquereurs_json(text[]) is
  'Fiches des acquereurs, dans l''ordre demande, pour app_affaire_ledger (2.6, '
  '06/09/2026). Un contact inconnu ne produit pas de ligne : on n''invente pas.';

grant execute on function public.app_acquereurs_json(text[])
  to anon, authenticated, service_role;

-- ─── L'APPELANT ───
-- app_change_annonce_status_optimistic a ete redeployee (meme signature, donc
-- GRANT conserves) avec, en plus :
--     v_acquereurs  le principal en tete, puis buyer_contact_ids sans doublon
--     v_acq_json    public.app_acquereurs_json(v_acquereurs)
--     l'INSERT porte desormais acquereur_json (le principal) et acquereurs_json
--     le retour porte 'acquereurs' : combien ont ete nommes
-- Sa definition complete reste celle de la base : on ne recopie pas ici une
-- fonction de 140 lignes qu'il faudrait ensuite tenir a jour deux fois.
