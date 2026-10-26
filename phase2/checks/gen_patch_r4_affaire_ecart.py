#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑧ R4 -- GENERE le patch des ecarts du carnet des transactions, son retour arriere et sa repetition.   26/10/2026

Le corps (table des decisions, vue des ecarts, fonction trancher) est dans gen_patch_r4_affaire_ecart_corps.sql :
UNE seule copie, reprise A L'IDENTIQUE par le patch et par la repetition (« la repetition joue le VRAI patch »).
Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md §54-55.

    python phase2/checks/gen_patch_r4_affaire_ecart.py
"""
from __future__ import annotations

from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CORPS = (Path(__file__).with_name("gen_patch_r4_affaire_ecart_corps.sql")).read_text(encoding="utf-8").replace("\r", "")
SORTIE = RACINE / "supabase"
NOM = "patch_r4_affaire_ecart_2026-10-26"

TETE = """-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · R4 — LES ÉCARTS DU CARNET DES TRANSACTIONS, ET LA RÉPONSE DE L'HUMAIN      26/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md §54-55
-- Fichier GÉNÉRÉ (phase2/checks/gen_patch_r4_affaire_ecart.py).
--
-- POURQUOI. Avec R2 et la décision A (« pas de durée maximale »), un « conflit » garde notre valeur au
-- registre : il peut cacher une correction faite ensuite dans Hektor. Il doit SONNER, et l'humain doit
-- pouvoir répondre. Aujourd'hui un conflit ou un échec n'existe que dans le journal du travail.
--
-- CE QUE FAIT CE PATCH — ADDITIF, aucune fonction existante retouchée, le carnet n'est pas modifié :
--   1. app_affaire_carnet_decision : la réponse de l'humain, et notre saisie rangée quand on prend Hektor ;
--   2. app_v_affaire_carnet_ecarts : une ligne par champ en conflit, en échec, ou en attente depuis > 48 h ;
--   3. app_affaire_carnet_ecart_trancher(affaire, champ, 'hektor' | 'app' | 'attendre') — admin seulement.
-- La sentinelle data.affaire_ecart (monitoring/check_gti_health.py) lit la vue (a_traiter) ; la rubrique
-- des affaires porte les deux gestes. Pas d'interrupteur : ces objets n'écrivent que sur un geste de l'admin.
--
-- RETOUR ARRIÈRE : supabase/patch_r4_affaire_ecart_2026-10-26_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

"""

CONTROLES = """
-- LES CONTRÔLES — tous doivent dire OK
SELECT 1 AS "#", 'la table des decisions existe, vide ; lecture seule pour les connectes, fermee a anon' AS controle,
       CASE WHEN (SELECT count(*) FROM public.app_affaire_carnet_decision) = 0
             AND has_table_privilege('authenticated', 'public.app_affaire_carnet_decision', 'SELECT')
             AND NOT has_table_privilege('authenticated', 'public.app_affaire_carnet_decision', 'INSERT')
             AND NOT has_table_privilege('anon', 'public.app_affaire_carnet_decision', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la vue des ecarts est lisible par les connectes et la cle de service, fermee a anon',
       CASE WHEN has_table_privilege('authenticated', 'public.app_v_affaire_carnet_ecarts', 'SELECT')
             AND has_table_privilege('service_role', 'public.app_v_affaire_carnet_ecarts', 'SELECT')
             AND NOT has_table_privilege('anon', 'public.app_v_affaire_carnet_ecarts', 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'la fonction trancher : ouverte aux connectes, fermee a anon',
       CASE WHEN has_function_privilege('authenticated', 'public.app_affaire_carnet_ecart_trancher(bigint,text,text)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_affaire_carnet_ecart_trancher(bigint,text,text)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'la vue se lit',
       CASE WHEN (SELECT count(*) FROM public.app_v_affaire_carnet_ecarts) >= 0 THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
"""

INVERSE_CORPS = """drop function if exists public.app_affaire_carnet_ecart_trancher(bigint, text, text);
drop view if exists public.app_v_affaire_carnet_ecarts;

DO $garde_decisions$
DECLARE
    n int;
    nom text := 'app_affaire_carnet_decision_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_affaire_carnet_decision') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_affaire_carnet_decision n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_affaire_carnet_decision' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_affaire_carnet_decision';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_affaire_carnet_decision rename to %I', nom);
        RAISE NOTICE '%', format('%s decision(s) gardee(s) sous public.%s (les saisies rangees par « prendre Hektor » y sont)', n, nom);
    END IF;
END
$garde_decisions$;
"""

INVERSE = """-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE R4 — les écarts du carnet des transactions                    26/10/2026
-- Fichier GÉNÉRÉ (phase2/checks/gen_patch_r4_affaire_ecart.py).
-- Il retire la fonction et la vue. ⛔ IL NE PERD AUCUNE DÉCISION : si la table porte des lignes (dont les
-- saisies rangées par « prendre la valeur de Hektor »), elle est RENOMMÉE
-- app_affaire_carnet_decision_avant_inverse_<aaaammjj>, pas supprimée.
-- ⚠ Il ne REMET PAS au carnet les lignes retirées par « prendre Hektor » : c'était une décision de l'humain.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

""" + INVERSE_CORPS + """
SELECT 1 AS "#", 'la fonction et la vue sont retirees' AS controle,
       CASE WHEN to_regprocedure('public.app_affaire_carnet_ecart_trancher(bigint,text,text)') IS NULL
             AND to_regclass('public.app_v_affaire_carnet_ecarts') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la table des decisions est retiree ou renommee',
       CASE WHEN to_regclass('public.app_affaire_carnet_decision') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'le carnet est intact',
       CASE WHEN to_regclass('public.app_affaire_champ_app') IS NOT NULL THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
"""

REP_TETE = """-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE R4 — les écarts du carnet et la réponse de l'humain — TOUT EST ANNULÉ        26/10/2026
-- Fichier GÉNÉRÉ (phase2/checks/gen_patch_r4_affaire_ecart.py).
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … ». Elle pose LE VRAI PATCH, fabrique des lignes de carnet
-- d'essai sur les transactions d'essai de 24113 (compromis 1001394, offre 1001393), joue la fonction comme un
-- admin puis comme un non-admin, puis LE VRAI RETOUR ARRIÈRE. Rien ne reste.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

"""

ESSAIS = """
DO $essai$
DECLARE
    v_admin uuid;
    v_autre uuid;
    v_err text;
    v_r jsonb;
    n int;
BEGIN
    SELECT id INTO v_admin FROM public.app_user_profile WHERE is_active AND role::text = 'admin' ORDER BY id LIMIT 1;
    SELECT id INTO v_autre FROM public.app_user_profile WHERE is_active AND role::text <> 'admin' ORDER BY id LIMIT 1;
    IF v_admin IS NULL OR v_autre IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : il faut un admin actif et un non-admin actif pour l''essai.';
    END IF;
    IF (SELECT count(*) FROM public.app_affaire_ledger WHERE app_affaire_id IN (1001393, 1001394)) <> 2 THEN
        RAISE EXCEPTION '%', 'ARRET : les transactions d''essai 1001393 / 1001394 n''existent plus.';
    END IF;

    -- les lignes d'essai (le carnet de 1001394 ne porte aucun de ces champs aujourd'hui)
    delete from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ in ('sequestre', 'montant', 'date_acte', 'date');
    delete from public.app_affaire_champ_app where app_affaire_id = 1001393 and champ = 'montant';
    insert into public.app_affaire_champ_app (app_affaire_id, champ, valeur_app, valeur_hektor_au_moment, valeur_hektor_relue, origine, ecrit_le, etat, constate_le)
    values (1001394, 'sequestre', '6000', null, '5000', 'creation_app', now() - interval '1 hour', 'conflit', now()),
           (1001394, 'montant', '135000', '130000', null, 'modification_app', now() - interval '3 hours', 'echec', now()),
           (1001394, 'date_acte', '2027-01-15', null, null, 'creation_app', now() - interval '72 hours', 'en_attente', now() - interval '20 hours'),
           (1001394, 'date', '2026-10-22', null, null, 'creation_app', now() - interval '2 hours', 'en_attente', now()),
           (1001393, 'montant', '160000', null, '16000', 'saisie_app', now() - interval '5 hours', 'conflit', now());

    SELECT count(*) INTO n FROM public.app_v_affaire_carnet_ecarts WHERE app_affaire_id IN (1001393, 1001394) AND a_traiter;
    insert into _m values (1, 'la vue montre EXACTEMENT conflit + echec + attente > 48 h (3)', case when n = 3
        and exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'sequestre' and ecart = 'conflit' and valeur_hektor = '5000' and kind = 'compromis')
        and exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'montant' and ecart = 'echec')
        and exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'date_acte' and ecart = 'attente_longue')
        then 'OK' else 'ECHEC (' || n || ')' end);
    insert into _m values (2, 'pas dans la vue : attente de 2 h, saisie_app, lignes arrivee / sans objet', case when
        not exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'date')
        and not exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001393 and champ = 'montant')
        and not exists (select 1 from public.app_v_affaire_carnet_ecarts v join public.app_affaire_champ_app c using (app_affaire_id, champ) where c.etat in ('arrivee', 'sans_objet'))
        then 'OK' else 'ECHEC' end);

    -- un NON-admin est refusé
    PERFORM set_config('request.jwt.claim.sub', v_autre::text, true);
    PERFORM set_config('request.jwt.claims', json_build_object('sub', v_autre::text, 'role', 'authenticated')::text, true);
    v_err := '';
    BEGIN
        PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'sequestre', 'hektor');
    EXCEPTION WHEN others THEN v_err := sqlerrm;
    END;
    insert into _m values (3, 'un non-admin est refuse (admin_requis), rien ne bouge', case when v_err = 'admin_requis'
        and exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'sequestre')
        and (select count(*) from public.app_affaire_carnet_decision) = 0 then 'OK' else 'ECHEC (' || v_err || ')' end);

    -- l'admin : « garder la nôtre » sur le conflit
    PERFORM set_config('request.jwt.claim.sub', v_admin::text, true);
    PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin::text, 'role', 'authenticated')::text, true);
    v_r := public.app_affaire_carnet_ecart_trancher(1001394, 'sequestre', 'app');
    insert into _m values (4, '« garder la notre » : decision rangee (par l''admin), la ligne RESTE au carnet, l''alerte se tait', case when
        (v_r->>'retiree_du_carnet')::boolean = false
        and exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'sequestre' and valeur_app = '6000')
        and exists (select 1 from public.app_affaire_carnet_decision where app_affaire_id = 1001394 and champ = 'sequestre' and decision = 'app' and decide_par = v_admin and valeur_hektor = '5000')
        and not exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'sequestre' and a_traiter)
        then 'OK' else 'ECHEC ' || v_r::text end);

    -- la saisie est RÉÉCRITE après la décision : elle sonne de nouveau
    update public.app_affaire_champ_app set valeur_app = '6500', ecrit_le = now() where app_affaire_id = 1001394 and champ = 'sequestre';
    insert into _m values (5, 'une saisie reecrite apres la decision SONNE de nouveau', case when
        exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'sequestre' and a_traiter)
        then 'OK' else 'ECHEC' end);

    -- « prendre la valeur de Hektor » sur l'échec
    v_r := public.app_affaire_carnet_ecart_trancher(1001394, 'montant', 'hektor');
    insert into _m values (6, '« prendre Hektor » : la saisie est RANGEE (valeur, verdict, origine) puis RETIREE du carnet', case when
        (v_r->>'retiree_du_carnet')::boolean = true
        and not exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'montant')
        and exists (select 1 from public.app_affaire_carnet_decision where app_affaire_id = 1001394 and champ = 'montant' and decision = 'hektor'
                    and valeur_app = '135000' and etat = 'echec' and origine = 'modification_app')
        then 'OK' else 'ECHEC ' || v_r::text end);

    -- « attendre encore » sur l'attente longue ; refusé sur un conflit ; « garder » refusé sur une attente
    v_r := public.app_affaire_carnet_ecart_trancher(1001394, 'date_acte', 'attendre');
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'sequestre', 'attendre'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (7, '« attendre » : accepte sur une attente (la ligne reste), refuse sur un conflit', case when
        exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'date_acte')
        and not exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'date_acte' and a_traiter)
        and v_err = 'attendre_reserve_a_l_attente' then 'OK' else 'ECHEC (' || v_err || ')' end);
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'date_acte', 'app'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (8, '« garder la notre » refuse sur une attente', case when v_err = 'garder_reserve_au_conflit_et_a_l_echec' then 'OK' else 'ECHEC (' || v_err || ')' end);

    -- les refus de forme
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'notaire_id', 'hektor'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (9, 'une ligne « arrivee » n''est pas un ecart (pas_un_ecart), elle reste', case when v_err = 'pas_un_ecart'
        and exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'notaire_id') then 'OK' else 'ECHEC (' || v_err || ')' end);
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001393, 'montant', 'hektor'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (10, 'une saisie gardee chez nous (saisie_app) n''est pas un ecart', case when v_err = 'pas_un_ecart' then 'OK' else 'ECHEC (' || v_err || ')' end);
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'champ_qui_n_existe_pas', 'hektor'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (11, 'une ligne absente : ligne_introuvable', case when v_err = 'ligne_introuvable' then 'OK' else 'ECHEC (' || v_err || ')' end);
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'date', 'supprimer'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (12, 'une decision inconnue est refusee', case when v_err = 'decision_inconnue' then 'OK' else 'ECHEC (' || v_err || ')' end);

    -- ce que compterait la sentinelle data.affaire_ecart : a_traiter = la seule ligne reecrite
    SELECT count(*) INTO n FROM public.app_v_affaire_carnet_ecarts WHERE a_traiter AND app_affaire_id IN (1001393, 1001394);
    insert into _m values (13, 'la sentinelle compterait 1 (le sequestre reecrit), rien d''autre', case when n = 1 then 'OK' else 'ECHEC (' || n || ')' end);
END
$essai$;

"""

# Dans la repetition, la table des decisions est NON VIDE : le vrai retour arriere la RENOMME (il ne perd rien) ;
# on retire ensuite ce renommage d'essai, pour que rien ne reste (la transaction est de toute facon annulee).
NETTOIE = """
DO $nettoie$
DECLARE t text;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'app_affaire_carnet_decision_avant_inverse_%' LOOP
        EXECUTE format('drop table public.%I', t);
    END LOOP;
END
$nettoie$;
"""

FIN = """
DO $fin$
DECLARE
    r text;
    ok int;
    total int;
BEGIN
    insert into _m values (14, 'le retour arriere a tout retire, le carnet est intact',
        case when to_regclass('public.app_affaire_carnet_decision') IS NULL
                  AND to_regclass('public.app_v_affaire_carnet_ecarts') IS NULL
                  AND to_regprocedure('public.app_affaire_carnet_ecart_trancher(bigint,text,text)') IS NULL
                  AND to_regclass('public.app_affaire_champ_app') IS NOT NULL
             then 'OK' else 'ECHEC' end);
    select count(*) filter (where valeur = 'OK'), count(*), string_agg(n || ' ' || valeur || ' ' || cle, ' | ' order by n)
      into ok, total, r from _m;
    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s | %s', ok, total, r);
END
$fin$;
"""


def ecrire(nom: str, texte: str) -> None:
    chemin = SORTIE / nom
    chemin.write_text(texte, encoding="utf-8", newline="\n")
    octets = chemin.read_bytes()
    print(f"{chemin.relative_to(RACINE)} : {len(octets)} octets, CR {octets.count(bytes([13]))}")


def main() -> None:
    ecrire(f"{NOM}.sql", TETE + CORPS + CONTROLES)
    ecrire(f"{NOM}_INVERSE.sql", INVERSE)
    ecrire(f"{NOM}_REPETITION.sql", REP_TETE + CORPS + ESSAIS + INVERSE_CORPS + NETTOIE + FIN)


if __name__ == "__main__":
    main()
