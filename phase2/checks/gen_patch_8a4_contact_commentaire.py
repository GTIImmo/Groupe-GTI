# Genere les 3 fichiers du patch 8a-A (le commentaire au clic) depuis LES MEMES ancres.
import json, pathlib

S = pathlib.Path(__file__).parent
OUT = pathlib.Path(r"C:\Hektor\Projet\supabase")
ANCRES = json.loads(S.joinpath("patch_a_ancres.json").read_text(encoding="utf-8"))
AVANT = "79d39e0e506d8afd3224fe20624598b3"
APRES = "eb93494b0856706f1f0426da7571d306"
FN = "public.app_edit_contact_optimistic(text,jsonb,integer)"
BASE = "patch_8a4_contact_commentaire_au_clic_2026-10-22"


def lit(t, i, cote):
    tag = f"${cote}{i}$"
    assert tag not in t
    return f"replace({tag}{t}{tag}, chr(13), '')"


def bloc_pose(nom_bloc, indent=""):
    a = ",\n        ".join(lit(x, i + 1, "a") for i, (x, _) in enumerate(ANCRES))
    n = ",\n        ".join(lit(y, i + 1, "n") for i, (_, y) in enumerate(ANCRES))
    return f"""DO ${nom_bloc}$
DECLARE
    d text := replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '');
    ancres text[] := array[
        {a}];
    neufs text[] := array[
        {n}];
    i int;
    nb int;
BEGIN
    IF md5(d) = '{APRES}' THEN
        RAISE NOTICE '%', 'Deja pose : app_edit_contact_optimistic porte deja l''empreinte {APRES[:8]}. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '{AVANT}' THEN
        RAISE EXCEPTION '%', format('ARRET : app_edit_contact_optimistic a l''empreinte %s, attendu {AVANT[:8]} (21/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '{APRES}' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu {APRES[:8]} (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) <> '{APRES}' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
${nom_bloc}$;"""


def bloc_inverse():
    a = ",\n        ".join(lit(x, i + 1, "a") for i, (x, _) in enumerate(ANCRES))
    n = ",\n        ".join(lit(y, i + 1, "n") for i, (_, y) in enumerate(ANCRES))
    return f"""DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '');
    ancres text[] := array[
        {a}];
    neufs text[] := array[
        {n}];
    i int;
    nb int;
BEGIN
    IF md5(d) = '{AVANT}' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_edit_contact_optimistic porte deja l''empreinte du 21/10 ({AVANT[:8]}).';
        RETURN;
    END IF;
    IF md5(d) <> '{APRES}' THEN
        RAISE EXCEPTION '%', format('ARRET : app_edit_contact_optimistic a l''empreinte %s, ni {APRES[:8]} (posee) ni {AVANT[:8]} (d''avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '{AVANT}' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu {AVANT[:8]}. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$;"""


INTERRUPTEUR = """insert into public.app_setting (key, value, description, updated_at)
values ('contact_commentaire_au_clic', 'off',
        'Chantier 8 / 8a-A 22/10/2026 : on = le commentaire saisi en modifiant un contact s''ecrit chez nous au clic (voir supabase/patch_8a4_contact_commentaire_au_clic_2026-10-22.sql). off = comportement d''avant (il n''arrive qu''au retour de Hektor).',
        now())
on conflict (key) do nothing;"""

CONTROLES = f"""SELECT 1 AS "#", 'app_edit_contact_optimistic porte l''empreinte {APRES[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{APRES}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_commentaire_au_clic' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les droits d''appel sont inchanges (authenticated peut appeler)',
       CASE WHEN has_function_privilege('authenticated', '{FN}', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;"""

ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · 8a-A — LE COMMENTAIRE D'UN CONTACT S'ÉCRIT CHEZ NOUS AU CLIC    22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (« 8a, fin — LA MODIFICATION DE CONTACT »)
--
-- LE DÉFAUT (audit du 22/10). En modifiant un contact, l'écran envoie le commentaire
-- (`comments`) à app_edit_contact_optimistic, mais elle ne le connaît pas : il part chez
-- Hektor et ne revient chez nous qu'à la relecture, ~11 minutes après (10 min d'attente
-- voulue + ~40 s). Hektor parti, il ne s'afficherait jamais. Les 12 autres champs, eux,
-- s'écrivent au clic.
--
-- CE QUE FAIT CE PATCH — CHIRURGICAL, TROIS ANCRES D'UNE LIGNE :
--   1. un INTERRUPTEUR, app_setting 'contact_commentaire_au_clic', posé à 'off' ;
--   2. dans app_edit_contact_optimistic : lu au début ; allumé, `comments` (ou
--      `commentaires`) s'écrit dans la colonne commentaires, et sa valeur d'avant entre
--      dans la photo (base_snapshot) comme les 12 autres. ÉTEINT : RIEN NE CHANGE.
--   Rien d'autre n'est touché : le travail pour Hektor, l'attente, la garde
--   anti-écrasement (elle ne lit que _date_maj) et la relecture restent ce qu'ils sont.
--
-- ⛔ GARDE : la fonction n'est modifiée que si son empreinte est {AVANT[:8]} (relevée le
--    21/10 et le 22/10), chaque ancre trouvée UNE fois, et le texte neuf porte
--    l'empreinte {APRES[:8]} CALCULÉE D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'contact_commentaire_au_clic';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'contact_commentaire_au_clic';
-- RETOUR ARRIÈRE COMPLET : supabase/{BASE}_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
"""

pose = f"""{ENTETE}
BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
{INTERRUPTEUR}

-- 2. LA FONCTION, PAR SES TROIS ANCRES
{bloc_pose("pose")}

-- 3. LES CONTRÔLES — tous doivent dire OK
{CONTROLES}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a-A — le commentaire au clic                           22/10/2026
-- Il rend à app_edit_contact_optimistic son texte du 21/10 (empreinte {AVANT[:8]}),
-- par les MÊMES ancres, et retire l'interrupteur. Il ne touche aucune donnée : les
-- commentaires déjà écrits au clic restent (la relecture de Hektor les confirme ou
-- les remplace, comme avant le patch).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

{bloc_inverse()}

delete from public.app_setting where key = 'contact_commentaire_au_clic';

SELECT 1 AS "#", 'app_edit_contact_optimistic a retrouve l''empreinte {AVANT[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_commentaire_au_clic') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
"""

repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a-A — le commentaire au clic                              22/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE : tout se passe dans UN bloc qui finit par une erreur
--   volontaire (« ESSAI ANNULE -- … ») ; le message porte le résultat. Rien ne reste :
--   ni la fonction modifiée, ni l'interrupteur, ni la saisie, ni la ligne d'attente.
-- Elle joue LE VRAI PATCH (mêmes ancres), puis appelle la fonction COMME L'ÉCRAN, au nom
-- de Frédéric, sur le contact d'essai 20000007 (« ESSAI 8A BIS », à supprimer) :
--   T1 interrupteur ÉTEINT  → le commentaire n'est PAS écrit (le témoin inverse) ;
--   T2 interrupteur ALLUMÉ  → il est écrit, il est dans la ligne d'attente, et sa valeur
--      d'avant est dans la photo ;
--   T3 les 12 autres champs s'écrivent toujours (nom changé dans T1 et T2) ;
--   T4 l'alias `commentaires` marche aussi ;
--   T5 l'inverse rend l'empreinte {AVANT[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    cid text := '20000007';
    avant_com text;
    r text := '';
    v text;
    snap jsonb;
    pf jsonb;
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (select 1 from public.app_contact_current where hektor_contact_id = cid) THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai 20000007 n''existe plus -- la repetition ne prouverait rien.';
    END IF;
    IF EXISTS (select 1 from public.app_contact_pending where hektor_contact_id = cid) THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai a deja une saisie en attente -- la repetition la melangerait.';
    END IF;
    select commentaires into avant_com from public.app_contact_current where hektor_contact_id = cid;

    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc_pose("pose_rep").replace("DO $pose_rep$", "EXECUTE $exec_pose$ DO $pose_rep$").replace("$pose_rep$;", "$pose_rep$ $exec_pose$;")}

    -- T1 ETEINT : le commentaire ne doit PAS s'ecrire
    update public.app_setting set value = 'off' where key = 'contact_commentaire_au_clic';
    PERFORM public.app_edit_contact_optimistic(cid, jsonb_build_object('last_name', 'ESSAI 8A BIS T1', 'comments', 'COMMENTAIRE T1 ETEINT'), 0);
    select commentaires into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v is not distinct from avant_com THEN ok := ok + 1; r := r || ' | T1 OK eteint : commentaire inchange';
    ELSE r := r || ' | T1 ECHEC eteint : commentaire = ' || coalesce(v, 'null'); END IF;
    select nom into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v = 'ESSAI 8A BIS T1' THEN ok := ok + 1; r := r || ' | T3a OK nom ecrit (eteint)';
    ELSE r := r || ' | T3a ECHEC nom = ' || coalesce(v, 'null'); END IF;
    delete from public.app_contact_pending where hektor_contact_id = cid;

    -- T2 ALLUME : le commentaire s'ecrit, part dans l'attente, et sa valeur d'avant est dans la photo
    update public.app_setting set value = 'on' where key = 'contact_commentaire_au_clic';
    PERFORM public.app_edit_contact_optimistic(cid, jsonb_build_object('last_name', 'ESSAI 8A BIS T2', 'comments', 'COMMENTAIRE T2 ALLUME'), 0);
    select commentaires into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v = 'COMMENTAIRE T2 ALLUME' THEN ok := ok + 1; r := r || ' | T2a OK allume : commentaire ecrit au clic';
    ELSE r := r || ' | T2a ECHEC allume : commentaire = ' || coalesce(v, 'null'); END IF;
    select base_snapshot, push_fields into snap, pf from public.app_contact_pending where hektor_contact_id = cid;
    total := total + 1;
    IF pf->>'comments' = 'COMMENTAIRE T2 ALLUME' THEN ok := ok + 1; r := r || ' | T2b OK le commentaire part chez Hektor (attente)';
    ELSE r := r || ' | T2b ECHEC attente = ' || coalesce(pf::text, 'null'); END IF;
    total := total + 1;
    IF snap ? 'comments' AND (snap->>'comments') is not distinct from avant_com AND snap ? '_date_maj' THEN ok := ok + 1; r := r || ' | T2c OK photo : valeur d''avant + _date_maj';
    ELSE r := r || ' | T2c ECHEC photo = ' || coalesce(snap::text, 'null'); END IF;
    select nom into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v = 'ESSAI 8A BIS T2' THEN ok := ok + 1; r := r || ' | T3b OK nom ecrit (allume)';
    ELSE r := r || ' | T3b ECHEC nom = ' || coalesce(v, 'null'); END IF;
    delete from public.app_contact_pending where hektor_contact_id = cid;

    -- T4 l'alias « commentaires »
    PERFORM public.app_edit_contact_optimistic(cid, jsonb_build_object('last_name', 'ESSAI 8A BIS T4', 'commentaires', 'COMMENTAIRE T4 ALIAS'), 0);
    select commentaires into v from public.app_contact_current where hektor_contact_id = cid;
    total := total + 1;
    IF v = 'COMMENTAIRE T4 ALIAS' THEN ok := ok + 1; r := r || ' | T4 OK alias commentaires';
    ELSE r := r || ' | T4 ECHEC alias : commentaire = ' || coalesce(v, 'null'); END IF;
    delete from public.app_contact_pending where hektor_contact_id = cid;

    -- T5 L'INVERSE
    {bloc_inverse().replace("DO $retour$", "EXECUTE $exec_inv$ DO $retour$").replace("$retour$;", "$retour$ $exec_inv$;")}
    total := total + 1;
    IF md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}' THEN ok := ok + 1; r := r || ' | T5 OK l''inverse rend {AVANT[:8]}';
    ELSE r := r || ' | T5 ECHEC inverse'; END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
