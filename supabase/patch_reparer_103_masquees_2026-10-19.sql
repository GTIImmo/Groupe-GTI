-- ============================================================================
-- REPARER LES 103 PHOTOS MASQUEES DECLAREES « DISPARUES » A TORT
-- 19/10/2026 · decision de Frederic : « 1. reparer »
-- ============================================================================
-- CE QUI S'EST PASSE. Le 15/10 a 23:23, la toute premiere nuit de « GTI
-- Entretien Documents », sa ligne 4/4 (accorder_photos_miroir.js --appliquer) a
-- declare « disparues de Hektor » 440 photos. Elle compare notre registre au
-- MIROIR, qui vient de l'API detail de Hektor -- QUI NE LISTE QUE LES VISIBLES.
--   · 337 l'etaient vraiment (reportages remplaces)  -> marquage JUSTE
--   · 103 etaient MASQUEES, pas supprimees           -> marquage FAUX
--
-- ⭐⭐ PROUVE A 100 %, PAS A 73 %. Les 14 annonces ont ete sondees UNE PAR UNE
--   chez Hektor, en lecture seule (mode=vignettes_hidden), les 18 et 19/10 :
--     32704=19  59434=14  40563=14  28509=12  61521=10  18724=6  32709=6
--     59559=5   59110=5   43435=4   11=4      28488=2   49544=1  59603=1
--   Somme = 103, et CHAQUE compte correspond EXACTEMENT au notre.
--   ➡ Les 103 photos sont TOUJOURS chez Hektor. Aucune n'a ete supprimee.
--
-- POURQUOI CA COMPTE, au-dela des 14 archives concernees : ces 103 masquees et
--   les 140 visibles des memes annonces (243 photos, entrees le 17/08 par
--   `sync_hektor_photos`) sont les SEULES du parc dont le drapeau `visible` dise
--   la verite. Les 441 000 autres portent `visible = true` PAR DEFAUT, parce que
--   le rattrapage de masse lit le miroir et ne sait pas lire les masquees.
--   Les perdre, c'est perdre les seuls cas reels pour eprouver le futur bouton.
--
-- ⚠ CE PATCH NE SE SUFFIT PAS A LUI-MEME, ET C'EST ESSENTIEL :
--   sans le VERROU 7 (pose le 19/10 dans accorder_photos_miroir.js), la tache de
--   21:00 LES RE-MARQUERAIT DES CE SOIR. Le verrou est donc un PREALABLE, et il
--   est deja en place -- verifiable : la fonction `drapeauVisible` existe dans le
--   script, et son epreuve (Console/test_masquee_pas_supprimee.js) rend 17 verts.
--
-- CE QUE CA NE TOUCHE PAS :
--   · `hors_vitrine_depuis` reste pose -- il est JUSTE : leurs 14 annonces sont
--     des ARCHIVES, et c'est l'ancre des six mois (G.8). Rien a y changer.
--   · `visible` reste a false -- elles SONT masquees chez Hektor, c'est la verite.
--   · aucun fichier, aucun derive, aucun appel a Hektor.
--   · le coffre public : ces 103 n'y ont AUCUN derive (mesure : 0 sur 103).
--
-- CE QUE CA CHANGE, et c'est tout :
--   · elles redeviennent visibles DANS LE PANNEAU PHOTOS DE L'APP
--     (`loadConsolePhotos` filtre `present_in_hektor = true`) ;
--   · elles redeviennent eligibles aux gestes (la RPC exige present_in_hektor) ;
--   · ⚠ `updated_at` bouge -> la descente de 07:45 les re-descendra. 103 lignes,
--     sans consequence.
--   ⛔ ELLES N'ENTRENT PAS DANS LA GALERIE PUBLIQUE : `app_photos_remplir_
--     adresses_app` exige `derives_json ? 'w400' AND ? 'w1600'`, et elles n'en
--     ont aucun. (Et de toute facon leurs annonces sont archivees.)
--
-- INVERSE : patch_reparer_103_masquees_2026-10-19_INVERSE.sql
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $do$
declare
  v_avant   integer;
  v_apres   integer;
  v_ecrites integer;
  v_verrou  boolean;
begin
  -- ⓵ COMBIEN SONT DANS CE CAS ? On compte AVANT, et on refuse une surprise.
  select count(*) into v_avant
    from public.app_console_photo
   where visible is false and present_in_hektor is false;

  if v_avant = 0 then
    raise notice 'DEJA FAIT : aucune photo masquee n est marquee absente';
    return;
  end if;

  -- ⚠ LE GARDE-FOU DU NOMBRE. 103 est le compte mesure et PROUVE une par une.
  --   Un nombre different veut dire que la population a bouge depuis -- on
  --   s'arrete et on remesure, on ne repare pas a l'aveugle.
  if v_avant <> 103 then
    raise exception 'STOP : % photos dans ce cas (attendu 103). La population a bouge : remesurer avant de reparer.', v_avant;
  end if;

  -- ⓶ LE PREALABLE : le verrou doit etre en place, sinon on repare pour rien
  --    (la tache de 21:00 les re-marquerait ce soir).
  --    ⚠ On ne peut pas lire un fichier JS depuis Postgres : ce controle ne peut
  --      donc PAS etre automatique ici. Il est fait par l'epreuve
  --      Console/test_masquee_pas_supprimee.js (17 verts le 19/10), et redit ici
  --      pour que personne ne colle ce patch sans y avoir pense.
  raise notice 'RAPPEL : ce patch suppose le VERROU 7 pose (test_masquee_pas_supprimee.js = 17 verts).';

  -- ⓷ LA REPARATION. On ne touche QUE les deux colonnes du marquage.
  update public.app_console_photo
     set present_in_hektor = true,
         absent_depuis = null
   where visible is false and present_in_hektor is false;
  get diagnostics v_ecrites = row_count;

  -- ⓸ LE CONTROLE DE SORTIE : plus aucune masquee marquee absente.
  select count(*) into v_apres
    from public.app_console_photo
   where visible is false and present_in_hektor is false;

  if v_apres <> 0 then
    raise exception 'STOP : il reste % masquees marquees absentes apres reparation', v_apres;
  end if;
  if v_ecrites <> v_avant then
    raise exception 'STOP : % lignes ecrites pour % attendues', v_ecrites, v_avant;
  end if;

  raise notice 'REPARE : % photos masquees redeviennent presentes chez Hektor (0 restante).', v_ecrites;
end
$do$;

commit;
