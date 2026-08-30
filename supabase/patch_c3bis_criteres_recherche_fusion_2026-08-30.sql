-- =====================================================================
-- LES CRITÈRES D'UNE RECHERCHE SE FUSIONNENT, ILS NE SE REMPLACENT PLUS
-- Date : 2026-08-30
--
-- LE DÉFAUT. Les deux fonctions d'édition — négociateur **et** espace client —
-- écrivaient `criteres_json = app_search_criteres_from_input(v_search)`. Or
-- cette fonction ne sait construire que **quatre** sortes de critères :
-- équipements, DPE, marge de prix, salles de bain minimum.
--
-- Tout le reste de la liste venue d'Hektor était donc **effacé** à la première
-- modification : pondération de quartier, mitoyenneté, nombre de niveaux,
-- étages, particularités, surfaces de commerce.
--
-- ─────────────────────────────────────────────────────────────────────
-- ET LA SYNCHRO NE LE RÉPARAIT PAS — c'est le point que j'avais d'abord manqué,
-- et que Frédéric m'a fait vérifier en demandant « donc si je modifie une
-- recherche, les champs Hektor auraient été supprimés ? »
--
-- Éditer une recherche pose une ligne dans `app_search_pending`, et le pipeline
-- lit cette table pour savoir **ce qu'il ne doit pas écraser** (principe
-- « Supabase d'abord », voulu et juste). Mais pour les recherches cette ligne
-- n'est **jamais** effacée : elle ne disparaît qu'au terme d'un travail d'envoi
-- vers Hektor, et **C.3 a fermé cette porte le 24/08** — donc aucun travail
-- n'est jamais créé. La ligne reste pour toujours, et Hektor ne reprend jamais
-- la main.
--
-- Autrement dit : la perte était **immédiate et définitive**, pas différée à la
-- coupure comme je l'avais d'abord annoncé.
-- ─────────────────────────────────────────────────────────────────────
--
-- MESURE DU 30/08 : **1 045 recherches sur 10 910 (9,6 %)** portent au moins un
-- critère qui n'a ni colonne dédiée ni équivalent reconstructible par l'app.
-- Le plus fréquent est `ITEM_QUARTIER_PONDERATION` (979).
--
-- CE QUI NOUS A SAUVÉS : `app_search_pending` est **vide**. Aucune recherche n'a
-- jamais été éditée depuis l'app. Le chemin existait, personne ne l'avait
-- emprunté — **rien n'est perdu à ce jour**.
--
-- LE CORRECTIF. On fusionne : les critères que l'app ne sait pas produire sont
-- **conservés tels quels**, et seuls ceux qu'elle sait écrire sont remplacés.
-- Ainsi décocher un équipement le retire bien, sans emporter la pondération de
-- quartier avec lui.
--
-- Le modèle « au moins » n'est pas touché — **C.10 a eu raison de l'abandonner** :
-- la porte sortante fermée, l'app n'a plus à parler la langue d'Hektor.
--
-- ÉPROUVÉ sur une recherche réelle portant une pondération de quartier :
--     elle portait                10 critères
--     ancien comportement          2   → 8 effacés
--     après fusion                11   → rien de perdu, plus les nouveaux
--     ITEM_QUARTIER_PONDERATION   conservée
--
-- Appliqué en production via la migration `c3bis_criteres_recherche_fusion`.
-- Les deux fonctions d'édition sont recréées à l'identique, **une seule ligne
-- changée dans chacune** — voir la migration pour leur texte complet.
-- =====================================================================

create or replace function public.app_search_criteres_fusion(p_existant jsonb, p_search jsonb)
returns jsonb
language sql
immutable
as $function$
  with app_ecrit(cle) as (values
    ('ITEM_GARAGE_PARKING'),('ITEM_TERRASSE'),('ITEM_BALCON'),('ITEM_PISCINE'),
    ('ITEM_ASCENSEUR'),('ITEM_CHEMINEE'),('ITEM_CAVE'),('ITEM_DOUBLE_VITRAGE'),
    ('ITEM_PLAIN_PIED'),('ITEM_GRENIER_COMBLE'),('ITEM_ACCES_HANDI'),
    ('ITEM_TERRAIN_CONSTRUCTIBLE'),('ITEM_TERRAIN_ARBORE'),('ITEM_TERRAIN_PISCINABLE'),
    ('ITEM_TERRAIN_VIABILISE'),('ITEM_DPE_CONS_LETTER'),('ITEM_PRIX_MARGE'),('ITEM_SDB_SDE_MIN')
  ),
  conserves as (
    select c
    from jsonb_array_elements(
           case when jsonb_typeof(p_existant) = 'array' then p_existant else '[]'::jsonb end) c
    where nullif(trim(coalesce(c->>'cle','')), '') is not null
      and (c->>'cle') not in (select cle from app_ecrit)
  ),
  neufs as (
    select c from jsonb_array_elements(public.app_search_criteres_from_input(p_search)) c
  )
  select coalesce(jsonb_agg(c order by c->>'cle'), '[]'::jsonb)
  from (select c from conserves union all select c from neufs) x;
$function$;

comment on function public.app_search_criteres_fusion(jsonb, jsonb) is
  'Fusionne les criteres d''une recherche : conserve ceux que l''app ne sait pas produire, '
  'remplace ceux qu''elle sait ecrire. Pose le 30/08 apres mesure : sans elle, une edition '
  'effacait definitivement 9,6 % des criteres, la synchro ne reprenant jamais la main.';

-- Les deux fonctions d'edition changent d'UNE ligne :
--     criteres_json = public.app_search_criteres_from_input(v_search)
--  -> criteres_json = public.app_search_criteres_fusion(cur.criteres_json, v_search)
-- Leur texte complet est dans la migration c3bis_criteres_recherche_fusion.
