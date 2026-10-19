#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble la REPETITION de ⑦-8 marche 4 en EXTRAYANT le patch verbatim.
                                                                    19/10/2026
⭐⭐ POURQUOI UN GENERATEUR, ET PAS UNE REPETITION ECRITE A LA MAIN.
   Le patch porte ~190 lignes (les 3 verrous + la RPC). Les recopier a la main
   dans la repetition, c'est risquer UNE divergence invisible -- et alors
   j'eprouverais une IMITATION, pas le code. C'est l'avertissement du 03/10 :
   « l'epreuve de la veille testait une imitation, pas le vrai code ».
   ➡ Ici la repetition est ASSEMBLEE A PARTIR DU PATCH. Le corps joue est le
     patch, a l'octet pres, et le generateur le VERIFIE (empreinte md5 des deux
     cotes, imprimee a la fin).

   ⚠ A REJOUER si le patch change : le fichier de repetition est un PRODUIT.
     python <ce fichier>
"""
import hashlib
import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:/Hektor/Projet/supabase")
PATCH = R / "patch_chantier7_8_marche4_visibilite_2026-10-19.sql"
SORTIE = R / "patch_chantier7_8_marche4_visibilite_2026-10-19_REPETITION.sql"

src = PATCH.read_text(encoding="utf-8")

# ── L'EXTRACTION : de « ① LA CONTRAINTE » jusqu'avant le COMMIT final ────────
# ⚠ On ancre sur des reperes du patch, et on VERIFIE qu'ils sont uniques :
#   une ancre qui apparait deux fois donnerait un corps tronque en silence.
for ancre in ("-- ① LA CONTRAINTE DES TYPES", "\nCOMMIT;"):
    if src.count(ancre) != 1:
        raise SystemExit(f"ANCRE NON UNIQUE ({src.count(ancre)}x) : {ancre!r} -- rien genere")

debut = src.index("-- ① LA CONTRAINTE DES TYPES")
fin = src.index("\nCOMMIT;")
corps = src[debut:fin].rstrip() + "\n"

# Les quatre poses doivent etre la, sinon l'extraction a rate.
for repere, nom in (("ALTER TABLE public.app_console_job ADD CONSTRAINT", "la contrainte"),
                    ("app_console_can_request_job", "les droits"),
                    ("app_console_claim_next_job", "la distribution"),
                    ("CREATE OR REPLACE FUNCTION public.app_console_photo_visibilite_optimistic", "la RPC")):
    if repere not in corps:
        raise SystemExit(f"EXTRACTION INCOMPLETE : {nom} absente -- rien genere")

EN_TETE = """-- ============================================================================
-- REPETITION -- le geste « masquer / afficher une photo » (⑦-8 marche 4)
-- 19/10/2026
-- ⚠⚠ FICHIER GENERE -- ne pas le modifier a la main.
--    Source : patch_chantier7_8_marche4_visibilite_2026-10-19.sql
--    Generateur : scratchpad/generer_repetition_marche4.py
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l'ERREUR VOLONTAIRE de la derniere font que RIEN n'est ecrit -- ni les trois
--    verrous, ni la RPC, ni le drapeau de la photo, ni le travail.
--
-- ⭐⭐ LE CORPS JOUE EST LE PATCH, EXTRAIT A L'OCTET PRES, pas recopie a la main.
--   Recopier 190 lignes, c'est risquer une divergence invisible -- et alors on
--   eprouve une IMITATION (avertissement du 03/10). Le generateur verifie
--   l'empreinte des deux cotes.
--
-- ELLE JOUE DANS L'ORDRE REEL : mesures AVANT -> LE VRAI PATCH -> le geste sur une
-- VRAIE annonce, DANS LES DEUX SENS -> les refus -> LE VRAI INVERSE -> le retour.
--
-- LA CIBLE : le BAC A SABLE 62774 (app_dossier_id 3828957, 4 photos), photo
--   visible n° 482253. ⭐ C'est le bien d'essai designe du projet.
--
-- ⛔⛔ ELLE N'APPELLE PAS HEKTOR. Elle eprouve LA BASE : les trois verrous et la
--   RPC. Le geste CHEZ HEKTOR est la piece 2 (le worker) et il ne se prouve que
--   par un ESSAI REEL -- accord separe.
--
-- LE MESSAGE ATTENDU si tout va bien :
--   1-avant  | la contrainte / les droits / la distribution  = non, non, non
--   1-avant  | la RPC existe                                 = non
--   1-avant  | 62774 : photos / visibles                     = 4 / 4
--   1-avant  | la photo 482253 est                           = visible
--   2-patch  | la contrainte / les droits / la distribution  = OUI, OUI, OUI
--   2-patch  | la RPC existe (4 parametres)                  = OUI
--   2-patch  | anon peut l appeler                           = NON
--   3-masque | le retour est ok                              = oui, visible=false
--   3-masque | la photo 482253 est devenue                   = masquee
--   3-masque | LE POST-IT est pose (index marques)           = 1 ou plus
--   3-masque | adresses_app_le de 62774                      = A BLANC
--   3-masque | le travail cree, du bon type                  = set_hektor_photo_visibility
--   3-masque | sa charge porte l etat d avant                = true (visible)
--   3-masque | visibles restantes / plus_aucune_visible      = 3 / non
--   4-rejoue | rejouer le MEME masquage                      = deja_dans_cet_etat
--   5-affich | on la REAFFICHE                               = oui, visible=true
--   6-refus  | une photo inconnue                            = photo_introuvable_chez_hektor
--   6-refus  | des parametres vides                          = parametres_incomplets
--   6-refus  | sous l identite d un commercial               = ce que la garde repond VRAIMENT
--   7-retour | la RPC a disparu / les 3 verrous non plus     = oui, oui
-- ============================================================================

begin;

set local lock_timeout = '10s';

create temporary table essai (id serial, etape text, mesure text, valeur text) on commit drop;
create temporary table cible as
  select 3828957::bigint as dossier, '62774'::text as annonce, '482253'::text as photo;

-- ⚠ LA CIBLE EST VERIFIEE AVANT TOUT : un numero ne se devine pas, et une
--   epreuve sur la mauvaise ligne ne prouve rien.
do $garde$
declare v_n integer;
begin
  select count(*) into v_n from public.app_dossier_current d, cible c
   where d.app_dossier_id = c.dossier and d.hektor_annonce_id::text = c.annonce;
  if v_n <> 1 then
    raise exception 'STOP : 3828957 n est pas le dossier de l annonce 62774 -- remesurer';
  end if;
  select count(*) into v_n from public.app_console_photo p, cible c
   where p.app_dossier_id = c.dossier and p.hektor_photo_id = c.photo
     and p.present_in_hektor and p.visible is true;
  if v_n <> 1 then
    raise exception 'STOP : la photo 482253 n est pas VISIBLE sur 62774 -- epreuve NON CONCLUANTE';
  end if;
end $garde$;

-- =============================== 1. AVANT ==================================

insert into essai (etape, mesure, valeur)
select '1-avant ', 'la contrainte connait le type ',
       case when position('set_hektor_photo_visibility' in pg_get_constraintdef(c.oid)) > 0 then 'OUI' else 'non' end
  from pg_constraint c where c.conrelid='public.app_console_job'::regclass
   and c.conname='app_console_job_job_type_check';

insert into essai (etape, mesure, valeur)
select '1-avant ', 'les droits connaissent le type',
       case when position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0 then 'OUI' else 'non' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_can_request_job';

insert into essai (etape, mesure, valeur)
select '1-avant ', 'la distribution connait le type',
       case when position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0 then 'OUI' else 'non' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai (etape, mesure, valeur)
select '1-avant ', 'la RPC existe                 ',
       case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                          where n.nspname='public' and p.proname='app_console_photo_visibilite_optimistic')
            then 'OUI' else 'non' end;

insert into essai (etape, mesure, valeur)
select '1-avant ', '62774 : photos / visibles     ',
       count(*)::text || ' / ' || count(*) filter (where p.visible)::text
  from public.app_console_photo p, cible c
 where p.app_dossier_id = c.dossier and p.present_in_hektor;

insert into essai (etape, mesure, valeur)
select '1-avant ', 'la photo 482253 est           ',
       case when p.visible then 'visible' else 'masquee' end
  from public.app_console_photo p, cible c
 where p.app_dossier_id = c.dossier and p.hektor_photo_id = c.photo and p.present_in_hektor;

insert into essai (etape, mesure, valeur)
select '1-avant ', 'adresses_app_le de 62774      ',
       coalesce(d.adresses_app_le::text, 'DEJA A BLANC')
  from public.app_dossier_current d, cible c where d.app_dossier_id = c.dossier;

-- ============ 2. LE VRAI PATCH -- EXTRAIT DU FICHIER, PAS RECOPIE ===========
"""

APRES = """
-- ============================ 2bis. LE PATCH A-T-IL PRIS ? ==================

insert into essai (etape, mesure, valeur)
select '2-patch ', 'la contrainte connait le type ',
       case when position('set_hektor_photo_visibility' in pg_get_constraintdef(c.oid)) > 0 then 'OUI' else 'NON -- ECHEC' end
  from pg_constraint c where c.conrelid='public.app_console_job'::regclass
   and c.conname='app_console_job_job_type_check';

insert into essai (etape, mesure, valeur)
select '2-patch ', 'les droits connaissent le type',
       case when position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0 then 'OUI' else 'NON -- ECHEC' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_can_request_job';

insert into essai (etape, mesure, valeur)
select '2-patch ', 'la distribution connait le type',
       case when position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0 then 'OUI' else 'NON -- ECHEC' end
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_claim_next_job';

insert into essai (etape, mesure, valeur)
select '2-patch ', 'la RPC existe (nb parametres) ',
       'OUI (' || p.pronargs::text || ' parametres)'
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_photo_visibilite_optimistic';

-- ⚠ LE DROIT `anon` : la lecon du 08/10 (chantier ①) -- Supabase pose un GRANT
--   a `authenticated` sur TOUTE fonction neuve, et un `revoke from public` ne
--   l'enleve pas. On verifie donc ce que dit VRAIMENT proacl, pas ce que le
--   patch annonce.
insert into essai (etape, mesure, valeur)
select '2-patch ', 'anon peut l appeler           ',
       case when array_to_string(p.proacl, ' ') like '%anon=%' then 'OUI -- ECHEC' else 'NON' end
       || '  (authenticated : ' ||
       case when array_to_string(p.proacl, ' ') like '%authenticated=%' then 'oui' else 'NON' end || ')'
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='app_console_photo_visibilite_optimistic';

-- ========================= 3. LE GESTE : ON MASQUE =========================

create temporary table retour as
  select public.app_console_photo_visibilite_optimistic(c.dossier, c.annonce, c.photo, false) as r
    from cible c;

insert into essai (etape, mesure, valeur)
select '3-masque', 'le retour est ok              ',
       case when (r->>'ok') = 'true'
            then 'oui, visible=' || coalesce(r->>'visible','?')
            else 'NON : ' || coalesce(r->>'erreur','?') end
  from retour;

insert into essai (etape, mesure, valeur)
select '3-masque', 'la photo 482253 est devenue   ',
       case when p.visible then 'visible -- ECHEC' else 'masquee' end
  from public.app_console_photo p, cible c
 where p.app_dossier_id = c.dossier and p.hektor_photo_id = c.photo;

insert into essai (etape, mesure, valeur)
select '3-masque', 'LE POST-IT (index marques)    ',
       coalesce(r->>'index_marques_a_refaire','?')
       || case when coalesce((r->>'index_marques_a_refaire')::int, 0) = 0
               then '  (0 est normal si adresses_app_le etait DEJA a blanc)' else '' end
  from retour;

insert into essai (etape, mesure, valeur)
select '3-masque', 'adresses_app_le de 62774      ',
       case when d.adresses_app_le is null then 'A BLANC -- le fabricant la reciblera'
            else 'ENCORE POSEE (' || d.adresses_app_le::text || ') -- ECHEC' end
  from public.app_dossier_current d, cible c where d.app_dossier_id = c.dossier;

insert into essai (etape, mesure, valeur)
select '3-masque', 'le travail cree, du bon type  ',
       coalesce(j.job_type, 'AUCUN TRAVAIL -- ECHEC')
       || case when j.status is not null then ' (' || j.status || ')' else '' end
  from retour r left join public.app_console_job j on j.id = (r.r->>'job_id')::uuid;

insert into essai (etape, mesure, valeur)
select '3-masque', 'sa charge : l etat d avant    ',
       coalesce(j.payload_json->>'etat_avant', '(absent) -- ECHEC')
       || ', demande=' || coalesce(j.payload_json->>'visible','?')
       || ', photos dans base_snapshot=' ||
       coalesce(jsonb_array_length(j.payload_json->'base_snapshot')::text, '?')
  from retour r left join public.app_console_job j on j.id = (r.r->>'job_id')::uuid;

insert into essai (etape, mesure, valeur)
select '3-masque', 'visibles restantes / derniere ',
       coalesce(r->>'visibles_restantes','?') || ' / plus_aucune_visible=' ||
       coalesce(r->>'plus_aucune_visible','?')
  from retour;

-- ===================== 4. ON REJOUE LE MEME MASQUAGE =======================
-- ⭐ Il ne doit PAS deranger Hektor une seconde fois.

insert into essai (etape, mesure, valeur)
select '4-rejoue', 'rejouer le MEME masquage      ',
       case when (x->>'deja_dans_cet_etat') = 'true' then 'deja_dans_cet_etat -- Hektor non derange'
            when (x->>'ok') = 'true' then 'UN SECOND TRAVAIL A ETE CREE -- ECHEC'
            else 'refus : ' || coalesce(x->>'erreur','?') end
  from (select public.app_console_photo_visibilite_optimistic(c.dossier, c.annonce, c.photo, false) as x
          from cible c) z;

-- ========================= 5. ET ON LA REAFFICHE ===========================
-- ⭐ LE TEMOIN INVERSE DU GESTE : la meme commande dans l'autre sens.

create temporary table retour2 as
  select public.app_console_photo_visibilite_optimistic(c.dossier, c.annonce, c.photo, true) as r
    from cible c;

insert into essai (etape, mesure, valeur)
select '5-affich', 'on la REAFFICHE               ',
       case when (r->>'ok') = 'true' then 'oui, visible=' || coalesce(r->>'visible','?')
            else 'NON : ' || coalesce(r->>'erreur','?') end
  from retour2;

insert into essai (etape, mesure, valeur)
select '5-affich', 'la photo 482253 est revenue   ',
       case when p.visible then 'visible' else 'masquee -- ECHEC' end
  from public.app_console_photo p, cible c
 where p.app_dossier_id = c.dossier and p.hektor_photo_id = c.photo;

insert into essai (etape, mesure, valeur)
select '5-affich', 'deux travaux distincts crees  ',
       case when (select r->>'job_id' from retour) is distinct from (select r->>'job_id' from retour2)
            then 'oui' else 'NON -- ECHEC' end;

-- ============================== 6. LES REFUS ===============================

insert into essai (etape, mesure, valeur)
select '6-refus ', 'une photo inconnue            ',
       coalesce(x->>'erreur', 'AUCUN REFUS -- ECHEC')
  from (select public.app_console_photo_visibilite_optimistic(c.dossier, c.annonce, '999999999', false) as x
          from cible c) z;

insert into essai (etape, mesure, valeur)
select '6-refus ', 'des parametres vides          ',
       coalesce(x->>'erreur', 'AUCUN REFUS -- ECHEC')
  from (select public.app_console_photo_visibilite_optimistic(null, '', '', null) as x) z;

-- ========================== 7. LE VRAI INVERSE =============================
-- ⚠ L'ORDRE EST CELUI DE L'INVERSE : la RPC d'abord, la contrainte en dernier.

drop function if exists public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean);

do $inv_distrib$
declare v_def text; v_pose text := replace(',''set_hektor_photo_visibility''', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_def
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='app_console_claim_next_job';
  if position(v_pose in v_def) > 0 then execute replace(v_def, v_pose, ''); end if;
end $inv_distrib$;

do $inv_droits$
declare v_def text; v_pose text := replace('''set_hektor_photo_visibility'',', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_def
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='app_console_can_request_job';
  if position(v_pose in v_def) > 0 then execute replace(v_def, v_pose, ''); end if;
end $inv_droits$;

do $inv_contrainte$
declare v_def text; v_pose text := replace(', ''set_hektor_photo_visibility''::text', chr(13), ''); v_neuf text;
begin
  select pg_get_constraintdef(c.oid) into v_def from pg_constraint c
   where c.conrelid='public.app_console_job'::regclass and c.conname='app_console_job_job_type_check';
  if position(v_pose in v_def) > 0 then
    v_neuf := replace(v_def, v_pose, '');
    execute 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    execute 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
            || v_neuf || ' NOT VALID';
  end if;
end $inv_contrainte$;

insert into essai (etape, mesure, valeur)
select '7-retour', 'la RPC a disparu              ',
       case when exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                          where n.nspname='public' and p.proname='app_console_photo_visibilite_optimistic')
            then 'NON -- ECHEC' else 'oui' end;

insert into essai (etape, mesure, valeur)
select '7-retour', 'les 3 verrous ne connaissent + ',
       case when (select position('set_hektor_photo_visibility' in pg_get_constraintdef(c.oid))
                    from pg_constraint c where c.conrelid='public.app_console_job'::regclass
                     and c.conname='app_console_job_job_type_check') = 0
             and (select position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid))
                    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                   where n.nspname='public' and p.proname='app_console_can_request_job') = 0
             and (select position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid))
                    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
                   where n.nspname='public' and p.proname='app_console_claim_next_job') = 0
            then 'oui, aucune trace' else 'NON -- ECHEC' end;

-- ================== 8. L ERREUR VOLONTAIRE : tout est annule ================
-- ⚠ Le compte rendu voyage DANS le message : un SELECT d une transaction qui
--   echoue n est pas toujours rendu par l editeur SQL.

do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit : ni les verrous, ni la RPC, ni le drapeau de la photo, ni les travaux.'
    || chr(10) || v_txt;
end
$fin$;

rollback;
"""

texte = EN_TETE + corps + APRES
with io.open(SORTIE, "w", encoding="utf-8", newline="") as f:
    f.write(texte)

# ── LES CONTROLES DU GENERATEUR ──────────────────────────────────────────────
emp_corps = hashlib.md5(corps.encode("utf-8")).hexdigest()
relu = SORTIE.read_text(encoding="utf-8")
print("patch          :", len(src), "caracteres")
print("corps extrait  :", len(corps), "caracteres   empreinte", emp_corps)
print("repetition     :", len(texte), "caracteres")
print()
print("LE CORPS EXTRAIT EST-IL DANS LA REPETITION, A L'OCTET PRES ?",
      "OUI" if corps in relu else "NON -- NE PAS COLLER")
print("la RPC complete y est             :",
      "CREATE OR REPLACE FUNCTION public.app_console_photo_visibilite_optimistic" in relu)
print("un seul begin; / un seul rollback :",
      sum(1 for l in relu.splitlines() if l.strip() == "begin;"),
      "/", sum(1 for l in relu.splitlines() if l.strip() == "rollback;"))
print("aucun commit; (interdit ici)      :",
      sum(1 for l in relu.splitlines() if l.strip().upper() == "COMMIT;"))
print("marqueur oublie (\\i_) :", "\\i_" in relu)
prot = re.findall(r"replace\('([^']*(?:''[^']*)*)', chr\(13\)", relu)
print("ancres protegees / multi-lignes   :", len(prot), "/", sum(1 for p in prot if "\n" in p))
