# Genere les 3 fichiers du patch 1b (l'acquereur sous SON numero Hektor) depuis LES MEMES ancres.
#     python -I phase2/checks/gen_patch_1b_affaire_acquereur_numero_hektor.py              -> la requete d'empreinte
#     python -I phase2/checks/gen_patch_1b_affaire_acquereur_numero_hektor.py <empreinte>  -> les 3 fichiers
# Meme patron que gen_patch_r1_affaire_nait_complete.py : l'empreinte d'apres se calcule dans la base.
import pathlib, sys

OUT = pathlib.Path(__file__).resolve().parents[2] / "supabase"
AVANT = "caab6b6c38091ba5b087f8819147756f"     # apres R1 (22/10, 18:19)
FN = "public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)"
BASE = "patch_1b_affaire_acquereur_numero_hektor_2026-10-22"
CLE = "affaire_acquereur_numero_hektor"

BLOC_1B = """  -- ─── 1b (22/10/2026, chantier 8) : L'ACQUEREUR SOUS SON NUMERO HEKTOR ───
  -- `hektor_acquereur_id` est la CLE du rapprochement de nuit (affaire_ledger.py, par
  -- acquereur) et de la chaine (app_chaine_pour la compare aux lignes venues de Hektor).
  -- Or l'ecran envoie tantot NOTRE identite (la recherche de contacts : 20000008 le 22/10),
  -- tantot le numero Hektor (605717 le 13/10). Les 62 288 contacts ont deux numeros
  -- differents : l'identite y faisait echouer le rapprochement (doublon de nuit), le
  -- numero Hektor y faisait perdre le lien vers notre contact (app_contact_id vide).
  -- Allume : on reconnait les DEUX (identite d'abord, numero Hektor ensuite), on range le
  -- numero Hektor ici et notre identite dans app_contact_id. Inconnu : on garde ce qui est
  -- venu, on n'invente rien. Le worker n'est PAS concerne : il lit la charge et traduit
  -- lui-meme. Eteint : comportement d'avant.
  if coalesce((select s.value from public.app_setting s
                where s.key = 'affaire_acquereur_numero_hektor'), 'off') = 'on' then
    if v_acquereur is not null and v_acquereur_app is null then
      select c.app_contact_id, nullif(btrim(coalesce(c.hektor_target_id, '')), '')
        into v_acquereur_app, v_acquereur_cible
        from app_contact_current c
       where c.hektor_target_id = v_acquereur
       limit 1;
    end if;
    v_acquereur_cible := coalesce(v_acquereur_cible, v_acquereur);
  else
    v_acquereur_cible := v_acquereur;
  end if;

  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───"""

ANCRES = [
    ("  v_nait_complete boolean := false;",
     "  v_nait_complete boolean := false;\n  -- 1b 22/10/2026 : l'acquereur sous son numero Hektor (interrupteur affaire_acquereur_numero_hektor)\n  v_acquereur_cible text;"),
    ("    select c.app_contact_id into v_acquereur_app",
     "    select c.app_contact_id, nullif(btrim(coalesce(c.hektor_target_id, '')), '') into v_acquereur_app, v_acquereur_cible"),
    ("  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───", BLOC_1B),
    ("       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur, v_kind, v_affaire_id),",
     "       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur_cible, v_kind, v_affaire_id),"),
    ("       v_acquereur,",
     "       v_acquereur_cible,         -- 1b : le numero Hektor (allume) ou ce qui est venu (eteint)"),
]


def lit(t, i, cote):
    tag = f"${cote}{i}$"
    assert tag not in t
    return f"replace({tag}{t}{tag}, chr(13), '')"


def tableaux():
    a = ",\n        ".join(lit(x, i + 1, "a") for i, (x, _) in enumerate(ANCRES))
    n = ",\n        ".join(lit(y, i + 1, "n") for i, (_, y) in enumerate(ANCRES))
    return a, n


def requete_empreinte():
    d = f"replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')"
    for i, (x, y) in enumerate(ANCRES):
        d = f"replace({d}, {lit(x, i + 1, 'a')}, {lit(y, i + 1, 'n')})"
    return (f"select md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) avant,\n"
            f"       md5({d}) apres;")


sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 2:
    print(requete_empreinte())
    sys.exit(0)
APRES = sys.argv[1]
assert len(APRES) == 32 and APRES != AVANT


def bloc_pose(nom_bloc):
    a, n = tableaux()
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
        RAISE NOTICE '%', 'Deja pose : app_change_annonce_status_optimistic porte deja l''empreinte {APRES[:8]}. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '{AVANT}' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu {AVANT[:8]} (R1, 22/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
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
    a, n = tableaux()
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
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte de R1 ({AVANT[:8]}).';
        RETURN;
    END IF;
    IF md5(d) <> '{APRES}' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, ni {APRES[:8]} (posee) ni {AVANT[:8]} (R1). Rien n''est ecrit.', md5(d));
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


INTERRUPTEUR = f"""insert into public.app_setting (key, value, description, updated_at)
values ('{CLE}', 'off',
        'Chantier 8 / 1b 22/10/2026 : on = une transaction creee dans l''app range l''acquereur sous SON numero Hektor dans hektor_acquereur_id (cle du rapprochement de nuit), et retrouve notre contact meme si l''ecran a envoye le numero Hektor (voir supabase/{BASE}.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;"""

CONTROLES = f"""SELECT 1 AS "#", 'app_change_annonce_status_optimistic porte l''empreinte {APRES[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{APRES}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les droits d''appel sont inchanges (authenticated peut appeler)',
       CASE WHEN has_function_privilege('authenticated', '{FN}', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'l''interrupteur de R1 est toujours la',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_nait_complete') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;"""

ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · 1b — L'ACQUÉREUR SOUS SON NUMÉRO HEKTOR                         22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (section 6)
--
-- LE DÉFAUT (essai réel du 22/10, VA6482). La RPC range dans hektor_acquereur_id le numéro
-- envoyé par l'écran. Les 62 288 contacts ont DEUX numéros (notre identité ≥ 10 M, le leur) et
-- l'écran envoie tantôt l'un, tantôt l'autre :
--   identité (20000008)    -> la nuit ne rapproche pas la ligne du compromis de Hektor : DOUBLON
--   numéro Hektor (605717) -> le lien vers notre contact (app_contact_id) se perd (la nuit le refait)
--
-- CE QUE FAIT CE PATCH — CHIRURGICAL, CINQ ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   allumé, la RPC reconnaît le contact par l'un OU l'autre numéro, range le numéro HEKTOR
--   dans hektor_acquereur_id et passe le même à app_chaine_pour ; notre identité reste dans
--   app_contact_id. Contact inconnu : rien n'est inventé. Éteint : comportement d'avant.
--   ⚠ LE WORKER N'EST PAS TOUCHÉ : il lit la charge (inchangée) et traduit lui-même.
--
-- ⛔ GARDE : empreinte {AVANT[:8]} exigée (posée par R1 le 22/10 à 18:19), chaque ancre trouvée
--    UNE fois, texte neuf {APRES[:8]} CALCULÉ D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
-- ⚠ ORDRE DES RETOURS ARRIÈRE : l'inverse de 1b AVANT celui de R1 (R1 exige {AVANT[:8]}).
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = '{CLE}';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = '{CLE}';
-- RETOUR ARRIÈRE COMPLET : supabase/{BASE}_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
"""

pose = f"""{ENTETE}
BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
{INTERRUPTEUR}

-- 2. LA FONCTION, PAR SES CINQ ANCRES
{bloc_pose("pose")}

-- 3. LES CONTRÔLES — tous doivent dire OK
{CONTROLES}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 1b — l'acquéreur sous son numéro Hektor                   22/10/2026
-- Il rend à app_change_annonce_status_optimistic son texte de R1 (empreinte {AVANT[:8]}), par
-- les MÊMES ancres, et retire l'interrupteur. Il ne touche aucune donnée.
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

{bloc_inverse()}

delete from public.app_setting where key = '{CLE}';

SELECT 1 AS "#", 'app_change_annonce_status_optimistic a retrouve l''empreinte {AVANT[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
"""


def appel(acq):
    return (f"(public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object("
            f"'amount', '130000', 'sale_price', '130000', 'transaction_date', '2026-10-22', "
            f"'buyer_contact_id', '{acq}', 'numero_mandat', '99999', 'titre_bien', 'ESSAI 1B'), 0)"
            f"->>'app_affaire_id')::bigint")


def test(num, libelle, condition, detail):
    return f"""    total := total + 1;
    IF {condition} THEN ok := ok + 1; r := r || ' | {num} OK {libelle}';
    ELSE r := r || ' | {num} ECHEC {libelle} : ' || coalesce({detail}, 'null'); END IF;"""


def cas(num, libelle, acq, attendu_hk, attendu_app):
    app = "l.app_contact_id is null" if attendu_app is None else f"l.app_contact_id = {attendu_app}"
    return f"""    aid := {appel(acq)};
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
{test(num, libelle, f"l.hektor_acquereur_id = '{attendu_hk}' and {app} and l.app_chaine_id is not null", "l.hektor_acquereur_id || ' / ' || coalesce(l.app_contact_id::text, 'null') || ' / chaine ' || coalesce(l.app_chaine_id::text, 'null')")}"""


repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 1b — l'acquéreur sous son numéro Hektor                      22/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni la
--   fonction modifiée, ni l'interrupteur, ni les transactions, ni les travaux. (La séquence des
--   numéros avance de 6 : une séquence ne recule jamais.)
-- Le VRAI PATCH, puis la fonction appelée COMME L'ÉCRAN, au nom de Frédéric, sur l'annonce
-- d'essai 63331 (dossier 10000009) :
--   T1 ÉTEINT, identité 20000008      → 20000008 rangé tel quel (le témoin inverse du doublon)
--   T2 ÉTEINT, numéro Hektor 605717    → app_contact_id VIDE (le témoin inverse du lien perdu)
--   T3 ALLUMÉ, identité 20000008      → 605946, notre contact 20000008
--   T4 ALLUMÉ, identité 10650570      → 605717, notre contact 10650570
--   T5 ALLUMÉ, numéro Hektor 605717    → 605717, notre contact 10650570 RETROUVÉ
--   T6 ALLUMÉ, numéro inconnu 999999999 → rangé tel quel, aucun contact inventé
--   (chaque cas exige aussi une chaîne posée) · T7 l'inverse rend {AVANT[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    dossier bigint := 10000009;
    aid bigint;
    l public.app_affaire_ledger%rowtype;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (select 1 from public.app_dossier_current where app_dossier_id = dossier) THEN
        RAISE EXCEPTION '%', 'ARRET : le dossier d''essai 10000009 n''est plus dans le parc vivant.';
    END IF;
    IF (select count(*) from public.app_contact_current where hektor_contact_id in ('20000008', '10650570')) <> 2 THEN
        RAISE EXCEPTION '%', 'ARRET : un contact de l''essai a disparu -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc_pose("pose_rep").replace("DO $pose_rep$", "EXECUTE $exec_pose$ DO $pose_rep$").replace("$pose_rep$;", "$pose_rep$ $exec_pose$;")}

    update public.app_setting set value = 'off' where key = '{CLE}';
{cas('T1', 'eteint, identite : rangee telle quelle', '20000008', '20000008', 20000008)}
{cas('T2', 'eteint, numero Hektor : lien vers notre contact VIDE', '605717', '605717', None)}

    update public.app_setting set value = 'on' where key = '{CLE}';
{cas('T3', 'allume, identite 20000008 -> 605946', '20000008', '605946', 20000008)}
{cas('T4', 'allume, identite 10650570 -> 605717', '10650570', '605717', 10650570)}
{cas('T5', 'allume, numero Hektor 605717 -> contact 10650570 retrouve', '605717', '605717', 10650570)}
{cas('T6', 'allume, inconnu -> range tel quel, rien d invente', '999999999', '999999999', None)}

    -- T7 L'INVERSE
    {bloc_inverse().replace("DO $retour$", "EXECUTE $exec_inv$ DO $retour$").replace("$retour$;", "$retour$ $exec_inv$;")}
{test('T7', 'l inverse rend ' + AVANT[:8], f"md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}'", "'empreinte differente'")}

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
