-- =====================================================================
-- Le numero Hektor d'une annonce a le droit d'etre vide
-- Applique en production le 20/08/2026 (tache 3 du plan).
--
-- POURQUOI. Une annonce creee dans l'app n'a pas encore de numero Hektor : il
-- n'arrive qu'apres la reponse du worker. Tant que la colonne est obligatoire, la
-- creation app-first est mecaniquement impossible -- la ligne ne peut pas exister.
--
-- PERIMETRE : 2 tables sur les 26 qui portent hektor_annonce_id en NON NUL.
-- Les 24 autres decrivent des objets qui n'existent pas encore au moment de la
-- creation (archives, brouillons, documents, photos, diffusion, RDV, registre...)
-- ou l'ont dans une cle primaire. Dans les deux cas : rien a changer.
--
-- CE QUE CA CHANGE AUJOURD'HUI : rien. C'est une AUTORISATION, pas un comportement.
--   - les 13 211 annonces gardent leur numero ;
--   - le worker lit le numero dans la charge du travail, pas dans la table ;
--   - le front joint par app_dossier_id.
-- Rien ne produira de valeur vide avant la tache 22 (la creation ecrit la vraie fiche).
--
-- CE QUE CA COUTE : la base ne refuse plus une fiche sans numero. Un bug pourrait
-- desormais en inserer une EN SILENCE -> d'ou la vue de surveillance, attendu 0.
-- =====================================================================

alter table public.app_dossier_current        alter column hektor_annonce_id drop not null;
alter table public.app_dossier_detail_current alter column hektor_annonce_id drop not null;

create or replace view public.app_annonces_sans_numero_hektor as
select 'fiche' as objet, d.app_dossier_id, d.numero_dossier, d.titre_bien, d.refreshed_at
  from public.app_dossier_current d
 where d.hektor_annonce_id is null
union all
select 'detail', x.app_dossier_id, null, null, null
  from public.app_dossier_detail_current x
 where x.hektor_annonce_id is null;

-- Verification apres application (constate le 20/08) :
--   fiche accepte le vide : YES | detail : YES
--   annonces : 13 211 | fiches sans numero : 0 | vue : 0
--
-- Retour arriere (possible tant qu'aucune valeur vide n'existe) :
--   alter table public.app_dossier_current        alter column hektor_annonce_id set not null;
--   alter table public.app_dossier_detail_current alter column hektor_annonce_id set not null;
--   drop view if exists public.app_annonces_sans_numero_hektor;
