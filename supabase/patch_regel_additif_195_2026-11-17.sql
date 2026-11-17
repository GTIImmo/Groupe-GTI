-- ═══════════════════════════════════════════════════════════════════════════
-- D1 -- LE RE-GEL ADDITIF : LIER LES 195 TRANSACTIONS CREEES LE 16/11
-- 17/11/2026
--
-- ⭐⭐⭐ POURQUOI CE PATCH EXISTE, ET C'EST SA QUESTION QUI L'A FAIT NAITRE.
--   Frederic, le 17/11 : « Mais on a pas deja ajouter les offres d'achat 195 ? ».
--   Oui -- et MON AUDIT NE LES VOYAIT PAS. Il cherchait les transactions d'une
--   ligne du classeur VIA `app_classeur_lien`, or LES 195 CREEES N'Y ONT AUCUN
--   LIEN : le gel ne connait que ce qui existait avant lui. Je recomptais donc
--   comme « manquant » ce que nous venions de poser (233 annoncees, 42 reelles).
--
--   ⛔ ET CE N'EST PAS QU'UNE ERREUR DE MESURE : tant que les 195 sont absentes
--     du gel, TOUTE lecture qui passe par lui les ignore -- aujourd'hui, et a
--     chaque audit futur. C'est le gel qui est incomplet, pas la mesure.
--
-- ⭐⭐ ET LE GESTE EST DETERMINISTE, SANS AUCUNE DEVINETTE. Chaque transaction
--   creee porte SA LIGNE D'ORIGINE dans son payload :
--     {"classeur_lot": "C5 lot B -- offres annulees", "classeur_pose_le":
--      "2026-11-16", "etat_au_classeur": "Annulee", "classeur_id_unique": "S13Z3PIN"}
--   On ne rapproche donc rien : on RELIT ce que le generateur a ecrit.
--   Mesure prealable : 195/195 trouvent leur ligne dans app_classeur_ligne_id.
--
-- ⛔ ADDITIF, ET STRICTEMENT : on n'UPDATE ni ne SUPPRIME aucun des 12 595 liens
--   existants. La clef primaire est (ligne_classeur + app_affaire_id), et le
--   `where not exists` garantit qu'on n'ecrase rien.
--
-- LES CHOIX DE VALEURS, ET POURQUOI :
--   role      = le `kind` de la transaction (offre / compromis / vente)
--   confiance = 'sûre' -- ce n'est PAS un appariement devine : c'est NOUS qui
--               avons cree la transaction DEPUIS cette ligne. La certitude est
--               par construction.
--   preuves   = 0 -- et c'est HONNETE : `preuves` compte les indices d'un
--               rapprochement, et il n'y a eu AUCUN rapprochement a faire.
--               Mettre un chiffre eleve mentirait sur la nature du lien.
--               ⭐ Verifie avant de choisir : AUCUN lecteur du projet ne filtre
--                 sur `preuves` ni sur `confiance` -- les deux sont informatives.
--   etage     = '0 creee par C5 depuis cette ligne' -- l'etage dit la METHODE,
--               et celle-ci n'est pas un etage d'appariement.
--   gele_par  = 'c5 re-gel additif 2026-11-17' -- pour qu'un lecteur futur sache
--               d'ou viennent ces liens sans avoir a le deviner.
--
-- ⭐ ET LA SENTINELLE NE CRIERA PAS : `app_v_classeur_lien_casse` ne retient un
--   lien que si la transaction a disparu, OU si `hektor_affaire_id IS NOT NULL`
--   et `present_in_hektor = false`. Les 195 ont `hektor_affaire_id` NULL
--   (195/195, mesure) -> elles n'entrent dans aucun des deux cas.
--
-- RETOUR ARRIERE : patch_regel_additif_195_2026-11-17_INVERSE.sql
-- CONTROLES      : patch_regel_additif_195_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① LA SAUVEGARDE DATEE -- le gel entier, avant tout geste
drop table if exists app_classeur_lien_avant_regel_20261117;
create table app_classeur_lien_avant_regel_20261117 as
  select * from app_classeur_lien;

do $$
declare n integer;
begin
  select count(*) into n from app_classeur_lien_avant_regel_20261117;
  if n <> 12595 then
    raise exception '⛔ LA SAUVEGARDE PORTE % liens au lieu de 12 595', n;
  end if;
end $$;

-- ② LE GARDE-FOU : si le re-gel est deja passe, on ne rejoue pas
do $$
declare n integer;
begin
  select count(*) into n from app_classeur_lien
   where gele_par = 'c5 re-gel additif 2026-11-17';
  if n > 0 then
    raise exception '⛔ DEJA POSE : % liens portent cette marque. Jouer l INVERSE '
      'd abord.', n;
  end if;
end $$;

-- ③ LE RE-GEL ADDITIF
--    ⭐ une seule requete, entierement deduite de ce qui est en base : aucune
--      liste de valeurs ecrite a la main, donc rien a recopier de travers.
insert into app_classeur_lien
    (ligne_classeur, app_affaire_id, role, confiance, preuves, etage,
     gele_par, id_unique)
select g.ligne_classeur,
       l.app_affaire_id,
       l.kind,
       'sûre',
       0,
       '0 creee par C5 depuis cette ligne',
       'c5 re-gel additif 2026-11-17',
       g.id_unique
  from app_affaire_ledger l
  join app_classeur_ligne_id g
    on g.id_unique = l.payload_json->>'classeur_id_unique'
 where l.transaction_origine = 'classeur'
   and not exists (select 1 from app_classeur_lien k
                    where k.ligne_classeur = g.ligne_classeur
                      and k.app_affaire_id = l.app_affaire_id);

-- ④ LES CONTROLES, DANS LA MEME TRANSACTION
do $$
declare n integer; m integer;
begin
  -- ⭐ LES 195 SONT TOUTES LIEES, et c'est le but du patch
  select count(*) into n from app_affaire_ledger l
   where l.transaction_origine = 'classeur'
     and not exists (select 1 from app_classeur_lien k
                      where k.app_affaire_id = l.app_affaire_id);
  if n <> 0 then raise exception '⛔ % des 195 n ont toujours pas de lien', n; end if;

  -- ⭐ ON EN A POSE EXACTEMENT 195
  select count(*) into n from app_classeur_lien
   where gele_par = 'c5 re-gel additif 2026-11-17';
  if n <> 195 then raise exception '⛔ % liens poses au lieu de 195', n; end if;

  -- ⭐⭐ ET LES 12 595 D'AVANT SONT INTACTS, A L'OCTET : on compare a la
  --   sauvegarde, ligne par ligne, et pas seulement leur nombre.
  select count(*) into n from app_classeur_lien;
  if n <> 12790 then
    raise exception '⛔ LE GEL PORTE % liens au lieu de 12 790 (12 595 + 195)', n;
  end if;
  select count(*) into n
    from app_classeur_lien_avant_regel_20261117 s
    left join app_classeur_lien k
           on k.ligne_classeur = s.ligne_classeur
          and k.app_affaire_id = s.app_affaire_id
   where k.app_affaire_id is null;
  if n <> 0 then raise exception '⛔ % liens d origine ONT DISPARU', n; end if;
  select count(*) into n
    from app_classeur_lien_avant_regel_20261117 s
    join app_classeur_lien k
      on k.ligne_classeur = s.ligne_classeur and k.app_affaire_id = s.app_affaire_id
   where k.role is distinct from s.role
      or k.confiance is distinct from s.confiance
      or k.preuves is distinct from s.preuves
      or k.etage is distinct from s.etage
      or k.id_unique is distinct from s.id_unique;
  if n <> 0 then raise exception '⛔ % liens d origine ONT ETE MODIFIES', n; end if;

  -- ⭐ chaque lien neuf porte le MEME role que sa transaction
  select count(*) into n from app_classeur_lien k
    join app_affaire_ledger l on l.app_affaire_id = k.app_affaire_id
   where k.gele_par = 'c5 re-gel additif 2026-11-17' and k.role <> l.kind;
  if n <> 0 then raise exception '⛔ % liens neufs ont un role faux', n; end if;

  -- ⭐ et le MEME id_unique que le payload de sa transaction
  select count(*) into n from app_classeur_lien k
    join app_affaire_ledger l on l.app_affaire_id = k.app_affaire_id
   where k.gele_par = 'c5 re-gel additif 2026-11-17'
     and k.id_unique is distinct from l.payload_json->>'classeur_id_unique';
  if n <> 0 then raise exception '⛔ % liens neufs ont un id_unique faux', n; end if;

  -- ⛔ TEMOIN INVERSE : la sentinelle du gel ne doit PAS crier
  select count(*) into n from app_v_classeur_lien_casse where gravite = 'DISPARUE';
  if n <> 0 then raise exception '⛔ % liens CASSES apres le re-gel', n; end if;
  select count(*) into m from app_v_classeur_lien_casse;
  if m <> 9 then
    raise exception '⛔ la vue des liens casses passe a % (elle etait a 9)', m;
  end if;

  -- ⭐ les lignes du classeur couvertes MONTENT ou restent egales, jamais moins
  select count(distinct id_unique) into n from app_classeur_lien;
  if n < 4702 then
    raise exception '⛔ le gel ne couvre plus que % lignes au lieu de 4 702', n;
  end if;

  raise notice '✅ 195 liens poses . le gel passe de 12 595 a 12 790 . % lignes couvertes', n;
end $$;

commit;
