-- ═══════════════════════════════════════════════════════════════════════════════
-- LOT 1a — LA COMMISSION ET SA CHARGE, DES L'OFFRE                 16/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage, aucun deploiement. Idempotent (re-collable sans risque).
--
-- ⚠ CE PATCH VIENT EN PREMIER, AVANT LE CODE LOCAL. Le run redescend ces
--   colonnes depuis Supabase apres le push (`rattacher_chaines_et_redescendre`,
--   affaire_ledger.py:1314) : si elles n'existent pas encore la-haut, cette
--   lecture echoue. Supabase d'abord, le local ensuite.
--
-- ─── POURQUOI ───────────────────────────────────────────────────────────────────
-- Demande de Frederic, 14/10 : saisir la commission ET savoir qui la paie, DES
-- L'OFFRE. Mesure du 14/10 qui l'a motivee :
--     la commission a l'offre   0 sur 11 182 chez nous  ·  22 sur 22 dans le classeur
--     la charge                 ne se deduit pas : sur 25 lignes ou le classeur dit
--                               « Acquereur », 13 sont rangees cote vendeur chez Hektor
-- Autrement dit : le classeur de Delphine sait deux choses que l'app ignore.
--
-- ─── CLASSE A : CE QUE CA VEUT DIRE, ET LES TROIS CONDITIONS ───────────────────
-- Hektor n'a AUCUNE destination pour ces trois valeurs a l'offre. Zero conflit
-- possible : il n'a rien a dire. Elles sont donc ECRITES PAR L'APP SEULE, dans
-- Supabase. Pour que ca tienne, il faut les TROIS conditions a la fois :
--   ① ici : les colonnes existent dans Supabase            <- CE PATCH
--   ② dans `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` : le push ne les envoie pas,
--      sinon la valeur LOCALE (vide) ecraserait celle de Supabase
--   ③ hors du `ON CONFLICT DO UPDATE SET` du local : le run ne les reecrit pas
-- ② et ③ arrivent avec le code local, juste apres.
--
-- ⚠⚠ LE PATRON CITE PAR LA NOTE DU 14/10 EST A MOITIE FAUX, VERIFIE LE 16/10.
--   Elle dit « patron de jours_validite, taux_honoraires, notaire_id ». Or
--   `jours_validite` A QUITTE LA CLASSE A LE 07/09 (1.2b) : Hektor le garde dans
--   la proposition de l'offre, donc Hektor fait foi, et il est desormais RELU a
--   chaque run (affaire_ledger.py:790). Le vrai patron, c'est
--   `taux_honoraires` et `notaire_id` -- les seuls deux membres actuels de
--   `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS`. C'est sur eux que ce patch se cale.
--
-- ─── CE QUE CES COLONNES NE SONT PAS ───────────────────────────────────────────
-- ⛔ PAS un doublon de `honoraires_entree` / `honoraires_sortie`, qui existent
--    deja : celles-la sont de CLASSE C -- Hektor les calcule, il fait foi, elles
--    sont relues a chaque run (affaire_ledger.py:794-795). Les ecrire depuis
--    l'app serait ecrase la nuit suivante. D'ou le suffixe `_app` : la valeur
--    QUE NOUS AVONS SAISIE, a cote de celle que Hektor rend.
-- ⛔ RIEN NE PART CHEZ HEKTOR. Decision de Frederic du 14/10 : la commission va
--    dans notre registre ET dans le classeur, JAMAIS chez Hektor. Aucun geste
--    existant n'est modifie.
--
-- ─── RETOUR ARRIERE ────────────────────────────────────────────────────────────
--   ALTER TABLE public.app_affaire_ledger
--     DROP COLUMN IF EXISTS honoraires_entree_app,
--     DROP COLUMN IF EXISTS honoraires_sortie_app,
--     DROP COLUMN IF EXISTS charge_commission_app;
--   Purement additif : rien ne lit ces colonnes avant le 1b et le 1c.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU D'ENTREE : la table doit etre celle qu'on croit.
-- ---------------------------------------------------------------------
do $garde$
declare n integer;
begin
  select count(*) into n from information_schema.tables
   where table_schema = 'public' and table_name = 'app_affaire_ledger';
  if n <> 1 then
    raise exception 'ARRET : app_affaire_ledger est introuvable';
  end if;

  -- Les deux membres actuels de la classe A doivent etre la : si elles ont
  -- disparu, le patron sur lequel ce patch se cale n'existe plus.
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaire_ledger'
     and column_name in ('taux_honoraires', 'notaire_id');
  if n <> 2 then
    raise exception 'ARRET : taux_honoraires et/ou notaire_id manquent -- '
                    'le patron de classe A n''est pas celui mesure le 16/10 (vu %)', n;
  end if;

  -- Et les deux colonnes de classe C, qu'on ne doit PAS confondre avec les neuves.
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaire_ledger'
     and column_name in ('honoraires_entree', 'honoraires_sortie');
  if n <> 2 then
    raise exception 'ARRET : honoraires_entree/sortie manquent -- la table n''est '
                    'pas celle attendue (vu %)', n;
  end if;
end $garde$;

-- ---------------------------------------------------------------------
-- LE GESTE — trois colonnes, additives
-- ---------------------------------------------------------------------
alter table public.app_affaire_ledger
    add column if not exists honoraires_entree_app text,
    add column if not exists honoraires_sortie_app text,
    add column if not exists charge_commission_app text;

-- La charge ne prend que deux valeurs, en minuscules et sans accent : le front
-- et l'expediteur du classeur traduiront pour l'affichage (« Vendeur » /
-- « Acquereur »). Normaliser ICI evite la salade casse/accents qui a deja coute
-- au projet, et NULL reste permis : « on ne sait pas » n'est pas « vendeur ».
do $contrainte$
begin
  if not exists (
    select 1 from pg_constraint
     where conrelid = 'public.app_affaire_ledger'::regclass
       and conname = 'app_affaire_ledger_charge_commission_app_chk'
  ) then
    alter table public.app_affaire_ledger
      add constraint app_affaire_ledger_charge_commission_app_chk
      check (charge_commission_app is null
             or charge_commission_app in ('vendeur', 'acquereur'));
  end if;
end $contrainte$;

comment on column public.app_affaire_ledger.honoraires_entree_app is
    'CLASSE A (16/10/2026) : les honoraires VENDEUR saisis dans l''app, des '
    'l''offre. Hektor n''a aucune destination pour eux a ce stade. ⚠ A ne pas '
    'confondre avec honoraires_entree, de CLASSE C : Hektor la calcule et elle '
    'est relue a chaque run. Jamais poussee depuis le local '
    '(COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS), jamais envoyee a Hektor.';

comment on column public.app_affaire_ledger.honoraires_sortie_app is
    'CLASSE A (16/10/2026) : les honoraires ACQUEREUR saisis dans l''app, des '
    'l''offre. Meme regime que honoraires_entree_app.';

comment on column public.app_affaire_ledger.charge_commission_app is
    'CLASSE A (16/10/2026) : qui paie la commission -- ''vendeur'' ou '
    '''acquereur'', jamais autre chose. ⚠ ELLE NE SE DEDUIT PAS : mesure du '
    '14/10, sur 25 lignes ou le classeur de suivi dit « Acquereur », 13 sont '
    'rangees cote vendeur chez Hektor. Il faut donc la SAISIR. NULL = non '
    'renseignee, ce qui n''est pas « vendeur ».';

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU DE SORTIE
-- ---------------------------------------------------------------------
do $garde$
declare n integer; lignes bigint; remplies bigint;
begin
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaire_ledger'
     and column_name in ('honoraires_entree_app', 'honoraires_sortie_app',
                         'charge_commission_app');
  if n <> 3 then
    raise exception 'Seulement % colonne(s) sur 3 ont ete creees', n;
  end if;

  if not exists (
    select 1 from pg_constraint
     where conrelid = 'public.app_affaire_ledger'::regclass
       and conname = 'app_affaire_ledger_charge_commission_app_chk'
  ) then
    raise exception 'La contrainte sur charge_commission_app est absente';
  end if;

  select count(*) into lignes from public.app_affaire_ledger;
  select count(honoraires_entree_app) + count(honoraires_sortie_app)
       + count(charge_commission_app) into remplies from public.app_affaire_ledger;
  raise notice 'OK : 3 colonnes creees + contrainte posee. % affaire(s) au '
               'registre, % valeur(s) renseignee(s) -- ATTENDU 0, rien ne les '
               'ecrit encore (le 1b apporte la RPC, le 1c l''ecran).',
               lignes, remplies;
end $garde$;

-- ─── CONTROLE APRES APPLICATION ────────────────────────────────────────────────
--   select column_name, data_type
--     from information_schema.columns
--    where table_schema = 'public' and table_name = 'app_affaire_ledger'
--      and column_name like '%\_app'
--    order by column_name;
--   ATTENDU : charge_commission_app, honoraires_entree_app, honoraires_sortie_app
--             (plus app_chaine_id / app_contact_id s'ils finissent en _app... non :
--              ils commencent par app_, le filtre ci-dessus les exclut).
