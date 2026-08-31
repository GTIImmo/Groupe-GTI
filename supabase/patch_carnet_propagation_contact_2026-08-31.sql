-- =====================================================================
-- LA PROPAGATION TIENT UN CARNET
-- Date : 2026-08-31
--
-- POURQUOI, ET C'EST FREDERIC QUI L'A VU. Sa question : « mais si rien n'est
-- cree dans l'app, on ne va rien voir avec la sentinelle ? »
--
-- La reponse est pire que sa question. Regardons l'ordre des taches :
--
--     05:30   GTI Quotidien      build -> push -> pousser -> PROPAGER
--     07:30   GTI Descente
--     07:48   GTI Health Monitor                         <- la sentinelle
--
-- LA SENTINELLE LIT L'ETAT *APRES* LA REPARATION. Elle affichera donc 0 chaque
-- matin, que le flux soit sain ou non -- puisque la propagation vient de tout
-- rattraper une heure plus tot. Elle prouve « la reparation a tourne », elle ne
-- prouve pas « le flux est bon ».
--
-- SUR SON PREMIER POINT, en revanche, la mesure dit le contraire de l'intuition :
-- les lignes qui perdaient leur numero n'etaient PAS creees par l'app. Personne
-- n'a cree de contact dans l'app depuis le 25/08, et il en manquait 5 288 --
-- c'est le RUN DE NUIT lui-meme qui fabrique des lignes (la reconstruction
-- recree relations et recherches, le moteur recalcule les rapprochements).
--
-- CE QUI SE MESURE VRAIMENT est donc COMBIEN la reparation a eu a faire. La
-- valeur de retour existait deja ; personne ne la gardait.
--
-- ⚠ C'EST EXACTEMENT LA LEÇON DU 21/08, et je viens de refaire le meme trou.
-- Le carnet du balayage des recherches disait deja, mot pour mot :
--     « Une reparation nocturne qui ne dit pas ce qu'elle repare ne se
--       surveille pas. »
--
-- PAS DE SECONDE SENTINELLE, et c'est deliberé : si la propagation s'arrete, le
-- compteur remonte d'environ 750 par jour et franchit le seuil de 150 en moins
-- de vingt-quatre heures. La sonde existante suffit a detecter l'arret ; le
-- carnet, lui, sert a mesurer le RYTHME.
--
-- CE QUI NE CHANGE PAS : les memes 18 UPDATE, la meme regle « on ne remplit que
-- les cases vides ». Seule l'ecriture du carnet est ajoutee. La fonction n'ayant
-- AUCUN parametre, `create or replace` conserve les droits -- contrairement au
-- piege des fonctions a parametres.
--
-- VERIFIE : rejoue a vide -> total 0, et la ligne s'ecrit bien dans le carnet.
--
-- Appliquee via la migration `c2b_propagation_contact_tient_un_carnet`.
-- =====================================================================

create table if not exists public.app_contact_id_propagation_log (
  run_at timestamptz primary key default now(),
  total  integer not null default 0,
  detail jsonb   not null default '{}'::jsonb
);

-- La fonction est identique a celle du 31/08 au matin, a l'insert du carnet pres.
-- Corps complet : voir la migration.
