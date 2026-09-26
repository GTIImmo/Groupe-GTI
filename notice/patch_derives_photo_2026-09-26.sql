-- G.11 -- OU SONT LES DERIVES D'UNE PHOTO                              26/09/2026
--
-- Deux colonnes seulement, et elles ne remplacent RIEN : le master reste sur le
-- serveur, l'index garde ses colonnes storage_* pour lui.
--
-- derives_generes_le NULL = pas encore de derives -> les 48 points d'affichage
-- retombent sur l'adresse Hektor (le repli de G.15). C'est ce qui permet de basculer
-- progressivement, sans jamais d'ecran vide.
--
-- ⚠ On ne stocke PAS l'URL complete mais le CHEMIN dans le coffre : le nom de domaine
-- reste connu d'un seul endroit. L'adresse publiee, elle, ne changera jamais (P-1).

alter table public.app_console_photo
  add column if not exists derives_json       jsonb,
  add column if not exists derives_generes_le timestamptz;

comment on column public.app_console_photo.derives_json is
  'Les derives publics : {"w400":{"chemin":"...","octets":N},"w1600":{...}}. Chemin '
  'dans le coffre gti-photo, PAS une URL -- le domaine reste connu d''un seul endroit.';

comment on column public.app_console_photo.derives_generes_le is
  'Quand les derives ont ete fabriques. NULL = aucun -> l''affichage retombe sur '
  'l''adresse Hektor (repli de G.15). Sert aussi a trouver le reste a faire (G.13).';

-- G.13 doit trouver « les photos vivantes sans derives » sans balayer 436 524 lignes.
create index if not exists app_console_photo_sans_derives_idx
  on public.app_console_photo (app_dossier_id)
  where derives_generes_le is null and present_in_hektor;
