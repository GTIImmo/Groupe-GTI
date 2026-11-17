-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (1er patch) -- LE CATALOGUE DES CLAUSES ET LES 169 MOTIFS D'ANNULATION
-- Genere le 2026-11-17 par phase2/checks/c4_generer_motifs_et_conditions_2026-11-17.py
--
-- SES DECISIONS DU 17/11 :
--   . le CATALOGUE : ajouter « Permis de construire » et « Delai de retractation SRU »
--   . les MOTIFS : « Les 216 motifs normalises, les 492 phrases uniques partant en
--     note » -> `motif_annulation_app` ne recoit QUE les motifs qui REVIENNENT
--   . les NOTES sont dans un SECOND patch (5 003 lignes), pas ici
--
-- ⛔ RIEN POUR LE PRET, ET C'EST MESURE : « Obtention Credit » EXISTE DEJA au
--   catalogue (id 2, 45 jours). ADP et ODP n'en sont pas deux clauses mais le
--   DEPART et l'ECHEANCE de celle-la -- ADP avant ODP **24 fois sur 24**, jamais
--   l'inverse, ecart median **31 jours** (le meme jour du mois, un mois plus tard).
--   J'avais propose « offre de pret » et « accord de pret » : c'eut ete un DOUBLON.
--
-- ⭐ LE LIBELLE D'UN MOTIF EST L'ECRITURE LA PLUS FREQUENTE DE SON GROUPE, jamais
--   un texte invente : « refus prêt » (31) l'emporte sur « refus de prêt » (25) et
--   « refus de pret » (1). Du texte reel du classeur -- ni invention, ni
--   normalisation agressive. C'est sa consigne « sans interpreter », appliquee.
--
-- ⭐⭐ ET LE MOTIF VA SUR LA MEME TRANSACTION QUE SA DATE : le compromis annule
--   d'abord (la cible de C3), l'offre refusee en repli quand la chaine n'a pas de
--   compromis. Ainsi `date_annulation_app` et `motif_annulation_app` sont sur la
--   MEME ligne -- le « quand » et le « pourquoi » enfin reunis.
--
-- ⛔ `motif_annulation_app` est de CLASSE A : dans
--   COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS et dans la boucle de creation locale. Rien
--   ne part chez Hektor, et le run ne l'ecrase pas.
--
-- Retour arriere : patch_c4_motifs_conditions_2026-11-17_INVERSE.sql
-- Controle       : patch_c4_motifs_conditions_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare deja integer; cat integer; cibles integer;
begin
  select count(*) into deja from public.app_affaire_ledger
   where motif_annulation_app is not null;
  if deja <> 0 then
    raise exception '⛔ ARRET : % motif(s) deja pose(s). Ce patch suppose la colonne '
      'vierge (0 au 17/11).', deja;
  end if;
  select count(*) into cat from public.app_condition_catalogue;
  if cat <> 2 then
    raise exception '⛔ ARRET : le catalogue porte % clause(s) au lieu de 2 '
      '(Preemption mairie, Obtention Credit).', cat;
  end if;
  select count(*) into cibles from public.app_affaire_ledger
   where app_affaire_id in (6157, 23983, 25965, 16096, 7176, 11110, 26603, 8840, 8845, 20296, 6343, 7422, 27178, 7067, 28155, 22, 27143, 101, 8839, 958, 7177, 11111, 7232, 11501, 4198, 4179, 12952, 8856, 16170, 17433, 17209, 17203, 24008, 14083, 26605, 15914, 20, 4203, 8864, 20077, 6138, 28263, 28258, 8917, 24188, 27145, 16169, 1874, 160, 1019, 9359, 19102, 8925, 4272, 7646, 6431, 8321, 7251, 7645, 74, 17226, 25867, 26013, 9362, 19086, 19561, 7560, 117, 14935, 19619, 25735, 17011, 4277, 25877, 4321, 4508, 1000142, 6499, 4372, 27338, 16251, 16046, 7580, 19113, 7606, 10015, 4300, 4329, 17291, 16833, 16298, 9896, 26072, 19512, 24165, 2533, 24168, 19456, 27243, 22008, 19095, 17301, 15042, 15073, 200, 7438, 7667, 4327, 23447, 11596, 15915, 16327, 3719, 4484, 4111, 26076, 24297, 16305, 11524, 21598, 19657, 15032, 7724, 4480, 25742, 14086, 1089, 7699, 25897, 15059, 269, 7725, 259, 16846, 16841, 19665, 25911, 14141, 20408, 27372, 16382, 28289, 17525, 15096, 4799, 24499, 11472, 26028, 24443, 16378, 26155, 20613, 4706, 26152, 11791, 27661, 1229, 22256, 23809, 16388, 24564, 4771, 11885, 11963, 11972, 15901, 28839, 28881, 30648);
  if cibles <> 169 then
    raise exception '⛔ ARRET : % cibles sur les 169 attendues.', cibles;
  end if;
  raise notice '✅ etat d''avant : 0 motif, catalogue a 2 clauses, 169 cibles.';
end $$;

-- ─── 2. LA SAUVEGARDE, ET ELLE NAIT FERMEE ─────────────────────────────────
create table if not exists public.app_affaire_avant_c4_20261117 as
  select app_affaire_id, kind, state, hektor_annonce_id, date_annulation_app,
         motif_annulation_app, now() as photographie_le
    from public.app_affaire_ledger
   where app_affaire_id in (6157, 23983, 25965, 16096, 7176, 11110, 26603, 8840, 8845, 20296, 6343, 7422, 27178, 7067, 28155, 22, 27143, 101, 8839, 958, 7177, 11111, 7232, 11501, 4198, 4179, 12952, 8856, 16170, 17433, 17209, 17203, 24008, 14083, 26605, 15914, 20, 4203, 8864, 20077, 6138, 28263, 28258, 8917, 24188, 27145, 16169, 1874, 160, 1019, 9359, 19102, 8925, 4272, 7646, 6431, 8321, 7251, 7645, 74, 17226, 25867, 26013, 9362, 19086, 19561, 7560, 117, 14935, 19619, 25735, 17011, 4277, 25877, 4321, 4508, 1000142, 6499, 4372, 27338, 16251, 16046, 7580, 19113, 7606, 10015, 4300, 4329, 17291, 16833, 16298, 9896, 26072, 19512, 24165, 2533, 24168, 19456, 27243, 22008, 19095, 17301, 15042, 15073, 200, 7438, 7667, 4327, 23447, 11596, 15915, 16327, 3719, 4484, 4111, 26076, 24297, 16305, 11524, 21598, 19657, 15032, 7724, 4480, 25742, 14086, 1089, 7699, 25897, 15059, 269, 7725, 259, 16846, 16841, 19665, 25911, 14141, 20408, 27372, 16382, 28289, 17525, 15096, 4799, 24499, 11472, 26028, 24443, 16378, 26155, 20613, 4706, 26152, 11791, 27661, 1229, 22256, 23809, 16388, 24564, 4771, 11885, 11963, 11972, 15901, 28839, 28881, 30648);
revoke all on public.app_affaire_avant_c4_20261117 from authenticated, anon;

-- ─── 3a. LE CATALOGUE : LES DEUX CLAUSES QUI MANQUENT ──────────────────────
-- ⭐ `on conflict do nothing` sur le libelle : si quelqu'un les a ajoutees entre
--   le controle 1 et ici, on ne cree pas de doublon.
-- ⛔ PAS de `cross join lateral (select row_number() over ())` : la colonne n'y est
--   pas visible (« column v.ordre does not exist », premiere tentative du 17/11,
--   rejetee AVANT le commit -- verifie : catalogue a 2, 0 motif, pas de sauvegarde).
--   `row_number() over ()` se met directement dans le SELECT.
-- ⛔⛔ ET `id` EST A FOURNIR : il est TEXT, NOT NULL, et SANS AUCUN DEFAUT
--   (mesure du 17/11 -- « null value in column id violates not-null constraint »,
--   seconde tentative, rejetee avant le commit). Ce n'est pas une sequence : c'est
--   un identifiant choisi a la main, et les deux clauses d'origine portent '1' et
--   '2'. On prend donc le MAXIMUM NUMERIQUE existant + 1, et on ne lit que les ids
--   numeriques -- un id non numerique ferait tomber la conversion.
insert into public.app_condition_catalogue
       (id, libelle, jours_defaut, actif, rang, ecrit_par)
select ((select coalesce(max(c.id::integer), 0) from public.app_condition_catalogue c
          where c.id ~ '^[0-9]+$') + row_number() over ())::text,
       v.libelle, v.jours, true,
       (select coalesce(max(c.rang), 0) from public.app_condition_catalogue c)
         + row_number() over ()::integer,
       'classeur:C4:2026-11-17'
  from (values
    ('Permis de construire', 0),
    ('Delai de retractation SRU', 10)
  ) as v(libelle, jours)
 where not exists (select 1 from public.app_condition_catalogue c
                    where lower(c.libelle) = lower(v.libelle));

-- ─── 3b. LES 169 MOTIFS D'ANNULATION ───────────────────────────────────────
with poser(app_affaire_id, motif) as (values
    (6157, 'Pret refuse'),
    (23983, 'Pret refuse'),
    (25965, 'Pret refuse'),
    (16096, 'Pret refuse'),
    (7176, 'Pret refuse'),
    (11110, 'Changement de situation acquereur'),
    (26603, 'Travaux ou etat du bien'),
    (8840, 'Pret refuse'),
    (8845, 'Changement de situation acquereur'),
    (20296, 'Pret refuse'),
    (6343, 'Pret refuse'),
    (7422, 'Retractation'),
    (27178, 'Retractation'),
    (7067, 'Changement de situation acquereur'),
    (28155, 'Pret refuse'),
    (22, 'Pret refuse'),
    (27143, 'Pret refuse'),
    (101, 'Retractation'),
    (8839, 'Pret refuse'),
    (958, 'Pret refuse'),
    (7177, 'Pret refuse'),
    (11111, 'Retractation'),
    (7232, 'Pret refuse'),
    (11501, 'Retractation'),
    (4198, 'Pret refuse'),
    (4179, 'Retractation'),
    (12952, 'Annule sans motif precise'),
    (8856, 'Retractation'),
    (16170, 'Changement de situation acquereur'),
    (17433, 'Pret refuse'),
    (17209, 'Retractation'),
    (17203, 'Changement de situation acquereur'),
    (24008, 'Annule sans motif precise'),
    (14083, 'Annule sans motif precise'),
    (26605, 'Retractation'),
    (15914, 'Annule sans motif precise'),
    (20, 'Retractation'),
    (4203, 'Annule sans motif precise'),
    (8864, 'Annule sans motif precise'),
    (20077, 'Pret refuse'),
    (6138, 'Annule sans motif precise'),
    (28263, 'Travaux ou etat du bien'),
    (28258, 'Travaux ou etat du bien'),
    (8917, 'Annule sans motif precise'),
    (24188, 'Pret refuse'),
    (27145, 'Retractation'),
    (16169, 'Retractation'),
    (1874, 'Retractation'),
    (160, 'Retractation'),
    (1019, 'Retractation'),
    (9359, 'Pret refuse'),
    (19102, 'Retractation'),
    (8925, 'Retractation'),
    (4272, 'Retractation'),
    (7646, 'Annule sans motif precise'),
    (6431, 'Retractation'),
    (8321, 'Retractation'),
    (7251, 'Retractation'),
    (7645, 'Retractation'),
    (74, 'Retractation'),
    (17226, 'Retractation'),
    (25867, 'Retractation'),
    (26013, 'Retractation'),
    (9362, 'Retractation'),
    (19086, 'Permis refuse'),
    (19561, 'Retractation'),
    (7560, 'Pret refuse'),
    (117, 'Retractation'),
    (14935, 'Changement de situation acquereur'),
    (19619, 'Pret refuse'),
    (25735, 'Retractation'),
    (17011, 'Retractation'),
    (4277, 'Pret refuse'),
    (25877, 'Pret refuse'),
    (4321, 'Retractation'),
    (4508, 'Retractation'),
    (1000142, 'Retractation'),
    (6499, 'Pret refuse'),
    (4372, 'Pret refuse'),
    (27338, 'Pret refuse'),
    (16251, 'Pret refuse'),
    (16046, 'Pret refuse'),
    (7580, 'Pret refuse'),
    (19113, 'Pret refuse'),
    (7606, 'Pret refuse'),
    (10015, 'Pret refuse'),
    (4300, 'Pret refuse'),
    (4329, 'Pret refuse'),
    (17291, 'Annule sans motif precise'),
    (16833, 'Pret refuse'),
    (16298, 'Pret refuse'),
    (9896, 'Pret refuse'),
    (26072, 'Pret refuse'),
    (19512, 'Pret refuse'),
    (24165, 'Annule sans motif precise'),
    (2533, 'Retractation'),
    (24168, 'Travaux ou etat du bien'),
    (19456, 'Pret refuse'),
    (27243, 'Travaux ou etat du bien'),
    (22008, 'Pret refuse'),
    (19095, 'Pret refuse'),
    (17301, 'Annule sans motif precise'),
    (15042, 'Annule sans motif precise'),
    (15073, 'Annule sans motif precise'),
    (200, 'Retractation'),
    (7438, 'Pret refuse'),
    (7667, 'Annule sans motif precise'),
    (4327, 'Retractation'),
    (23447, 'Retractation'),
    (11596, 'Retractation'),
    (15915, 'Retractation'),
    (16327, 'Annule sans motif precise'),
    (3719, 'Annule sans motif precise'),
    (4484, 'Retractation'),
    (4111, 'Pret refuse'),
    (26076, 'Travaux ou etat du bien'),
    (24297, 'Travaux ou etat du bien'),
    (16305, 'Pret refuse'),
    (11524, 'Retractation'),
    (21598, 'Permis refuse'),
    (19657, 'Pret refuse'),
    (15032, 'Pret refuse'),
    (7724, 'Pret refuse'),
    (4480, 'Retractation'),
    (25742, 'Retractation'),
    (14086, 'Retractation'),
    (1089, 'Pret refuse'),
    (7699, 'Retractation'),
    (25897, 'Changement de situation acquereur'),
    (15059, 'Pret refuse'),
    (269, 'Retractation'),
    (7725, 'Retractation'),
    (259, 'Pret refuse'),
    (16846, 'Pret refuse'),
    (16841, 'Pret refuse'),
    (19665, 'Pret refuse'),
    (25911, 'Pret refuse'),
    (14141, 'Pret refuse'),
    (20408, 'Retractation'),
    (27372, 'Retractation'),
    (16382, 'Pret refuse'),
    (28289, 'Retractation'),
    (17525, 'Retractation'),
    (15096, 'Annule sans motif precise'),
    (4799, 'Retractation'),
    (24499, 'Retractation'),
    (11472, 'Annule sans motif precise'),
    (26028, 'Retractation'),
    (24443, 'Changement de situation acquereur'),
    (16378, 'Changement de situation acquereur'),
    (26155, 'Pret refuse'),
    (20613, 'Retractation'),
    (4706, 'Pret refuse'),
    (26152, 'Retractation'),
    (11791, 'Retractation'),
    (27661, 'Pret refuse'),
    (1229, 'Pret refuse'),
    (22256, 'Pret refuse'),
    (23809, 'Annule sans motif precise'),
    (16388, 'Pret refuse'),
    (24564, 'Pret refuse'),
    (4771, 'Pret refuse'),
    (11885, 'Retractation'),
    (11963, 'Retractation'),
    (11972, 'Retractation'),
    (15901, 'Pret refuse'),
    (28839, 'Pret refuse'),
    (28881, 'Pret refuse'),
    (30648, 'Pret refuse')
)
update public.app_affaire_ledger l
   set motif_annulation_app = p.motif
  from poser p
 where l.app_affaire_id = p.app_affaire_id
   and l.motif_annulation_app is null;

-- ─── 4. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  poses    integer;
  ailleurs integer;
  cat      integer;
  sans_date integer;
  ferme    integer;
begin
  select count(*) into poses from public.app_affaire_ledger
   where app_affaire_id in (6157, 23983, 25965, 16096, 7176, 11110, 26603, 8840, 8845, 20296, 6343, 7422, 27178, 7067, 28155, 22, 27143, 101, 8839, 958, 7177, 11111, 7232, 11501, 4198, 4179, 12952, 8856, 16170, 17433, 17209, 17203, 24008, 14083, 26605, 15914, 20, 4203, 8864, 20077, 6138, 28263, 28258, 8917, 24188, 27145, 16169, 1874, 160, 1019, 9359, 19102, 8925, 4272, 7646, 6431, 8321, 7251, 7645, 74, 17226, 25867, 26013, 9362, 19086, 19561, 7560, 117, 14935, 19619, 25735, 17011, 4277, 25877, 4321, 4508, 1000142, 6499, 4372, 27338, 16251, 16046, 7580, 19113, 7606, 10015, 4300, 4329, 17291, 16833, 16298, 9896, 26072, 19512, 24165, 2533, 24168, 19456, 27243, 22008, 19095, 17301, 15042, 15073, 200, 7438, 7667, 4327, 23447, 11596, 15915, 16327, 3719, 4484, 4111, 26076, 24297, 16305, 11524, 21598, 19657, 15032, 7724, 4480, 25742, 14086, 1089, 7699, 25897, 15059, 269, 7725, 259, 16846, 16841, 19665, 25911, 14141, 20408, 27372, 16382, 28289, 17525, 15096, 4799, 24499, 11472, 26028, 24443, 16378, 26155, 20613, 4706, 26152, 11791, 27661, 1229, 22256, 23809, 16388, 24564, 4771, 11885, 11963, 11972, 15901, 28839, 28881, 30648) and motif_annulation_app is not null;
  if poses <> 169 then
    raise exception '⛔ 169 attendus, % poses.', poses;
  end if;

  -- ⭐ TEMOIN INVERSE : rien hors du lot
  select count(*) into ailleurs from public.app_affaire_ledger
   where motif_annulation_app is not null and app_affaire_id not in (6157, 23983, 25965, 16096, 7176, 11110, 26603, 8840, 8845, 20296, 6343, 7422, 27178, 7067, 28155, 22, 27143, 101, 8839, 958, 7177, 11111, 7232, 11501, 4198, 4179, 12952, 8856, 16170, 17433, 17209, 17203, 24008, 14083, 26605, 15914, 20, 4203, 8864, 20077, 6138, 28263, 28258, 8917, 24188, 27145, 16169, 1874, 160, 1019, 9359, 19102, 8925, 4272, 7646, 6431, 8321, 7251, 7645, 74, 17226, 25867, 26013, 9362, 19086, 19561, 7560, 117, 14935, 19619, 25735, 17011, 4277, 25877, 4321, 4508, 1000142, 6499, 4372, 27338, 16251, 16046, 7580, 19113, 7606, 10015, 4300, 4329, 17291, 16833, 16298, 9896, 26072, 19512, 24165, 2533, 24168, 19456, 27243, 22008, 19095, 17301, 15042, 15073, 200, 7438, 7667, 4327, 23447, 11596, 15915, 16327, 3719, 4484, 4111, 26076, 24297, 16305, 11524, 21598, 19657, 15032, 7724, 4480, 25742, 14086, 1089, 7699, 25897, 15059, 269, 7725, 259, 16846, 16841, 19665, 25911, 14141, 20408, 27372, 16382, 28289, 17525, 15096, 4799, 24499, 11472, 26028, 24443, 16378, 26155, 20613, 4706, 26152, 11791, 27661, 1229, 22256, 23809, 16388, 24564, 4771, 11885, 11963, 11972, 15901, 28839, 28881, 30648);
  if ailleurs <> 0 then
    raise exception '⛔ % ligne(s) hors du lot portent un motif.', ailleurs;
  end if;

  -- ⭐ LE CATALOGUE : 2 + 2 = 4, pas plus
  select count(*) into cat from public.app_condition_catalogue;
  if cat <> 4 then
    raise exception '⛔ le catalogue porte % clauses au lieu de 4.', cat;
  end if;

  -- ⭐⭐ LE CONTROLE QUI DONNE SON SENS AU LOT : un motif SANS date d'annulation
  --   est une moitie de reponse. On le COMPTE, on ne l'interdit pas -- toutes les
  --   lignes de C3 ne sont pas ici, et inversement.
  select count(*) into sans_date from public.app_affaire_ledger
   where motif_annulation_app is not null and date_annulation_app is null;
  raise notice 'ⓘ % motif(s) sans date d''annulation -- le « pourquoi » sans le '
    '« quand ». Normal : C3 et C4 n''ont pas le meme perimetre.', sans_date;

  select count(*) into ferme from information_schema.role_table_grants
   where table_schema='public' and table_name='app_affaire_avant_c4_20261117'
     and grantee in ('authenticated','anon');
  if ferme <> 0 then
    raise exception '⛔ la sauvegarde porte encore % droit(s).', ferme;
  end if;

  raise notice '✅ 169 motifs poses . 0 hors du lot . catalogue a 4 clauses . '
    'sauvegarde FERMEE.';
end $$;

commit;
