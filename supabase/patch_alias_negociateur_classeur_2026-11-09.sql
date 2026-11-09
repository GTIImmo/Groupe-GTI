-- ============================================================================
-- LA TABLE D'ALIAS DES NEGOCIATEURS DU CLASSEUR -- 09/11/2026
--
-- ⭐ DEJA APPLIQUEE en production le 09/11/2026, avec l'accord explicite de
--   Frederic (« Go »). Ce fichier est la TRACE : il est rejouable sans danger
--   (create if not exists + on conflict do nothing).
--
-- A QUOI ELLE SERT : le classeur Sheet nomme certaines personnes autrement que
-- notre registre. Sans correspondance, le rattrapage ajoute la meme personne
-- DEUX FOIS et COUPE SA COMMISSION EN DEUX -- sur 282 cases mesurees le 09/11
-- (163 pour Aline VALETTE, 119 pour Lucie DECHANDON).
--
-- ⛔ ELLE NE PORTE QUE DES DECISIONS HUMAINES. Les ecarts d'ECRITURE (une
--   particule qui perd son espace : DIMARIA pour DI MARIA) sont DEJA traites
--   par le code depuis le 29/10 -- `mots_du_nom()` ajoute les formes collees, et
--   la mesure du 09/11 l'a confirme : DIMARIA rencontre « Magali DI MARIA ».
--   ⚠ J'avais annonce qu'il fallait coder cette normalisation : C'ETAIT FAUX,
--     elle existait. Je l'avais mesuree avec MA fonction au lieu de la vraie.
--
-- ⚠ CE QUI RESTE VRAI ET NON TRAITE : l'APPARIEUR (`apparier_classeur.py`) n'a
--   PAS la meme fonction de noms que le rapport. Sa `mots_propres()` ne colle
--   pas les mots separes par un espace, donc « DIMARIA » n'y rencontre pas
--   « DI MARIA » (verifie le 09/11). Deux scripts, deux facons de lire un nom.
--   ⛔ NON CORRIGE : toucher la fonction de noms de l'apparieur, c'est toucher
--     le coeur du gel. Demande une mesure de non-regression sur les 4 679 liens
--     et l'accord de Frederic.
--
-- ⛔⛔ POURQUOI LA CLE EST `app_personne_id` ET PAS UN NUMERO HEKTOR :
--   un negociateur a DEUX numeros. Les alias etaient codes en dur avec « 68 »
--   et « 178 », qui sont des `hektor_user_id` -- et le code les comparait bien
--   a des hektor_user_id (l. 556 du rapport), donc IL ETAIT JUSTE.
--   MAIS le nombre seul est AMBIGU : pris pour des `hektor_negociateur_id`,
--   68 designe Nadege PEYRARD et 178 designe David BADIER -- DEUX AUTRES
--   PERSONNES (temoin inverse mesure le 09/11). `app_personne_id` n'a qu'un
--   seul sens possible, et le `hektor_user_id` s'en DEDUIT par les fiches.
-- ============================================================================

create table if not exists public.app_classeur_alias_negociateur (
  texte_classeur   text    primary key,
  app_personne_id  bigint  not null
                   references public.app_negociateur_personne(app_personne_id),
  nom_chez_nous    text    not null,
  cases_vues       integer,
  decide_le        date    not null default current_date,
  decide_par       text    not null,
  note             text,
  constraint alias_texte_non_vide check (btrim(texte_classeur) <> ''),
  constraint alias_nom_non_vide   check (btrim(nom_chez_nous)  <> '')
);

comment on table public.app_classeur_alias_negociateur is
  'Noms de negociateurs du classeur Sheet qui designent une personne de notre '
  'registre sous un AUTRE nom. Lue par l''apparieur, le rapport de gel et le '
  'rattrapage. Ne porte QUE des decisions humaines ; les ecarts d''ecriture '
  '(espaces de particule) sont traites par le code.';

comment on column public.app_classeur_alias_negociateur.texte_classeur is
  'Le nom TEL QU''ECRIT dans le classeur, sans retouche.';
comment on column public.app_classeur_alias_negociateur.app_personne_id is
  'La personne de app_negociateur_personne. ⛔ JAMAIS un hektor_user_id ni un '
  'hektor_negociateur_id : un negociateur a DEUX numeros, et les confondre '
  'designe quelqu''un d''autre.';
comment on column public.app_classeur_alias_negociateur.cases_vues is
  'Combien de cases du classeur portaient ce texte le jour de la decision. '
  'Sert de temoin : si ce nombre s''ecroule, le classeur a change de forme.';

-- ── LES DROITS. ⛔ `revoke from public` NE FERME PAS `authenticated` :
--   chaque role se revoque nommement (lecon du projet).
alter table public.app_classeur_alias_negociateur enable row level security;
revoke all on table public.app_classeur_alias_negociateur from anon, authenticated;

-- ── LES DEUX ALIAS, confirmes par Frederic le 29/10/2026, reposes le 09/11
insert into public.app_classeur_alias_negociateur
  (texte_classeur, app_personne_id, nom_chez_nous, cases_vues,
   decide_le, decide_par, note)
values
  ('GIRAUD', 1000058, 'Aline VALETTE', 163, '2026-11-09', 'Frederic GERPHAGNON',
   'Confirme par Frederic le 29/10/2026. Le classeur ecrit GIRAUD, notre '
   'registre Aline VALETTE (fiche 1000110, hektor_negociateur_id 42, '
   'hektor_user_id 68 -- c''est ce 68 qui etait code en dur et qui preterait '
   'a confusion avec le negociateur 68, Nadege PEYRARD).'),
  ('ALVES MENDES', 1000128, 'Lucie DECHANDON', 119, '2026-11-09', 'Frederic GERPHAGNON',
   'Confirme par Frederic le 29/10/2026. Le classeur ecrit ALVES MENDES, notre '
   'registre Lucie DECHANDON (fiche 1000183, hektor_negociateur_id 135, '
   'hektor_user_id 178 -- c''est ce 178 qui etait code en dur et qui preterait '
   'a confusion avec le negociateur 178, David BADIER).')
on conflict (texte_classeur) do nothing;
