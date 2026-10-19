-- ============================================================================
-- REPETITION -- reparer les 103 photos masquees
-- 19/10/2026
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l ERREUR VOLONTAIRE de la derniere font que RIEN n est ecrit.
--
-- Elle joue dans l'ordre REEL : mesures AVANT (dont le TEMOIN INVERSE : ces
-- photos sont-elles vraiment invisibles dans l'app aujourd'hui ?) -> LE VRAI
-- PATCH -> mesures APRES -> LE VRAI INVERSE -> mesure du RETOUR -> erreur.
--
-- LE MESSAGE ATTENDU si tout va bien :
--    1-avant  | masquees ET marquees absentes  = 103
--    1-avant  | masquees ET presentes          = 0
--    1-avant  | une seule date d absence       = oui (2026-10-15 21:23:23.635+00)
--    1-avant  | TEMOIN INVERSE : vues au panneau de l app = 0 sur 103 -- elles sont bien perdues
--    1-avant  | annonces concernees            = 14, toutes ARCHIVEES
--    2-apres  | masquees ET marquees absentes  = 0
--    2-apres  | masquees ET presentes          = 103
--    2-apres  | vues au panneau de l app       = 103 sur 103
--    2-apres  | elles restent MASQUEES         = oui (visible toujours false)
--    2-apres  | hors_vitrine_depuis INTACT     = 103 (on n y touche pas)
--    2-apres  | aucune n entre dans la galerie publique = 0 avec derives
--    3-retour | masquees ET marquees absentes  = 103
--    3-retour | la date d origine est revenue  = oui
-- ============================================================================

begin;

create temporary table essai_mesures (
  id serial, etape text, mesure text, valeur text
) on commit drop;

-- =============================== 1. AVANT ==================================

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'masquees ET marquees absentes  ', count(*)::text
from app_console_photo where visible is false and present_in_hektor is false;

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'masquees ET presentes          ', count(*)::text
from app_console_photo where visible is false and present_in_hektor is true;

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'une seule date d absence       ',
       case when count(distinct absent_depuis) = 1
            then 'oui (' || min(absent_depuis)::text || ')'
            else 'NON : ' || count(distinct absent_depuis)::text || ' dates' end
from app_console_photo where visible is false and present_in_hektor is false;

-- ⭐ LE TEMOIN INVERSE. Sans lui, on repare peut-etre un probleme qui n'existe
--   pas. `loadConsolePhotos` (App.tsx) filtre `present_in_hektor = true` : on
--   reproduit EXACTEMENT ce filtre pour compter ce que l'ecran montre.
insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'TEMOIN INVERSE : vues au panneau',
       count(*) filter (where present_in_hektor is true)::text
       || ' sur ' || count(*)::text
       || case when count(*) filter (where present_in_hektor is true) = 0
               then ' -- elles sont bien perdues pour l app'
               else ' -- ATTENTION, elles ne sont pas toutes perdues' end
from app_console_photo where visible is false;

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'annonces concernees            ',
       count(distinct p.app_dossier_id)::text || ', dont '
       || count(distinct p.app_dossier_id) filter (
            where exists (select 1 from app_archive_annonce_index_current a
                           where a.app_archive_id = p.app_dossier_id))::text
       || ' ARCHIVEES'
from app_console_photo p where p.visible is false;

-- ====================== 2. LE VRAI PATCH, copie conforme ====================

do $do$
declare
  v_avant   integer;
  v_apres   integer;
  v_ecrites integer;
begin
  select count(*) into v_avant
    from public.app_console_photo
   where visible is false and present_in_hektor is false;

  if v_avant = 0 then
    raise notice 'DEJA FAIT : aucune photo masquee n est marquee absente';
    return;
  end if;

  if v_avant <> 103 then
    raise exception 'STOP : % photos dans ce cas (attendu 103). La population a bouge : remesurer avant de reparer.', v_avant;
  end if;

  raise notice 'RAPPEL : ce patch suppose le VERROU 7 pose (test_masquee_pas_supprimee.js = 17 verts).';

  update public.app_console_photo
     set present_in_hektor = true,
         absent_depuis = null
   where visible is false and present_in_hektor is false;
  get diagnostics v_ecrites = row_count;

  select count(*) into v_apres
    from public.app_console_photo
   where visible is false and present_in_hektor is false;

  if v_apres <> 0 then
    raise exception 'STOP : il reste % masquees marquees absentes apres reparation', v_apres;
  end if;
  if v_ecrites <> v_avant then
    raise exception 'STOP : % lignes ecrites pour % attendues', v_ecrites, v_avant;
  end if;
end
$do$;

-- =============================== 3. APRES ==================================

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'masquees ET marquees absentes  ', count(*)::text
from app_console_photo where visible is false and present_in_hektor is false;

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'masquees ET presentes          ', count(*)::text
from app_console_photo where visible is false and present_in_hektor is true;

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'vues au panneau de l app       ',
       count(*) filter (where present_in_hektor is true)::text || ' sur ' || count(*)::text
from app_console_photo where visible is false;

-- ⚠ ELLES DOIVENT RESTER MASQUEES. Le patch repare le marquage, PAS le drapeau :
--   elles SONT masquees chez Hektor, c'est la verite et on la garde.
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'elles restent MASQUEES         ',
       case when count(*) = 103 then 'oui (visible toujours false)'
            else 'NON : ' || count(*)::text || ' au lieu de 103' end
from app_console_photo where visible is false;

-- ⚠ `hors_vitrine_depuis` est JUSTE (leurs annonces sont des archives) : intact.
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'hors_vitrine_depuis INTACT     ',
       count(*) filter (where hors_vitrine_depuis is not null)::text || ' sur ' || count(*)::text
from app_console_photo where visible is false;

-- ⛔ ET AUCUNE N'ENTRE DANS LA GALERIE PUBLIQUE : la fonction qui la fabrique
--   exige les deux derives, et elles n'en ont aucun.
insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'entrent dans la galerie publique',
       count(*) filter (where derives_json ? 'w400' and derives_json ? 'w1600')::text
       || ' sur ' || count(*)::text || ' (0 attendu)'
from app_console_photo where visible is false;

-- ========================== 4. LE VRAI INVERSE =============================

do $inv$
declare
  v_cibles  integer;
  v_ecrites integer;
  v_reste   integer;
  v_date    constant timestamptz := '2026-10-15 21:23:23.635+00';
begin
  select count(*) into v_cibles
    from public.app_console_photo
   where visible is false and present_in_hektor is true;

  if v_cibles = 0 then
    raise notice 'RIEN A DEFAIRE';
    return;
  end if;
  if v_cibles <> 103 then
    raise exception 'STOP : % photos masquees et presentes (attendu 103)', v_cibles;
  end if;

  update public.app_console_photo
     set present_in_hektor = false,
         absent_depuis = v_date
   where visible is false and present_in_hektor is true;
  get diagnostics v_ecrites = row_count;

  select count(*) into v_reste
    from public.app_console_photo
   where visible is false and present_in_hektor is true;
  if v_reste <> 0 then
    raise exception 'STOP : il reste % masquees presentes apres le retour', v_reste;
  end if;
end
$inv$;

-- =============================== 5. RETOUR =================================

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'masquees ET marquees absentes  ', count(*)::text
from app_console_photo where visible is false and present_in_hektor is false;

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'la date d origine est revenue  ',
       case when count(*) = 103 and count(distinct absent_depuis) = 1
                 and min(absent_depuis) = '2026-10-15 21:23:23.635+00'::timestamptz
            then 'oui, a la milliseconde'
            else 'NON : ' || coalesce(min(absent_depuis)::text,'(aucune)') end
from app_console_photo where visible is false and present_in_hektor is false;

-- ================== 6. L ERREUR VOLONTAIRE : tout est annule ================
-- ⚠ Le compte rendu voyage DANS le message : un SELECT d une transaction qui
--   echoue n est pas toujours rendu par l editeur SQL.

do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai_mesures;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit.' || chr(10) || v_txt;
end
$fin$;

rollback;
