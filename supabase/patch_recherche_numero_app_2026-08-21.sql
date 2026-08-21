-- =====================================================================
-- Le numero de recherche, pose EN DOUBLURE
-- Date : 2026-08-21
-- Applique en prod via la migration `recherche_numero_app_doublure`
--
-- LE DEFAUT. Le nom d'une recherche, `contact_search_key`, est le hache de son
-- CONTENU (`build_contacts_layer.py:827`, seul endroit du projet qui le fabrique).
-- Le contenu change -> le nom change -> au retour de nuit l'app ne reconnait plus
-- la ligne : elle en cree une neuve et supprime l'ancienne. Tout ce qui pendait
-- dessous tombe -- propositions, relances, retours acquereur, envois,
-- rapprochements. C'est l'origine des 1 373 orphelins reparees le 20/08.
--
-- LE FAIT QUI DECIDE : il y a DEJA deux haches sur chaque recherche.
-- Preuve dans phase2.sqlite, table app_contact_supabase_push_state :
--
--    UNE RECHERCHE  nom : 001697ad4134b105219d5549   empreinte : 742548023fb0...
--    UN CONTACT     nom : 100030                      empreinte : 03dd0f0f5e96...
--
-- L'empreinte de contenu (`stable_payload_hash`) est calculee et stockee sur
-- CHAQUE recherche -- et jamais lue. La boucle de detection
-- (`push_contacts_to_supabase.py:206-211`) fait
--    known_hashes.get(row_key(row)) != stable_payload_hash(row)
-- or pour une recherche `row_key` EST le hache du contenu : le nom change avec le
-- contenu, `.get()` ne trouve rien, la ligne est traitee comme neuve et l'ancienne
-- comme disparue.
--
-- > Le premier hache fait mal le travail du second. Le second, qui le ferait bien,
-- > n'est jamais consulte.
--
-- app_contact_current prouve que l'autre voie marche : son nom est un NUMERO, ses
-- modifications faites dans Hektor remontent en mise a jour SUR PLACE, meme boucle,
-- meme empreinte. Il n'y a rien a construire -- il y a un doublon a retirer.
--
-- POURQUOI LA PAIRE (contact, rang) EST FIABLE. Hektor n'efface jamais une
-- recherche : meme le bouton "Supprimer" de l'app appelle archiveHektorContactSearch
-- -> modifDateArchiveCritere, qui pose une date d'archivage
-- (console_job_worker.js:11878-11890, :11918). L'archivee garde sa place dans la
-- liste, donc le rang ne glisse pas.
--
-- EN DOUBLURE -- et c'est le point de methode, arrete par Frederic le 20/08.
-- La colonne est posee A COTE, sans rien lui confier : `contact_search_key` reste la
-- cle et commande tout. On observera pendant des SEMAINES si le numero reste colle a
-- la bonne recherche, et on ne basculera qu'ensuite.
--   « poser le numero a cote / observer / basculer une fois qu'il a fait ses preuves »
-- C'est l'inverse de ce qui a ete fait pour les annonces : app_dossier_id a derive de
-- mars a juin precisement parce que personne ne l'observait.
--
-- PAS D'INDEX UNIQUE POUR L'INSTANT : pendant l'observation, un doublon doit lever une
-- sentinelle, pas faire tomber le run de 05:30. L'index viendra a la bascule.
--
-- COTE LOCAL, le numero vit dans une table A PART, `app_search_registry`, jamais videe.
-- Raison : la couche des recherches a DEUX chemins d'ecriture, et l'un d'eux
-- (`replace_table_rows`, run complet de 05:30) VIDE toute la table. Un numero range
-- la-dedans ne survivrait pas. Les deux chemins appellent `assign_search_ids`.
--
-- VERIFIE le 21/08 : 76 839 recherches locales numerotees (registre 1..76 839,
-- 0 doublon) ; reconstruction d'un contact -> numeros identiques ; 10 744 lignes
-- poussees dans Supabase, 0 sans numero, 0 doublon.
-- Sentinelles `data.recherche_sans_numero` et `data.recherche_numero_double`, seuil 0.
-- =====================================================================

alter table public.app_contact_search_current
  add column if not exists app_search_id bigint;

comment on column public.app_contact_search_current.app_search_id is
  'Numero de recherche distribue par le serveur local. EN DOUBLURE depuis le 21/08 : contact_search_key reste la cle.';

create index if not exists idx_app_contact_search_app_id
  on public.app_contact_search_current (app_search_id);

-- Les deux sentinelles d'observation. Elles SONT le dispositif : c'est leur silence,
-- semaine apres semaine, qui autorisera la bascule.
create or replace view public.app_recherches_sans_numero as
  select contact_search_key, hektor_contact_id, search_index, is_active
    from public.app_contact_search_current
   where app_search_id is null;

create or replace view public.app_recherches_numero_en_double as
  select app_search_id, count(*) as combien,
         string_agg(hektor_contact_id || '/' || search_index, ', ') as porteuses
    from public.app_contact_search_current
   where app_search_id is not null
   group by app_search_id
  having count(*) > 1;

-- --- Retour arriere ----------------------------------------------------
-- Rien ne depend de cette colonne : la supprimer des deux cotes suffit, et
-- `app_search_registry` peut rester (elle ne gene personne). C'est tout l'interet
-- d'une doublure.
