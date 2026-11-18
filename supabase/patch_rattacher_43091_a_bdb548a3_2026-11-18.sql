-- ═══════════════════════════════════════════════════════════════════════════════
-- 43091 : L'OFFRE ET LE COMPROMIS REVIENNENT A LEUR LIGNE DU SHEET    18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- DECISION DE FREDERIC, 18/11 : « A » -- rattacher, et laisser 53ZS73KW orpheline.
--
-- LE CONSTAT. Le mandat 16992 porte DEUX lignes au Sheet, et une SEULE chaine chez
-- nous (21551, dossier D2026-0067) :
--     ligne  227  53ZS73KW  GIBERT Sabrina  . offre 22/10/2024 . compromis 18/12/2024
--                 « Annulée », ANNULEE LE 16/07/2025, ni vente ni facture
--     ligne 4505  bdb548a3  CHAPUIS Francois . offre 06/02/2026 . compromis 09/03/2026
--                 vente 30/07/2026 . facture GGTI00004406 . « Vente réglée »
--
-- Le gel du 29/10 a colle le compromis 17016 ET l'offre 32791 a la ligne GIBERT,
-- et la seule vente a la ligne CHAPUIS. ⛔ C'EST FAUX, ET LE SHEET LE PROUVE SEUL :
--     compromis 17016  date 2026-03-09  = AU JOUR EXACT du compromis de bdb548a3,
--                                         a 447 jours de celui de 53ZS73KW
--     offre 32791      vraie date 2026-03-09 (1re proposition au journal Hektor)
--                                         a 31 jours de bdb548a3, 503 de 53ZS73KW
--     et les TROIS transactions portent l'acquereur CHAPUIS chez Hektor.
--
-- CE QUE FAIT CE PATCH : il deplace DEUX liens, de la ligne 227 vers la ligne 4505.
-- ⛔ IL NE TOUCHE AUCUNE TRANSACTION -- ni chez nous, ni chez Hektor. Le registre,
--   les etats, les dates, les montants sont inchanges. Seul le RATTACHEMENT bouge.
--
-- ⚠⚠ CE QU'IL LAISSE OUVERT, ET QUI EST DIT PLUTOT QUE TU : apres ce patch,
--   53ZS73KW n'a plus AUCUN role gele. Les lots du classeur ecartent une ligne
--   « quand un role est DEJA relie » -- donc GIBERT redevient CANDIDATE, et son
--   etat « Annulée » la ferait entrer dans « offres annulees » ET « compromis
--   annules ». Un lot rejoue creerait l'affaire GIBERT, c'est-a-dire l'option B
--   que Frederic n'a PAS choisie. ⛔ NE PAS REJOUER UN LOT SANS TRANCHER CE POINT.
--
-- RETOUR ARRIERE : ..._INVERSE.sql       CONTROLE : ..._REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

-- ── ① LA GARDE : l'etat de depart, exactement ─────────────────────────────────
do $$
declare a int; b int; t int;
begin
  select count(*) into a from app_classeur_lien
   where ligne_classeur=227 and app_affaire_id in (21551,21552) and id_unique='53ZS73KW';
  select count(*) into b from app_classeur_lien
   where ligne_classeur=4505 and app_affaire_id=21553 and id_unique='bdb548a3';
  select count(*) into t from app_classeur_lien;
  if a <> 2 then raise exception '⛔ garde : % lien(s) sur la ligne 227 au lieu de 2', a; end if;
  if b <> 1 then raise exception '⛔ garde : % lien(s) sur la ligne 4505 au lieu de 1', b; end if;
  if t <> 12787 then raise exception '⛔ garde : % liens au total au lieu de 12 787', t; end if;
end $$;

-- ── ② LA SAUVEGARDE DATEE ─────────────────────────────────────────────────────
create table if not exists app_classeur_lien_avant_rattachement_43091_20261118
  as select * from app_classeur_lien where false;
insert into app_classeur_lien_avant_rattachement_43091_20261118
  select * from app_classeur_lien
   where ligne_classeur=227 and app_affaire_id in (21551,21552);

-- ── ③ LE DEPLACEMENT ──────────────────────────────────────────────────────────
--   ⚠ La cle primaire est (ligne_classeur, app_affaire_id) : on la deplace, donc
--     (4505,21551) et (4505,21552) doivent etre libres -- la garde ① l'a verifie
--     en comptant 1 seul lien sur 4505, celui de la vente 21553.
--   ⭐ `preuves` = 2 : la date du compromis AU JOUR EXACT, et l'acquereur CHAPUIS.
--     On ne recopie pas les 5 preuves de l'apparieur : elles valaient pour GIBERT.
update app_classeur_lien
   set ligne_classeur = 4505,
       id_unique      = 'bdb548a3',
       confiance      = 'sûre',
       preuves        = 2,
       etage          = 'rattachement decide a la main (18/11)',
       gele_le        = now(),
       gele_par       = 'rattachement_43091_2026-11-18'
 where ligne_classeur = 227 and app_affaire_id in (21551,21552);

-- ── ④ LES CONTROLES, AVANT LE COMMIT ──────────────────────────────────────────
do $$
declare n4505 int; n227 int; roles text; total int; ailleurs int;
begin
  select count(*), string_agg(role, '+' order by role) into n4505, roles
    from app_classeur_lien where ligne_classeur=4505;
  if n4505 <> 3 then raise exception '⛔ la ligne 4505 porte % liens au lieu de 3', n4505; end if;
  if roles <> 'compromis+offre+vente' then
    raise exception '⛔ roles de la ligne 4505 : %, attendu compromis+offre+vente', roles; end if;

  select count(*) into n227 from app_classeur_lien where ligne_classeur=227;
  if n227 <> 0 then raise exception '⛔ la ligne 227 porte encore % lien(s)', n227; end if;

  -- ⭐ TEMOIN INVERSE : on a DEPLACE, pas cree ni supprime.
  select count(*) into total from app_classeur_lien;
  if total <> 12787 then raise exception '⛔ % liens au total au lieu de 12 787', total; end if;

  -- ⭐ ET AUCUNE TRANSACTION N'A BOUGE : les 3 de 43091 sont toujours la, meme chaine.
  select count(*) into ailleurs from app_affaire_ledger
   where hektor_annonce_id=43091 and app_chaine_id=21551;
  if ailleurs <> 3 then raise exception '⛔ 43091 porte % transactions au lieu de 3', ailleurs; end if;

  raise notice '✅ offre et compromis rattaches a bdb548a3 ; 53ZS73KW est orpheline ; 0 transaction touchee';
end $$;

commit;
