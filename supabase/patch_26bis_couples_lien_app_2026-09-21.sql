-- ═══════════════════════════════════════════════════════════════════════════
-- 26bis-COUPLES — LE LIEN DE MENAGE S'ECRIT EN NUMERO D'APP       21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- CE QUE HEKTOR FAIT. Chaque contact porte un `refCouple`, numero de MENAGE qui
-- vaut l'identifiant de la fiche portant l'identite. Quand la civilite est
-- « Mr./Mme », Hektor cree une SECONDE fiche, vide, pour le second membre. Chez
-- GTI elle n'a jamais ete remplie : 133 343 contacts sans nom ni prenom, dont
-- 96 877 nommables par ce lien (mesure du 11/09).
--
-- LE DEFAUT, TEL QUE LA TACHE LE POSE : le lien est ecrit en NUMERO HEKTOR. Il
-- pointe donc vers une serie qui n'est pas la notre -- et le jour ou un contact
-- naitra dans l'app, son conjoint n'aura aucun numero Hektor a designer.
--
-- CE PATCH POSE LE LIEN EN NUMERO D'APP, A COTE, sans toucher a l'autre :
--    hektor_couple_contact_id  le lien tel que Hektor l'ecrit   (on n'y touche pas)
--    app_couple_contact_id     le meme lien, dans NOTRE serie   (nouveau)
--
-- ⚠ POURQUOI EN SQL, ET PAS DANS LA COUCHE LOCALE. L'empreinte du push couvre
--   toutes les colonnes : ajouter une colonne cote local changerait les 200 000
--   empreintes et renverrait tout d'un coup -- c'est ce qui a sature Supabase le
--   22/08, et c'est exactement le raisonnement qui a fait poser app_contact_id
--   du cote Postgres le 31/08. Meme trou, meme parade.
--
-- MESURE AVANT : 40 150 contacts portent un lien de menage dans l'app, dont
-- 37 398 traduisibles tout de suite (93 %). Les 2 752 autres pointent vers une
-- fiche que l'app ne porte pas -- perimetre des contacts eligibles, ou fiche
-- supprimee chez Hektor (14 080 liens sur 124 455 le sont, verifie par API en
-- septembre). Ces lignes gardent leur lien Hektor et attendent : rien ne se perd.
--
-- ⚠ CE PATCH N'AFFICHE RIEN. La regle « une personne, une ligne » est deja en
--   place a l'ecran depuis le 11/09. Ici on pose le lien dans notre serie, pour
--   qu'il survive a la renumerotation et a un conjoint ne dans l'app.
--
-- RETOUR ARRIERE :
--   drop view public.app_v_couples_non_traduits;
--   alter table public.app_contact_current drop column app_couple_contact_id;
-- ═══════════════════════════════════════════════════════════════════════════

alter table public.app_contact_current add column if not exists app_couple_contact_id bigint;

comment on column public.app_contact_current.app_couple_contact_id is
  '26bis-COUPLES 21/09/2026 : le lien de menage dans NOTRE serie (app_contact_id du conjoint). Pose a cote de hektor_couple_contact_id, qui reste tel quel. Le jour de la renumerotation, ce lien ne bouge pas.';

-- ── LE REMPLISSAGE, PAR AUTO-JOINTURE ──────────────────────────────────────
update public.app_contact_current c
   set app_couple_contact_id = p.app_contact_id
  from public.app_contact_current p
 where coalesce(c.hektor_couple_contact_id, '') <> ''
   and p.hektor_contact_id = c.hektor_couple_contact_id
   and p.app_contact_id is not null
   and c.app_couple_contact_id is distinct from p.app_contact_id;

-- ── CE QUI RESTE INTRADUISIBLE, ET POURQUOI ────────────────────────────────
create or replace view public.app_v_couples_non_traduits as
  select c.hektor_contact_id, c.hektor_couple_contact_id, c.display_name,
         case when not exists (select 1 from public.app_contact_current p
                                where p.hektor_contact_id = c.hektor_couple_contact_id)
              then 'conjoint absent de l app'
              else 'conjoint sans numero d app' end as raison
    from public.app_contact_current c
   where coalesce(c.hektor_couple_contact_id, '') <> ''
     and c.app_couple_contact_id is null;

comment on view public.app_v_couples_non_traduits is
  '26bis-COUPLES 21/09/2026 : liens de menage que l''app ne sait pas ecrire dans sa serie. Attendu > 0 (perimetre eligible, fiches supprimees chez Hektor) ; ce qui compte est que le nombre NE MONTE PAS.';

grant select on public.app_v_couples_non_traduits to service_role, authenticated;
