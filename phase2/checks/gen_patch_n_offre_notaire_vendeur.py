# Genere les 3 fichiers du patch N (le notaire du VENDEUR d'une OFFRE est garde chez nous).
#     python phase2/checks/gen_patch_n_offre_notaire_vendeur.py                    -> la requete d'empreinte (lecture seule)
#     python phase2/checks/gen_patch_n_offre_notaire_vendeur.py <apres_C> <apres_M> -> les 3 fichiers
# Meme patron que gen_patch_a5_modif_au_registre.py : l'empreinte d'apres se calcule dans la base.
# Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 27.
import pathlib, sys

OUT = pathlib.Path(__file__).resolve().parents[2] / "supabase"
BASE = "patch_n_offre_notaire_vendeur_2026-10-23"
CLE = "offre_notaire_vendeur"
INTER = f"coalesce((select s.value from public.app_setting s where s.key = '{CLE}'), 'off') = 'on'"

# Les deux fonctions, et leur empreinte MESUREE le 23/10 (apres R1 / A5).
FN_C = "public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)"
AVANT_C = "f9d024471d0740fa21fffa532e9aa2ae"
FN_M = "public.app_modifier_affaire_optimistic(bigint,jsonb,integer)"
AVANT_M = "0dac8c866a73517032bf23a9bd307b71"

# CREATION : une ancre d'UNE ligne, la ligne du notaire de l'acquereur dans la carte du carnet.
ANC_C = "        ('notaire_id',         v_payload->>'buyer_notary_id'),"
NEUF_C = "\n".join([
    ANC_C,
    "        -- N (23/10/2026, chantier 8) : le notaire du VENDEUR d'une OFFRE. Hektor ne le garde pas sur une",
    "        --   offre (0 sur 11 190) : le carnet le garde, et le compromis de la chaine le reprend.",
    f"        --   Interrupteur '{CLE}'. Compromis et vente : inchanges (R1 les ecrit au registre).",
    f"        ('notaire_mandant_id',  case when v_kind = 'offre' and {INTER}",
    "                                 then v_payload->>'seller_notary_id' end),",
    f"        ('notaire_mandant_nom', case when v_kind = 'offre' and {INTER}",
    "                                  and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null",
    "                                 then v_payload->>'seller_notary_nom' end),",
])

# MODIFICATION : la ligne de la carte (seulement si le notaire du vendeur est AFFIRME, comme A5),
# et la ligne de la liste du point E (la cle tapee qui l'autorise).
ANC_M1 = "      ('notaire_id',         v_payload->>'buyer_notary_id',                             null::text),"
GARDE_M = (f"a.kind = 'offre' and (v_payload->'notaires_affirmes'->>'mandant') = 'true' and {INTER}")
NEUF_M1 = "\n".join([
    ANC_M1,
    "      -- N (23/10/2026) : le notaire du VENDEUR d'une OFFRE, s'il est AFFIRME (voir la creation).",
    f"      ('notaire_mandant_id',  case when {GARDE_M}",
    "                               then v_payload->>'seller_notary_id' end,                null::text),",
    f"      ('notaire_mandant_nom', case when {GARDE_M}",
    "                                and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null",
    "                               then v_payload->>'seller_notary_nom' end,               null::text),",
])
ANC_M2 = "             when 'notaire_id'         then array['buyer_notary_id']"
NEUF_M2 = "\n".join([
    ANC_M2,
    "             when 'notaire_mandant_id'  then array['seller_notary_id']",
    "             when 'notaire_mandant_nom' then array['seller_notary_id']",
])

FONCTIONS = [
    ("C", FN_C, AVANT_C, [(ANC_C, NEUF_C)], "app_change_annonce_status_optimistic"),
    ("M", FN_M, AVANT_M, [(ANC_M1, NEUF_M1), (ANC_M2, NEUF_M2)], "app_modifier_affaire_optimistic"),
]


def lit(t, tag):
    assert f"${tag}$" not in t
    return f"replace(${tag}${t}${tag}$, chr(13), '')"


def tableaux(code, ancres):
    a = ",\n        ".join(lit(x, f"{code.lower()}a{i + 1}") for i, (x, _) in enumerate(ancres))
    n = ",\n        ".join(lit(y, f"{code.lower()}n{i + 1}") for i, (_, y) in enumerate(ancres))
    return a, n


def requete_empreinte():
    morceaux = []
    for code, fn, _avant, ancres, _nom in FONCTIONS:
        d = f"replace(pg_get_functiondef('{fn}'::regprocedure), chr(13), '')"
        for i, (x, y) in enumerate(ancres):
            d = f"replace({d}, {lit(x, code.lower() + 'a' + str(i + 1))}, {lit(y, code.lower() + 'n' + str(i + 1))})"
        morceaux.append(f"select '{code}' f, md5(replace(pg_get_functiondef('{fn}'::regprocedure), chr(13), '')) avant,\n"
                        f"       md5({d}) apres")
    return "\nunion all\n".join(morceaux) + ";"


sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 3:
    print(requete_empreinte())
    sys.exit(0)
APRES = {"C": sys.argv[1], "M": sys.argv[2]}
for code, _fn, avant, _a, _n in FONCTIONS:
    assert len(APRES[code]) == 32 and APRES[code] != avant, code


def bloc_pose(code, fn, avant, ancres, nom, etiquette):
    a, n = tableaux(code, ancres)
    apres = APRES[code]
    return f"""DO ${etiquette}$
DECLARE
    d text := replace(pg_get_functiondef('{fn}'::regprocedure), chr(13), '');
    ancres text[] := array[
        {a}];
    neufs text[] := array[
        {n}];
    i int;
    nb int;
BEGIN
    IF md5(d) = '{apres}' THEN
        RAISE NOTICE '%', 'Deja pose : {nom} porte deja l''empreinte {apres[:8]}. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '{avant}' THEN
        RAISE EXCEPTION '%', format('ARRET : {nom} a l''empreinte %s, attendu {avant[:8]} (mesuree le 23/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : {nom}, l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '{apres}' THEN
        RAISE EXCEPTION '%', format('ARRET : {nom}, le texte neuf a l''empreinte %s, attendu {apres[:8]} (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('{fn}'::regprocedure), chr(13), '')) <> '{apres}' THEN
        RAISE EXCEPTION '%', 'ARRET : {nom}, apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
${etiquette}$;"""


def bloc_inverse(code, fn, avant, ancres, nom, etiquette):
    a, n = tableaux(code, ancres)
    apres = APRES[code]
    return f"""DO ${etiquette}$
DECLARE
    d text := replace(pg_get_functiondef('{fn}'::regprocedure), chr(13), '');
    ancres text[] := array[
        {a}];
    neufs text[] := array[
        {n}];
    i int;
    nb int;
BEGIN
    IF md5(d) = '{avant}' THEN
        RAISE NOTICE '%', 'Rien a retirer : {nom} porte deja l''empreinte d''avant ({avant[:8]}).';
        RETURN;
    END IF;
    IF md5(d) <> '{apres}' THEN
        RAISE EXCEPTION '%', format('ARRET : {nom} a l''empreinte %s, ni {apres[:8]} (posee) ni {avant[:8]} (avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : {nom}, le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '{avant}' THEN
        RAISE EXCEPTION '%', format('ARRET : {nom}, le texte rendu a l''empreinte %s, attendu {avant[:8]}. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
${etiquette}$;"""


INTERRUPTEUR = f"""insert into public.app_setting (key, value, description, updated_at)
values ('{CLE}', 'off',
        'Chantier 8 / N 23/10/2026 : on = le notaire du VENDEUR saisi sur une OFFRE est garde au carnet (notaire_mandant_id / notaire_mandant_nom), a la creation et a la modification s''il est affirme (voir supabase/{BASE}.sql). Hektor ne le garde pas sur une offre. off = comportement d''avant (il se perd).',
        now())
on conflict (key) do nothing;"""


def controles():
    lignes = []
    k = 0
    for code, fn, _avant, _a, nom in FONCTIONS:
        k += 1
        lignes.append(f"SELECT {k} AS \"#\", '{nom} porte l''empreinte {APRES[code][:8]}' AS controle,\n"
                      f"       CASE WHEN md5(replace(pg_get_functiondef('{fn}'::regprocedure), chr(13), '')) = '{APRES[code]}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict")
        k += 1
        lignes.append(f"SELECT {k}, '{nom} : droits d''appel inchanges, SECURITY DEFINER',\n"
                      f"       CASE WHEN has_function_privilege('authenticated', '{fn}', 'EXECUTE') AND (SELECT prosecdef FROM pg_proc WHERE oid = '{fn}'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END")
    k += 1
    lignes.append(f"SELECT {k}, 'l''interrupteur existe, ETEINT',\n"
                  f"       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END")
    return "\nUNION ALL ".join(lignes) + "\nORDER BY 1;"


ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · N — LE NOTAIRE DU VENDEUR D'UNE OFFRE EST GARDÉ CHEZ NOUS        23/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (section 27). Décision de
-- Frédéric : « A » (le garder chez nous, et que le compromis le reprenne).
--
-- LE DÉFAUT. La modale propose « Notaire du vendeur » sur l'onglet Offre ; le worker l'envoie à Hektor,
-- qui ne le garde pas sur une offre (0 sur 11 190) ; R1 ne l'écrit qu'au compromis et à la vente ; le
-- carnet n'avait qu'un champ notaire, celui de l'acquéreur. La saisie se perdait.
--
-- CE QUE FAIT CE PATCH — TROIS ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting '{CLE}', posé à 'off' ;
--   2. app_change_annonce_status_optimistic (création) : deux lignes de plus dans la carte du carnet,
--      notaire_mandant_id / notaire_mandant_nom, POUR UNE OFFRE SEULEMENT ;
--   3. app_modifier_affaire_optimistic (modification) : les mêmes, seulement si le notaire du vendeur
--      est AFFIRMÉ (notaires_affirmes.mandant), et la clé 'seller_notary_id' dans la liste du point E.
--   Rien d'autre ne change : le travail pour Hektor, le registre, le compromis, la vente.
--   ⚠ Ces lignes de carnet n'ont PAS de colonne : elles restent au carnet (règle de sortie du 16/09).
--
-- ⛔ GARDE : empreintes {AVANT_C[:8]} (création) et {AVANT_M[:8]} (modification) exigées, chaque ancre
--    trouvée UNE fois, textes neufs {APRES['C'][:8]} / {APRES['M'][:8]} CALCULÉS D'AVANCE. Sinon : ARRÊT.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = '{CLE}';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = '{CLE}';
-- RETOUR ARRIÈRE COMPLET : supabase/{BASE}_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
"""

pose = ENTETE + f"""
BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
{INTERRUPTEUR}

-- 2. LA CRÉATION
{bloc_pose(*FONCTIONS[0], "pose_c")}

-- 3. LA MODIFICATION
{bloc_pose(*FONCTIONS[1], "pose_m")}

-- 4. LES CONTRÔLES — tous doivent dire OK
{controles()}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE N — le notaire du vendeur d'une offre gardé chez nous   23/10/2026
-- Il rend aux deux fonctions leur texte d'avant ({AVANT_C[:8]} / {AVANT_M[:8]}), par les MÊMES ancres, et
-- retire l'interrupteur. Il ne touche aucune donnée : les lignes de carnet déjà écrites restent.
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

{bloc_inverse(*FONCTIONS[0], "retour_c")}

{bloc_inverse(*FONCTIONS[1], "retour_m")}

delete from public.app_setting where key = '{CLE}';

SELECT 1 AS "#", 'app_change_annonce_status_optimistic a retrouve {AVANT_C[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN_C}'::regprocedure), chr(13), '')) = '{AVANT_C}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'app_modifier_affaire_optimistic a retrouve {AVANT_M[:8]}',
       CASE WHEN md5(replace(pg_get_functiondef('{FN_M}'::regprocedure), chr(13), '')) = '{AVANT_M}' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
"""


def test(num, libelle, condition, detail):
    return f"""    total := total + 1;
    IF {condition} THEN ok := ok + 1; r := r || ' | {num} OK {libelle}';
    ELSE r := r || ' | {num} ECHEC {libelle} : ' || coalesce({detail}, 'null'); END IF;"""


# La charge d'une CREATION d'offre, comme l'ecran l'envoie (essai 3 du 23/10, VA6482).
CREE = ("jsonb_build_object('amount', '115000', 'sale_price', '128787', 'transaction_date', '2026-10-23', "
        "'validity_days', '15', 'retraction_days', '10', 'buyer_fees', '5000', 'buyer_fees_rate', '4.35', "
        "'buyer_contact_id', '20000013', 'buyer_notary_id', '10064499', "
        "'seller_notary_id', '10355906', 'seller_notary_nom', 'Me. Eric PAILHES', "
        "'numero_dossier', 'VA6482', 'hektor_annonce_id', '24113')")
# La charge d'une MODIFICATION de l'offre 33114 (1001384), notaire du vendeur affirme.
MODIF = ("jsonb_build_object('amount', '115000', 'transaction_date', '2026-10-23', 'validity_days', '15', "
         "'seller_notary_id', '10355906', 'seller_notary_nom', 'Me. Eric PAILHES', "
         "'notaires_affirmes', jsonb_build_object('acquereur', false, 'mandant', true), "
         "'champs_touches', jsonb_build_array('seller_notary_id'))")


def appel_cree(charge):
    # La RPC rend le TRAVAIL ; le numero de la transaction neuve est dans sa charge (comme l'ecran le lit).
    # Le travail est retire aussitot : un travail en attente sur l'annonce ne doit pas gener l'appel suivant.
    return (f"    res := public.app_change_annonce_status_optimistic(1068399, 'offer', {charge}, 9);\n"
            f"    neuf := coalesce((res->>'app_affaire_id')::bigint,\n"
            f"                     (select (j.payload_json->>'app_affaire_id')::bigint from public.app_console_job j where j.id::text = res->>'job_id'));\n"
            f"    delete from public.app_console_job where id::text = res->>'job_id';")


def carnet(aid, champ):
    return f"(select valeur_app from public.app_affaire_champ_app where app_affaire_id = {aid} and champ = '{champ}')"


repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE N — le notaire du vendeur d'une offre gardé chez nous    23/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni les
--   fonctions modifiées, ni l'interrupteur, ni les transactions créées, ni le carnet, ni les travaux.
-- Le VRAI PATCH, puis les fonctions appelées COMME L'ÉCRAN, au nom de Frédéric, sur VA6482 (dossier
-- 1068399) et son offre 33114 (1001384, essai 3 du 23/10).
--   T1 ÉTEINT : créer une offre avec notaire du vendeur → pas de ligne (le témoin inverse : le défaut)
--   T2 allumé : créer une offre avec notaire du vendeur → id 10355906 et nom au carnet
--   T3 allumé : créer une offre SANS notaire du vendeur → aucune ligne
--   T4 allumé : les AUTRES lignes du carnet de la création sont les mêmes qu'éteint (rien d'autre ne change)
--   T5 allumé : modifier l'offre 1001384, notaire du vendeur AFFIRMÉ et tapé → les deux lignes
--   T6 allumé : modifier, NON affirmé → aucune ligne
--   T7 l'inverse rend {AVANT_C[:8]} et {AVANT_M[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    res jsonb;
    neuf bigint;
    neuf_eteint bigint;
    autres_eteint text;
    autres_allume text;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.app_affaire_ledger WHERE app_affaire_id = 1001384 AND kind = 'offre') THEN
        RAISE EXCEPTION '%', 'ARRET : l''offre d''essai 1001384 n''existe plus -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc_pose(*FONCTIONS[0], "pose_c_rep").replace("DO $pose_c_rep$", "EXECUTE $exec_c$ DO $pose_c_rep$").replace("$pose_c_rep$;", "$pose_c_rep$ $exec_c$;")}
    {bloc_pose(*FONCTIONS[1], "pose_m_rep").replace("DO $pose_m_rep$", "EXECUTE $exec_m$ DO $pose_m_rep$").replace("$pose_m_rep$;", "$pose_m_rep$ $exec_m$;")}

    -- T1 ETEINT
{appel_cree(CREE)}
    neuf_eteint := neuf;
    select string_agg(champ || '=' || valeur_app, ',' order by champ) into autres_eteint
      from public.app_affaire_champ_app where app_affaire_id = neuf_eteint;
{test('T1', 'eteint : pas de notaire du vendeur au carnet', f"neuf_eteint is not null and {carnet('neuf_eteint', 'notaire_mandant_id')} is null", "coalesce(" + carnet('neuf_eteint', 'notaire_mandant_id') + ", res::text)")}

    update public.app_setting set value = 'on' where key = '{CLE}';
    -- T2 ALLUME, AVEC
{appel_cree(CREE)}
{test('T2', 'allume : id et nom au carnet', f"{carnet('neuf', 'notaire_mandant_id')} = '10355906' and {carnet('neuf', 'notaire_mandant_nom')} = 'Me. Eric PAILHES'", "concat_ws(' / ', " + carnet('neuf', 'notaire_mandant_id') + ", " + carnet('neuf', 'notaire_mandant_nom') + ", res::text)")}
    -- T4 RIEN D'AUTRE NE CHANGE
    select string_agg(champ || '=' || valeur_app, ',' order by champ) into autres_allume
      from public.app_affaire_champ_app where app_affaire_id = neuf and champ not in ('notaire_mandant_id', 'notaire_mandant_nom');
{test('T4', 'les autres lignes du carnet sont les memes', "autres_allume is not distinct from autres_eteint", "autres_allume || ' <> ' || coalesce(autres_eteint, 'null')")}
    -- T3 ALLUME, SANS
{appel_cree(CREE + " - 'seller_notary_id' - 'seller_notary_nom'")}
{test('T3', 'allume, sans notaire du vendeur : aucune ligne', f"{carnet('neuf', 'notaire_mandant_id')} is null and {carnet('neuf', 'notaire_mandant_nom')} is null", carnet('neuf', 'notaire_mandant_id'))}

    -- T5 MODIFICATION, AFFIRME
    delete from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ in ('notaire_mandant_id', 'notaire_mandant_nom');
    res := public.app_modifier_affaire_optimistic(1001384, {MODIF}, 9);
    delete from public.app_console_job where id::text = res->>'job_id';
{test('T5', 'modification affirmee : les deux lignes', f"{carnet(1001384, 'notaire_mandant_id')} = '10355906' and {carnet(1001384, 'notaire_mandant_nom')} = 'Me. Eric PAILHES'", "concat_ws(' / ', " + carnet(1001384, 'notaire_mandant_id') + ", res::text)")}
    -- T6 MODIFICATION, NON AFFIRME
    delete from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ in ('notaire_mandant_id', 'notaire_mandant_nom');
    res := public.app_modifier_affaire_optimistic(1001384, {MODIF} || jsonb_build_object('notaires_affirmes', jsonb_build_object('acquereur', false, 'mandant', false)), 9);
    delete from public.app_console_job where id::text = res->>'job_id';
{test('T6', 'modification non affirmee : aucune ligne', f"{carnet(1001384, 'notaire_mandant_id')} is null", carnet(1001384, 'notaire_mandant_id'))}

    -- T7 L'INVERSE
    {bloc_inverse(*FONCTIONS[0], "retour_c_rep").replace("DO $retour_c_rep$", "EXECUTE $exec_ic$ DO $retour_c_rep$").replace("$retour_c_rep$;", "$retour_c_rep$ $exec_ic$;")}
    {bloc_inverse(*FONCTIONS[1], "retour_m_rep").replace("DO $retour_m_rep$", "EXECUTE $exec_im$ DO $retour_m_rep$").replace("$retour_m_rep$;", "$retour_m_rep$ $exec_im$;")}
{test('T7', 'l inverse rend les deux empreintes', f"md5(replace(pg_get_functiondef('{FN_C}'::regprocedure), chr(13), '')) = '{AVANT_C}' and md5(replace(pg_get_functiondef('{FN_M}'::regprocedure), chr(13), '')) = '{AVANT_M}'", "'empreinte differente'")}

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
