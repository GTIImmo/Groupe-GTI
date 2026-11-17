-- ═══════════════════════════════════════════════════════════════════════════
-- C2 -- LES COMMISSIONS DU CLASSEUR QUE NOUS N'AVONS PAS
-- Genere le 2026-11-17 par phase2/checks/c2_generer_commissions_2026-11-17.py
--
-- FREDERIC, 17/11 : « Les 62 seules. » -> 62 lignes posees, les 270
-- affaires ANNULEES ne sont PAS posees.
--
-- ⛔⛔ POURQUOI LES ANNULEES SONT ECARTEES, ET C'EST COMPTABLE, PAS TECHNIQUE :
--   une affaire annulee n'a JAMAIS genere de commission. Le montant du classeur
--   etait PREVU, pas perçu. Et `honoraires_entree_app` dit « les honoraires VENDEUR
--   saisis dans l'app » : y mettre 270 montants jamais encaisses fausserait
--   tout calcul de chiffre d'affaires -- une erreur qui ne se voit qu'au moment ou
--   quelqu'un additionne. Il n'existe aucune colonne pour « commission prevue non
--   perçue » : la creer serait une decision a part.
--
-- ⭐ LE BLOCAGE DU PLAN EST PERIME POUR CE CHEMIN. Le plan dit « LA CASE EXISTE,
--   MAIS LE ROBINET EST FERME » (`CHAMPS_APP_AFFAIRE = ()`, etape absente du run,
--   « une valeur ecrite au carnet et non reposee serait INVISIBLE LE LENDEMAIN »).
--   Mais ca ne concerne QUE le carnet, qui ecrit `honoraires_entree`, de CLASSE C.
--   Nous ecrivons `honoraires_entree_app`, de CLASSE A : dans
--   COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (affaire_ledger.py l. 3108) ET dans la liste
--   des colonnes du local (l. 620). Le code le dit lui-meme l. 375 : « exactement le
--   trou que honoraires_entree_app comble depuis le lot 1 ».
--
-- ⚠⚠ RESERVE DECLAREE, ET ELLE VIENT DE SA PROPRE REGLE DU CHANTIER :
--   LOT 1  20 affaires ABOUTIES (158 537 EUR) -- historique pur, aucune reserve
--   LOT 2  42 affaires EN COURS (283 480 EUR) -- sa regle dit « on ne reprend que ce
--          que Hektor ne rendra plus », et Hektor calculera leur commission A LA
--          VENTE. ➡ POUR S'ARRETER AUX 20 : ne jouer que le bloc 3a, et sauter 3b.
--
-- LA CIBLE : la transaction la PLUS AVANCEE de la chaine (vente > compromis > offre),
--   parce que la colonne accepte les trois « des l'offre » et qu'on pose la valeur la
--   ou l'affaire en est.
--
-- Retour arriere : patch_c2_commissions_2026-11-17_INVERSE.sql
-- Controle       : patch_c2_commissions_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare deja integer; cibles integer;
begin
  select count(*) into deja from public.app_affaire_ledger
   where app_affaire_id in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817) and honoraires_entree_app is not null;
  if deja <> 0 then
    raise exception '⛔ ARRET : % cible(s) portent deja une valeur.', deja;
  end if;
  select count(*) into cibles from public.app_affaire_ledger
   where app_affaire_id in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817);
  if cibles <> 62 then
    raise exception '⛔ ARRET : % cibles sur les 62 attendues.', cibles;
  end if;
  raise notice '✅ etat d''avant : 0 valeur posee, 62 cibles retrouvees.';
end $$;

-- ─── 2. LA SAUVEGARDE, ET ELLE NAIT FERMEE (la lecon du 16/11) ─────────────
create table if not exists public.app_affaire_avant_c2_20261117 as
  select app_affaire_id, kind, hektor_annonce_id, honoraires_entree,
         honoraires_entree_app, commission_agence, now() as photographie_le
    from public.app_affaire_ledger
   where app_affaire_id in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817);
revoke all on public.app_affaire_avant_c2_20261117 from authenticated, anon;

-- ─── 3a. LOT 1 : LES 20 AFFAIRES ABOUTIES (158 537 EUR) ─────────────────────
with poser(app_affaire_id, montant) as (values
    (27346, '6000'),
    (28668, '8000'),
    (8884, '9000'),
    (28948, '7500'),
    (30761, '8000'),
    (29028, '10000'),
    (27011, '12000'),
    (28878, '15000'),
    (30778, '7000'),
    (30716, '15200'),
    (30743, '2900'),
    (14137, '2337'),
    (998, '1000'),
    (28665, '13000'),
    (28962, '10000'),
    (29032, '7000'),
    (7113, '6400'),
    (25846, '5700'),
    (28952, '5000'),
    (28656, '7500')
)
update public.app_affaire_ledger l
   set honoraires_entree_app = p.montant
  from poser p
 where l.app_affaire_id = p.app_affaire_id
   and l.honoraires_entree_app is null;

-- ─── 3b. LOT 2 : LES 42 AFFAIRES EN COURS (283 480 EUR) ─────────────────────
-- ⚠ SA REGLE DU CHANTIER LES ECARTERAIT. Pour s'arreter au lot 1, NE PAS jouer
--   ce bloc -- et ajuster les comptes du controle 4 en consequence.
with poser(app_affaire_id, montant) as (values
    (29015, '7000'),
    (30688, '6000'),
    (30784, '4000'),
    (30706, '2500'),
    (30729, '5000'),
    (30692, '11000'),
    (30742, '11000'),
    (30744, '10000'),
    (30759, '9500'),
    (28995, '4000'),
    (29020, '500'),
    (28985, '1700'),
    (30763, '9000'),
    (30768, '4000'),
    (30786, '9000'),
    (30815, '9000'),
    (30735, '10000'),
    (30804, '10000'),
    (30796, '12400'),
    (28568, '4000'),
    (30713, '6580'),
    (30707, '8000'),
    (30792, '4000'),
    (30764, '5000'),
    (30658, '3500'),
    (30808, '10500'),
    (30816, '3500'),
    (30785, '8000'),
    (1000320, '4600'),
    (30775, '2000'),
    (30758, '4000'),
    (30741, '5000'),
    (30806, '3900'),
    (30803, '9000'),
    (30802, '14000'),
    (1000318, '1800'),
    (30756, '10000'),
    (30705, '10000'),
    (30797, '7000'),
    (30747, '8000'),
    (30702, '5500'),
    (30817, '10000')
)
update public.app_affaire_ledger l
   set honoraires_entree_app = p.montant
  from poser p
 where l.app_affaire_id = p.app_affaire_id
   and l.honoraires_entree_app is null;

-- ─── 4. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  posees   integer;
  ailleurs integer;
  mauvais  integer;
  ferme    integer;
begin
  select count(*) into posees from public.app_affaire_ledger
   where app_affaire_id in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817) and honoraires_entree_app is not null;
  if posees <> 62 then
    raise exception '⛔ 62 attendues, % posees.', posees;
  end if;

  -- ⭐ TEMOIN INVERSE : aucune AUTRE ligne n'a recu de valeur. On compte les lignes
  --   hors du lot : il y en avait 4 au 17/11 (des saisies de l'app), pas 0.
  select count(*) into ailleurs from public.app_affaire_ledger
   where honoraires_entree_app is not null
     and app_affaire_id not in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817);
  if ailleurs <> 4 then
    raise exception '⛔ % ligne(s) hors du lot portent une valeur, 4 attendues '
      '(les saisies de l''app). Le patch a debordé, ou une saisie est arrivee.', ailleurs;
  end if;

  -- ⭐ AUCUN MONTANT ABSURDE : ni zero, ni negatif, ni non-numerique
  select count(*) into mauvais from public.app_affaire_ledger
   where honoraires_entree_app is not null
     and (honoraires_entree_app !~ '^[0-9]+(\.[0-9]+)?$'
          or honoraires_entree_app::numeric <= 0);
  if mauvais <> 0 then
    raise exception '⛔ % montant(s) absurde(s) (zero, negatif ou illisible).', mauvais;
  end if;

  select count(*) into ferme from information_schema.role_table_grants
   where table_schema='public' and table_name='app_affaire_avant_c2_20261117'
     and grantee in ('authenticated','anon');
  if ferme <> 0 then
    raise exception '⛔ la sauvegarde porte encore % droit(s).', ferme;
  end if;

  raise notice '✅ 62 commissions posees (20 abouties + 42 en cours) . '
    '4 saisies de l''app intactes . 0 montant absurde . sauvegarde FERMEE.';
end $$;

commit;
