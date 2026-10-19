-- ============================================================================
-- CHANTIER ⑦-8 -- LES DEUX BOITES : la boite PUBLIQUE ne porte plus de masquee
-- 19/10/2026                                        marche 1 sur 4 du point ⑦-8
-- ============================================================================
-- L'IDEE EST DE FREDERIC (19/10) : « mais on peut pas faire deux boites ? »
-- Et la deuxieme boite EXISTE DEJA.
--
--   la boite PUBLIQUE  = images_preview_json_app + photo_url_listing_app
--                        -> la vitrine Android, l'espace client, le portail de
--                           rapprochement, la galerie de la fiche
--   la boite COMPLETE  = la table app_console_photo elle-meme
--                        -> le PANNEAU PHOTOS (loadConsolePhotos, api.ts:7991),
--                           qui lit la TABLE et jamais la boite. C'est la que
--                           vivra le bouton masquer/afficher.
--
-- CE QUE CE PATCH FAIT : il ajoute « et la photo n'est pas masquee » aux DEUX
-- where de app_photos_remplir_adresses_app -- celui de la COUVERTURE (l. 50) et
-- celui de la GALERIE (l. 62).
--
-- ⭐ POURQUOI C'ETAIT NECESSAIRE, mesure du 19/10 : `p.visible desc nulls last`
--   est un TRI, JAMAIS UN FILTRE. La couverture prenait la premiere ligne (donc
--   une visible TANT QU'IL EN EXISTE UNE), mais le `jsonb_agg` de la galerie
--   prenait TOUT, les masquees a la fin. La seule barriere etait l'absence de
--   derives -- un hasard, pas une protection.
--
-- ⭐⭐ ET LE PROJET AVAIT DEJA ECRIT QUE C'ETAIT LE BON ENDROIT.
--   Console/accorder_photos_miroir.js, en-tete l. 92-96 :
--     « ET LE RESTE SE CORRIGE TOUT SEUL. [ce patch] recalcule
--       photo_url_listing_app et images_preview_json_app [...] Donc la vignette
--       du listing, celle du registre des mandats et LA GALERIE DU SITE PUBLIC
--       redeviennent justes au passage suivant du run, SANS TOUCHER UNE LIGNE
--       DE FRONT. »
--
-- CE QUE CA PROTEGE, SANS UNE LIGNE DE CODE AILLEURS :
--     vitrine Android publique ......... 0 ligne   (Ecrans Android/export_project_vitrine.py)
--     espace client (page du vendeur) .. 0 ligne   (espace_client.py:88, via la vue)
--     portail de rapprochement ......... 0 ligne   (espace_portal <- espace_client._photos:476)
--     ⭐ les envois pub pas encore ecrits .. 0 ligne, POUR TOUJOURS
--   -> la discipline (« ne pas oublier le filtre ») est remplacee par une
--      IMPOSSIBILITE. C'est pour ca que les pieces A et B sont ABANDONNEES.
--
-- ⭐ `visible is not false` ET NON `not visible` : un NULL doit rester VISIBLE.
--   C'est la regle que le projet porte deja (`coalesce(img->>'visible','1')` dans
--   la vitrine). On recopie la regle du projet, on n'en invente pas une seconde.
--
-- ⚠ L'ANCRE EST LA MEME POUR LES DEUX WHERE, ET C'EST VOULU :
--   `where p.present_in_hektor and p.derives_json` apparait EXACTEMENT 2 fois
--   (mesure du 19/10) -- une fois pour la couverture, une fois pour la galerie.
--   Un seul remplacement corrige les deux, et LE COMPTE EST VERIFIE (= 2) avant
--   d'ecrire. Si un jour il en apparaissait une 3e, le patch REFUSE.
--
-- ⚠⚠ ANCRE SUR UNE SEULE LIGNE + replace(chr(13)) DES DEUX COTES (lecon 30,
--   payee TROIS fois) : colle depuis Windows, ce fichier arrive en CRLF, et une
--   ancre multi-lignes ne se retrouverait plus dans un corps stocke en LF.
--   Mesure du 19/10 : le corps en base porte 0 retour chariot.
--
-- CE QUE CA CHANGE A L'ECRAN, ET QUI EST ASSUME :
--   · la GALERIE DE LA FICHE (App.tsx:18699-18706) ne montrera plus que les
--     visibles -> c'est JUSTE : elle montre ce que le public voit. Le PANNEAU
--     PHOTOS, lui, montre tout (il lit la table).
--   · ⭐ c'est exactement le dessin de Hektor lui-meme : deux galeries,
--     mode=vignettes et mode=vignettes_hidden.
--   · une annonce dont TOUTES les photos sont masquees affichera « Sans photo ».
--     C'est juste aussi -- et 0 annonce est dans ce cas (mesure du 19/10).
--
-- ⚠ LE PRIX, DIT : on continue de FABRIQUER les derives des masquees (aucun
--   changement a generer_derives_photos.js), donc leur w400/w1600 vit dans le
--   coffre PUBLIC : liste nulle part, mais ouvrable par qui connaitrait
--   l'adresse exacte. C'est deja vrai de TOUTES nos photos (regle G.8). C'est ce
--   qui rend le futur bouton « afficher » INSTANTANE -- l'arbitrage de Frederic.
--
-- CE QUE CA NE TOUCHE PAS :
--   · app_photos_remplir_adresses_registre : elle RECOPIE ce que les index
--     savent, donc elle herite du filtre sans etre modifiee ;
--   · app_console_photo_couverture_optimistic : son jsonb_agg fabrique l'ETAT
--     D'AVANT du retour arriere, elle n'ecrit PAS la boite (0 occurrence des
--     deux colonnes, mesure du 19/10) -- et elle exige DEJA une cible VISIBLE ;
--   · le drapeau `visible` lui-meme : personne ne l'ecrase (accorder_photos_
--     miroir.js, en-tete l. 88 : « ON NE TOUCHE PAS AU DRAPEAU visible »).
--
-- RETOUR ARRIERE : patch_chantier7_8_deux_boites_2026-10-19_INVERSE.sql
-- EPREUVE       : patch_chantier7_8_deux_boites_2026-10-19_REPETITION.sql
--                 ⚠ elle FABRIQUE la situation (0 masquee n'a de derive
--                   aujourd'hui, donc une epreuve naive serait verte pour rien).
--
-- CONTROLE APRES COLLAGE : la condition doit apparaitre 2 fois, et le run de
-- nuit remettra les boites d'aplomb au passage suivant de
-- Console/remplir_adresses_photos.js (seul appelant).
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $do$
declare
  v_src   text;
  v_new   text;
  -- ⚠ UNE SEULE LIGNE, et chr(13) retire des DEUX cotes (lecon 30).
  v_ancre text := replace('where p.present_in_hektor and p.derives_json', chr(13), '');
  v_neuf  text := replace('where p.present_in_hektor and p.visible is not false and p.derives_json', chr(13), '');
  v_emp   constant text := '682e386007b59eda6e5dc54056c87693';
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if v_src is null then
    raise exception 'STOP : public.app_photos_remplir_adresses_app est introuvable';
  end if;

  -- ⓵ DEJA FAIT ? On ne rejoue pas, et on ne crie pas.
  if position(v_neuf in v_src) > 0 then
    raise notice 'DEJA FAIT : la condition est posee % fois -- rien a ecrire.',
      (length(v_src) - length(replace(v_src, v_neuf, ''))) / length(v_neuf);
    return;
  end if;

  -- ⓶ L'EMPREINTE DE DEPART. Si elle differe, la fonction a bouge depuis la
  --    mesure du 19/10 : on ne patche pas a l'aveugle.
  if md5(v_src) <> v_emp then
    raise exception 'STOP : empreinte % au lieu de % -- la fonction a change depuis la mesure du 19/10. La RELIRE avant de patcher.',
      md5(v_src), v_emp;
  end if;

  -- ⓷ L'ANCRE DOIT APPARAITRE EXACTEMENT 2 FOIS : la couverture ET la galerie.
  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 2 then
    raise exception 'STOP : l ancre apparait % fois (attendu 2 : le where de la COUVERTURE et celui de la GALERIE)', v_vu;
  end if;

  v_new := replace(v_src, v_ancre, v_neuf);

  -- ⓸ LES CONTROLES AVANT D'ECRIRE
  if (length(v_new) - length(replace(v_new, v_neuf, ''))) / length(v_neuf) <> 2 then
    raise exception 'STOP : la forme neuve n apparait pas 2 fois apres remplacement';
  end if;
  if position(v_ancre in replace(v_new, v_neuf, '')) > 0 then
    raise exception 'STOP : il reste une ancre NON traitee -- remplacement incomplet';
  end if;
  if v_new = v_src then
    raise exception 'STOP : le patch n a RIEN change (lecon 2 : un patch doit changer quelque chose)';
  end if;

  execute v_new;

  -- ⓹ RELECTURE EN BASE -- on ne croit pas, on verifie.
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  v_vu := (length(v_src) - length(replace(v_src, v_neuf, ''))) / length(v_neuf);
  if v_vu <> 2 then
    raise exception 'STOP : apres ecriture, la condition apparait % fois (attendu 2)', v_vu;
  end if;
  if position(v_ancre in replace(v_src, v_neuf, '')) > 0 then
    raise exception 'STOP : apres ecriture, une ancre nue subsiste';
  end if;

  raise notice 'POSE : « visible is not false » est dans les DEUX where (couverture + galerie). Nouvelle empreinte : %', md5(v_src);
  raise notice 'La boite PUBLIQUE ne peut plus porter une masquee. Le PANNEAU PHOTOS, qui lit la table, les voit toujours.';
  raise notice 'Les boites existantes se remettront d aplomb au prochain passage de Console/remplir_adresses_photos.js (run de nuit).';
end
$do$;

commit;
