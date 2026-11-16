-- ════════════════════════════════════════════════════════════════════════════
-- B1 -- LES 6 COLONNES QUI MANQUENT AU CHANTIER CLASSEUR          16/11/2026
-- ════════════════════════════════════════════════════════════════════════════
--
-- SON ENONCE, AU PLAN : « CREER LES 6 COLONNES MANQUANTES (9 = 3 qui existent
--   + 6) : Y Vente Reglee . AA N0 de facture -> colonnes de CLASSE A ;
--   AH Avis a envoyer . AI Commentaire Avis . AJ Avis envoye -> table a part,
--   cle id_unique (aucune colonne "avis" n'existe dans TOUTE la base) ;
--   C numero_mandat_app -> PREALABLE DU 29/10 JAMAIS FAIT. »
--
-- ⛔ B1 BLOQUE C8 ET C9 -- les deux plus gros postes du chantier :
--      C8  Y et AA remplis : 3 756 + 3 741 valeurs (mesure A1 du 16/11)
--      C9  AH AI AJ : 2 266 + 392 + 2 405 valeurs, et le numero de mandat
--
-- ⭐ CLASSE A, ET C'EST TOUT LE SUJET. Une colonne de classe A est un champ que
--   HEKTOR IGNORE : l'app seule l'ecrit, `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` la
--   retient au push, et la redescente la ramene. A l'inverse, `numero_mandat` est
--   de CLASSE C -- Hektor le calcule, et toute ecriture y est EFFACEE au run
--   suivant. D'ou `numero_mandat_app`, a cote et non a la place.
--
-- ⛔⛔ L'ORDRE N'EST PAS NEGOCIABLE : SUPABASE D'ABORD, LE CODE ENSUITE.
--   C'est ecrit dans affaire_ledger.py : « les colonnes sont POSEES CHEZ SUPABASE
--   DEPUIS CE JOUR -- dans cet ordre, jamais l'inverse : une colonne locale que
--   Supabase n'a pas est reclamee pour rien a la redescente (c'est l'etat ou dort
--   app_dossier_uuid depuis le 09/11) ».
--   ➡ Ce patch ne fait QUE la base. L'ajout aux trois listes du code vient apres.
--
-- ⚠⚠ ET LE TYPE DE Y EST UNE DECISION FONDEE SUR A1, PAS UNE HABITUDE :
--   A1 (16/11) a mesure que Y porte 2 962 dates ET 794 TEXTES (« 29 decembre23 »),
--   soit 21 % -- « une sur cinq », le defaut des deux formats deja paye le 14/11.
--   ⛔ UNE COLONNE `date` PERDRAIT CES 794 VALEURS A L'INSERTION, EN SILENCE.
--   Elles entrent donc en TEXT, brutes, et la lecture tolerante viendra dans C8.
--   Meme raison pour AA (« GGTI00003620 » n'est pas un nombre) et pour les avis
--   (AH melange oui/OUI/non/NON/« pas acq. », AJ porte des PRENOMS).
--
-- RETOUR ARRIERE : patch_b1_colonnes_classeur_2026-11-16_INVERSE.sql
-- CONTROLES      : patch_b1_colonnes_classeur_2026-11-16_REPETITION.sql
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- ── LES GARDES : rien ne doit exister avant, et rien ne doit etre ecrase
do $$
begin
  if exists (select 1 from information_schema.columns
              where table_schema = 'public' and table_name = 'app_affaire_ledger'
                and column_name in ('vente_reglee_app','numero_facture_app','numero_mandat_app')) then
    raise exception 'ARRET : une de ces trois colonnes existe deja -- ce patch est le PREMIER';
  end if;
  if exists (select 1 from information_schema.tables
              where table_schema = 'public' and table_name = 'app_classeur_avis') then
    raise exception 'ARRET : app_classeur_avis existe deja';
  end if;
  -- ⭐ le temoin de ce qu'on NE touche PAS : numero_mandat (classe C) doit rester
  if not exists (select 1 from information_schema.columns
                  where table_schema = 'public' and table_name = 'app_affaire_ledger'
                    and column_name = 'numero_mandat') then
    raise exception 'ARRET : numero_mandat a disparu -- la base n est pas celle attendue';
  end if;
end $$;

-- ── ① Y ET AA : DEUX COLONNES DE CLASSE A SUR LE REGISTRE
alter table public.app_affaire_ledger
  add column vente_reglee_app  text,   -- Y  « Vente Reglee » -- TEXT : 794 non-dates
  add column numero_facture_app text;  -- AA « Numero de facture » -- « GGTI00003620 »

comment on column public.app_affaire_ledger.vente_reglee_app is
  'Classeur, colonne Y « Vente Reglee ». CLASSE A : l app seule l ecrit, le push ne '
  'l envoie pas, la redescente la ramene. TEXT ET NON date : A1 du 16/11 a mesure '
  '2 962 dates ET 794 textes (« 29 decembre23 »), soit 21 %% -- une colonne date les '
  'perdrait en silence. La lecture tolerante est la charge de C8.';
comment on column public.app_affaire_ledger.numero_facture_app is
  'Classeur, colonne AA « Numero de facture ». CLASSE A. TEXT : « GGTI00003620 », '
  '« GTI6300000169 », « G432210 » -- 3 735 valeurs distinctes sur 3 741.';

-- ── ② LE PREALABLE DU 29/10, JAMAIS FAIT : notre numero de mandat
alter table public.app_affaire_ledger
  add column numero_mandat_app text;

comment on column public.app_affaire_ledger.numero_mandat_app is
  'Classeur, colonne C. CLASSE A, et c est TOUT L INTERET : `numero_mandat` est de '
  'CLASSE C -- Hektor le calcule et toute ecriture y est EFFACEE au run suivant. '
  'Cette colonne-ci est a COTE, jamais a la place. Prealable du 29/10, pose le 16/11. '
  'ATTENTION : 33 numeros du classeur sont RECYCLES aux charges divergentes -- un '
  'numero n identifie pas un mandat (4 142 doublons mesures).';

-- ── ③ LES AVIS : UNE TABLE A PART, CAR RIEN N EXISTE DANS TOUTE LA BASE
--     Cle `id_unique` : la ligne du classeur, et JAMAIS le numero de ligne
--     (« une seule ligne vide au milieu et tout glisse » -- lecon du 04/11).
create table public.app_classeur_avis (
  id_unique        text primary key,
  avis_a_envoyer   text,          -- AH : oui/OUI/non/NON/« pas acq. »  -> BRUT
  commentaire_avis text,          -- AI : « ok » 195, « 1 » 115
  avis_envoye      text,          -- AJ : « ok » 1 700, puis des PRENOMS
  origine          text not null default 'classeur',
  ecrit_le         timestamptz not null default now(),
  ecrit_par        text
);

comment on table public.app_classeur_avis is
  'Classeur, colonnes AH AI AJ (le suivi d envoi des avis). Table a part parce '
  'qu AUCUNE colonne « avis » n existe dans toute la base (mesure du 16/11). '
  'Les trois valeurs entrent BRUTES, sans normaliser : AH melange oui/OUI/non/NON '
  'et « pas acq. » / « pas vend. » (120 valeurs distinctes), AJ porte des PRENOMS '
  '(Marion 192, Nico 59, Claire 24). ⭐ ET AH/AJ NE SE CONTREDISENT PAS : AH dit '
  '« a envoyer », AJ dit « envoye » -- deux etapes, pas deux versions.';

alter table public.app_classeur_avis enable row level security;

-- ⛔ AUCUN DROIT AU ROLE PUBLIC -- la regle du chantier n0 1 (08/10). Le service
--   role passe outre RLS ; `authenticated` n a rien tant que personne n en a besoin.
revoke all on public.app_classeur_avis from public;

-- ── CE QUI VIENT D'ETRE POSE, a lire dans la sortie
select column_name, data_type
  from information_schema.columns
 where table_schema = 'public' and table_name = 'app_affaire_ledger'
   and column_name in ('vente_reglee_app','numero_facture_app','numero_mandat_app',
                       'numero_mandat','transaction_origine')
 order by column_name;

select column_name, data_type, is_nullable
  from information_schema.columns
 where table_schema = 'public' and table_name = 'app_classeur_avis'
 order by ordinal_position;

-- ── LES CONTROLES, AVANT LE COMMIT
do $$
declare
  neuves integer;
  avis   integer;
  lignes integer;
begin
  select count(*) into neuves from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaire_ledger'
     and column_name in ('vente_reglee_app','numero_facture_app','numero_mandat_app');
  if neuves <> 3 then
    raise exception 'ARRET : %s colonne(s) creees au lieu de 3', neuves;
  end if;

  select count(*) into avis from information_schema.columns
   where table_schema = 'public' and table_name = 'app_classeur_avis';
  if avis <> 7 then
    raise exception 'ARRET : app_classeur_avis a %s colonnes au lieu de 7', avis;
  end if;

  -- ⭐ LE TEMOIN : on n a RIEN touche au registre. Pas une ligne, pas une valeur.
  select count(*) into lignes from app_affaire_ledger;
  if lignes <> 31253 then
    raise exception 'ARRET : le registre porte %s lignes au lieu de 31 253 -- NE PAS VALIDER', lignes;
  end if;
  if exists (select 1 from app_affaire_ledger
              where vente_reglee_app is not null or numero_facture_app is not null
                 or numero_mandat_app is not null) then
    raise exception 'ARRET : une des colonnes neuves porte deja une valeur';
  end if;

  raise notice 'OK : 3 colonnes de classe A + la table des avis (7 colonnes), registre intact a %s lignes', lignes;
end $$;

commit;
