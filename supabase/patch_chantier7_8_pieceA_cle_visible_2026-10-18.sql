-- ============================================================================
-- (7)-8 PIECE A -- LA CLE `visible` ENTRE DANS NOTRE GALERIE
-- 18/10/2026
-- ============================================================================
-- POURQUOI. La vitrine publique (Ecrans Android/export_project_vitrine.py)
-- PORTE DEJA le bon filtre, depuis le 27/09 (regle G.15) :
--
--     def visible_photos(...):
--         for img in ordered:
--             if str(img.get("visible", "1")).strip() == "0":
--                 continue
--
-- MAIS IL EST INERTE : notre galerie `images_preview_json_app` porte QUATRE
-- cles -- `full, legend, order, url` -- et PAS `visible`. Mesure du 16/10 :
-- ZERO galerie sur 10 259 en porte une. Le filtre lit donc le defaut « 1 » et
-- ne mord jamais.
--
-- Le commentaire de la vitrine le frole : « LE FORMAT TOMBE JUSTE SANS
-- CONVERSION : nos entrees sont {url, full, order, legend} ». L'auteur avait
-- verifie `url` et `order`, sans voir que `visible` manquait.
--
-- CE PATCH AJOUTE LA CLE. IL NE FILTRE RIEN, et c'est le point :
--   . la VITRINE publique filtre (elle a deja le code) -> les masquees sortent
--   . l'APP garde les masquees a l'ecran -> on peut encore les demasquer
--   Filtrer a la source aurait prive l'app des masquees : l'app et la vitrine
--   lisent LE MEME blob (App.tsx:18698 lit images_preview_json, que api.ts a
--   deja remplace par la notre).
--
-- ⚠⚠ LA VALEUR EST UNE CHAINE '1' / '0', PAS UN BOOLEEN. Le filtre teste
--   `== "0"`. Un booleen jsonb `false` arrive en Python comme `False`, et
--   `str(False)` vaut « False », PAS « 0 » : le filtre ne mordrait toujours
--   pas. On emet donc '1'/'0', exactement comme Hektor dans son propre
--   images_json (mesure du 16/10 : 17 535 entrees, toutes a '1').
--
-- ⭐ `visible IS FALSE` et non `NOT visible` : une valeur NULL reste VISIBLE,
--   c'est la regle que porte deja le repli (`coalesce(img->>'visible','1')`).
--   On recopie la regle du projet, on n'en invente pas une seconde.
--
-- CE QUE CA NE CHANGE PAS -- mesure du 18/10, consommateur par consommateur :
--   . `photo_url_listing_app` = entrees->0->>'url' : INCHANGE (on n'ajoute
--     qu'une cle, l'ordre du tableau ne bouge pas).
--   . `app_photos_remplir_adresses_registre` : elle RECOPIE le blob, elle n'en
--     construit pas -- la cle s'y propage seule. ⚠ Elle recopiera les 10 259
--     galeries UNE FOIS, le blob ayant change de forme.
--   . le front (`galerieAppEnTexte`, `listingPreviewUrl`, `ListingThumbnail`,
--     App.tsx:18698) : tous lisent PAR CLE (`url`, `full`) et ignorent le reste.
--   . `app_get_dossier_photos` : lit app_console_photo en direct, pas le blob.
--   . `espace_client.py` (espace client) : il ne filtre PAS, et il re-trie par
--     `order`. ⛔ CE PATCH NE LE CORRIGE DONC PAS -- c'est la piece B, et je le
--     dis au lieu de laisser croire que (7)-8 est fini.
--   . aucun travail worker, aucun redemarrage, aucune RLS (SECURITY DEFINER).
--
-- EFFET REEL IMMEDIAT : AUCUN. Il n'existe aujourd'hui aucune photo
--   `visible = false AND present_in_hektor = true` (mesure du 16/10 : 0).
--   C'est un FILET POSE D'AVANCE, prealable au bouton « masquer » (piece C).
--
-- CE PATCH NE RECOPIE PAS LA FONCTION : il la LIT dans la base, verifie son
-- empreinte et que son ancre est unique, remplace, reexecute.
--   empreinte attendue (sans retours chariot) : 682e386007b59eda6e5dc54056c87693
--   ancre : UNE SEULE LIGNE, vue 1 fois (mesure du 18/10)
--   ANCRES MULTI-LIGNES : ZERO  (lecon du 15/10, payee trois fois)
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('''legend'', p.legend)', chr(13), '');
  v_neuf  text := replace('''legend'', p.legend, ''visible'', case when p.visible is false then ''0'' else ''1'' end)', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if v_src is null then
    raise exception 'STOP : app_photos_remplir_adresses_app introuvable';
  end if;

  if position(v_neuf in v_src) > 0 then
    raise notice 'DEJA FAIT : la cle visible est dans la galerie';
    return;
  end if;

  if md5(v_src) <> '682e386007b59eda6e5dc54056c87693' then
    raise notice 'ATTENTION : empreinte % (attendue 682e3860...) -- un autre patch est passe. On continue : l ancre unique et l absence du texte sont les vrais garde-fous.', md5(v_src);
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then
    raise exception 'STOP : l ancre apparait % fois (attendu 1)', v_vu;
  end if;

  v_new := replace(v_src, v_ancre, v_neuf);
  execute v_new;
  raise notice 'POSE : la galerie porte desormais la cle visible (chaine 1 / 0)';
end
$do$;

commit;
