# Genere les 3 fichiers du patch V (le COMPROMIS est verrouille par sa VENTE).
#     python phase2/checks/gen_patch_v_compromis_verrouille.py                    -> la requete d'empreinte (lecture seule)
#     python phase2/checks/gen_patch_v_compromis_verrouille.py <apres_G> <apres_M> -> les 3 fichiers
# Meme patron que gen_patch_n_offre_notaire_vendeur.py : l'empreinte d'apres se calcule dans la base.
# Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, sections 33 et 34.
import pathlib, sys

OUT = pathlib.Path(__file__).resolve().parents[2] / "supabase"
BASE = "patch_v_compromis_verrouille_2026-10-23"
CLE = "compromis_verrouille_par_vente"
INTER = f"coalesce((select s.value from public.app_setting s where s.key = '{CLE}'), 'off') = 'on'"

FN_G = "public.app_geste_affaire_optimistic(bigint,text,integer)"
AVANT_G = "20eeca7cc00bd4afe5b4175febacb2f7"      # mesuree le 23/10
FN_M = "public.app_modifier_affaire_optimistic(bigint,jsonb,integer)"
AVANT_M = "43247de7ff89e395d3b6e970353a891b"      # apres le patch N, mesuree le 23/10

# La vente qui verrouille : dans la MEME chaine, et pas effacee chez Hektor -- la clause du verrou de l'offre
# (16/09) et du chainage (07/09) : une vente supprimee chez eux ne doit pas tenir le compromis en otage.
def vente_de_la_chaine(var):
    return (f"      SELECT l.hektor_affaire_id::text INTO {var}\n"
            "        FROM app_affaire_ledger l\n"
            "       WHERE l.app_chaine_id = a.app_chaine_id\n"
            "         AND l.app_affaire_id <> a.app_affaire_id\n"
            "         AND l.kind = 'vente'\n"
            "         AND NOT (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''\n"
            "                  AND l.present_in_hektor IS FALSE)\n"
            "       LIMIT 1;")

MESSAGE = ("'compromis_verrouille: ce dossier porte une vente (n° %). Pour revenir sur le compromis, "
           "il faut d''abord supprimer la vente.'")

ANC_G = "  -- Une transaction DEJA dans cet etat : on ne renvoie pas de travail pour rien."
NEUF_G = "\n".join([
    "  -- ⛔ ─── V (23/10/2026, chantier 8) : LE COMPROMIS EST VERROUILLE PAR SA VENTE ─── ⛔",
    "  -- Decision de Frederic : « apres la vente tout est verrouille ; pour modifier quoi que ce soit sur",
    "  -- le compromis, il faut d'abord supprimer la vente ». Meme regle que l'offre ci-dessus (16/09).",
    "  -- Essai reel du 23/10 (compromis 50135/50136) : sans elle, modifier le compromis d'une chaine vendue",
    f"  -- remettait le bien « Sous compromis » chez Hektor. Interrupteur '{CLE}'.",
    "  IF a.kind = 'compromis' AND geste IN ('annuler', 'supprimer') AND a.app_chaine_id IS NOT NULL",
    f"     AND {INTER} THEN",
    vente_de_la_chaine("bloc_id"),
    "    IF FOUND THEN",
    f"      RAISE EXCEPTION {MESSAGE},",
    "        coalesce(nullif(btrim(bloc_id), ''), '?') USING errcode = '22023';",
    "    END IF;",
    "  END IF;",
    "",
    ANC_G,
])

ANC_M = "  select * into d from app_dossier_current where app_dossier_id = a.app_dossier_id;"
NEUF_M = "\n".join([
    "  -- ⛔ ─── V (23/10/2026, chantier 8) : LE COMPROMIS EST VERROUILLE PAR SA VENTE ─── ⛔",
    "  -- Voir app_geste_affaire_optimistic. Modifier le compromis d'une chaine vendue renvoie son statut a",
    "  -- Hektor (« Sous compromis ») alors que la vente existe. ⚠ v_cible sert ici de tampon : elle est",
    "  -- reaffectee plus bas (genre vise), sans rapport.",
    f"  if a.kind = 'compromis' and a.app_chaine_id is not null and {INTER} then",
    vente_de_la_chaine("v_cible"),
    "    if found then",
    f"      raise exception {MESSAGE},",
    "        coalesce(nullif(btrim(v_cible), ''), '?') using errcode = '22023';",
    "    end if;",
    "  end if;",
    "",
    ANC_M,
])

FONCTIONS = [
    ("G", FN_G, AVANT_G, [(ANC_G, NEUF_G)], "app_geste_affaire_optimistic"),
    ("M", FN_M, AVANT_M, [(ANC_M, NEUF_M)], "app_modifier_affaire_optimistic"),
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
APRES = {"G": sys.argv[1], "M": sys.argv[2]}
for code, _fn, avant, _a, _n in FONCTIONS:
    assert len(APRES[code]) == 32 and APRES[code] != avant, code


def bloc(code, fn, avant, ancres, nom, etiquette, sens):
    a, n = tableaux(code, ancres)
    apres = APRES[code]
    if sens == "pose":
        de, vers, src, dst, lib_de, lib_vers = avant, apres, "ancres", "neufs", "attendu", "posee"
        deja = f"RAISE NOTICE '%', 'Deja pose : {nom} porte deja l''empreinte {apres[:8]}. Rien n''est ecrit.'; RETURN;"
        test_deja = apres
    else:
        de, vers, src, dst = apres, avant, "neufs", "ancres"
        deja = f"RAISE NOTICE '%', 'Rien a retirer : {nom} porte deja l''empreinte d''avant ({avant[:8]}).'; RETURN;"
        test_deja = avant
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
    IF md5(d) = '{test_deja}' THEN
        {deja}
    END IF;
    IF md5(d) <> '{de}' THEN
        RAISE EXCEPTION '%', format('ARRET : {nom} a l''empreinte %s, attendu {de[:8]}. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length({src}, 1) LOOP
        nb := (length(d) - length(replace(d, {src}[i], ''))) / length({src}[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : {nom}, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, {src}[i], {dst}[i]);
    END LOOP;
    IF md5(d) <> '{vers}' THEN
        RAISE EXCEPTION '%', format('ARRET : {nom}, le texte rendu a l''empreinte %s, attendu {vers[:8]} (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('{fn}'::regprocedure), chr(13), '')) <> '{vers}' THEN
        RAISE EXCEPTION '%', 'ARRET : {nom}, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
${etiquette}$;"""


INTERRUPTEUR = f"""insert into public.app_setting (key, value, description, updated_at)
values ('{CLE}', 'off',
        'Chantier 8 / V 23/10/2026 : on = un COMPROMIS dont la chaine porte une VENTE ne se modifie, ne s''annule et ne se supprime plus (« pour revenir sur le compromis, il faut d''abord supprimer la vente » -- decision de Frederic). Voir supabase/{BASE}.sql. off = comportement d''avant.',
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
-- CHANTIER ⑧ · V — LE COMPROMIS EST VERROUILLÉ PAR SA VENTE                     23/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (sections 33 et 34). Décision de
-- Frédéric : « après la vente tout est verrouillé ; pour modifier quoi que ce soit sur le compromis, il faut
-- d'abord supprimer la vente ».
--
-- LE DÉFAUT (essai réel du 23/10, compromis 50136 / vente 23357 sur VA6482). L'offre est verrouillée par
-- son compromis et sa vente depuis le 16/09 (patch_offre_verrouillee) ; le COMPROMIS, lui, ne l'était par
-- rien : le modifier renvoyait son statut à Hektor et remettait un bien VENDU « Sous compromis ».
--
-- CE QUE FAIT CE PATCH — DEUX ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting '{CLE}', posé à 'off' ;
--   2. app_geste_affaire_optimistic : « annuler » et « supprimer » un compromis dont la chaîne porte une
--      vente (non effacée chez Hektor) sont REFUSÉS, avec la raison et le geste qui débloque ;
--   3. app_modifier_affaire_optimistic : la modification d'un tel compromis est REFUSÉE, de même.
--   Rien d'autre ne change : l'offre, la vente (elle se supprime toujours), un compromis sans vente.
--
-- ⛔ GARDE : empreintes {AVANT_G[:8]} (gestes) et {AVANT_M[:8]} (modification) exigées, chaque ancre trouvée UNE
--    fois, textes neufs {APRES['G'][:8]} / {APRES['M'][:8]} CALCULÉS D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
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

-- 2. LES GESTES
{bloc(*FONCTIONS[0], "pose_g", "pose")}

-- 3. LA MODIFICATION
{bloc(*FONCTIONS[1], "pose_m", "pose")}

-- 4. LES CONTRÔLES — tous doivent dire OK
{controles()}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE V — le compromis verrouillé par sa vente   23/10/2026
-- Il rend aux deux fonctions leur texte d'avant ({AVANT_G[:8]} / {AVANT_M[:8]}), par les MÊMES ancres, et
-- retire l'interrupteur. Il ne touche aucune donnée. Pour seulement SUSPENDRE : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

{bloc(*FONCTIONS[0], "retour_g", "inverse")}

{bloc(*FONCTIONS[1], "retour_m", "inverse")}

delete from public.app_setting where key = '{CLE}';

SELECT 1 AS "#", 'app_geste_affaire_optimistic a retrouve {AVANT_G[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN_G}'::regprocedure), chr(13), '')) = '{AVANT_G}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
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


def essai(appel):
    """Appelle, et rend dans `err` le message d'erreur (ou '') ; le travail cree est retire aussitot."""
    return f"""    err := '';
    BEGIN
      res := {appel};
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;"""


MODIF = "jsonb_build_object('amount', '115000', 'champs_touches', jsonb_build_array())"
COMP, VENTE, OFFRE = 1001391, 1001392, 1001390

repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE V — le compromis verrouillé par sa vente    23/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni les fonctions
--   modifiées, ni l'interrupteur, ni les travaux, ni le registre.
-- Le VRAI PATCH, puis les fonctions appelées COMME L'ÉCRAN, au nom de Frédéric, sur la chaîne d'essai 1001390
-- de VA6482 (offre {OFFRE}, compromis {COMP} = 50136, vente {VENTE} = 23357 ; essai 4 du 23/10).
--   T1 ÉTEINT : modifier le compromis → accepté (le témoin inverse : le défaut)
--   T2 allumé : modifier le compromis → REFUSÉ « compromis_verrouille »
--   T3 allumé : annuler le compromis → REFUSÉ   · T4 allumé : supprimer le compromis → REFUSÉ
--   T5 allumé : modifier la VENTE → accepté (la vente n'est pas verrouillée)
--   T6 allumé : le verrou de l'OFFRE répond toujours (refuser l'offre → « offre_verrouillee »)
--   T7 allumé : la vente EFFACÉE chez Hektor ne verrouille plus → modifier le compromis accepté
--   T8 l'inverse rend {AVANT_G[:8]} et {AVANT_M[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    res jsonb;
    err text;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.app_affaire_ledger WHERE app_affaire_id = {COMP} AND kind = 'compromis')
       OR NOT EXISTS (SELECT 1 FROM public.app_affaire_ledger WHERE app_affaire_id = {VENTE} AND kind = 'vente' AND present_in_hektor IS NOT FALSE) THEN
        RAISE EXCEPTION '%', 'ARRET : la chaine d''essai 1001390 n''a plus son compromis ou sa vente -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc(*FONCTIONS[0], "pose_g_rep", "pose").replace("DO $pose_g_rep$", "EXECUTE $exec_g$ DO $pose_g_rep$").replace("$pose_g_rep$;", "$pose_g_rep$ $exec_g$;")}
    {bloc(*FONCTIONS[1], "pose_m_rep", "pose").replace("DO $pose_m_rep$", "EXECUTE $exec_m$ DO $pose_m_rep$").replace("$pose_m_rep$;", "$pose_m_rep$ $exec_m$;")}

    -- T1 ETEINT
{essai(f"public.app_modifier_affaire_optimistic({COMP}, {MODIF}, 9)")}
{test('T1', 'eteint : modifier le compromis est accepte', "err = ''", "err")}

    update public.app_setting set value = 'on' where key = '{CLE}';
    -- T2
{essai(f"public.app_modifier_affaire_optimistic({COMP}, {MODIF}, 9)")}
{test('T2', 'allume : modifier le compromis est refuse', "err like 'compromis_verrouille:%' and err like '%23357%'", "nullif(err, '')")}
    -- T3
{essai(f"public.app_geste_affaire_optimistic({COMP}, 'annuler', 9)")}
{test('T3', 'allume : annuler le compromis est refuse', "err like 'compromis_verrouille:%'", "nullif(err, '')")}
    -- T4
{essai(f"public.app_geste_affaire_optimistic({COMP}, 'supprimer', 9)")}
{test('T4', 'allume : supprimer le compromis est refuse', "err like 'compromis_verrouille:%'", "nullif(err, '')")}
    -- T5
{essai(f"public.app_modifier_affaire_optimistic({VENTE}, {MODIF}, 9)")}
{test('T5', 'allume : modifier la vente reste accepte', "err = ''", "err")}
    -- T6
{essai(f"public.app_geste_affaire_optimistic({OFFRE}, 'refus', 9)")}
{test('T6', 'le verrou de l offre repond toujours', "err like 'offre_verrouillee:%'", "nullif(err, '')")}
    -- T7
    update public.app_affaire_ledger set present_in_hektor = false where app_affaire_id = {VENTE};
{essai(f"public.app_modifier_affaire_optimistic({COMP}, {MODIF}, 9)")}
    update public.app_affaire_ledger set present_in_hektor = true where app_affaire_id = {VENTE};
{test('T7', 'une vente effacee chez Hektor ne verrouille plus', "err = ''", "err")}

    -- T8 L'INVERSE
    {bloc(*FONCTIONS[0], "retour_g_rep", "inverse").replace("DO $retour_g_rep$", "EXECUTE $exec_ig$ DO $retour_g_rep$").replace("$retour_g_rep$;", "$retour_g_rep$ $exec_ig$;")}
    {bloc(*FONCTIONS[1], "retour_m_rep", "inverse").replace("DO $retour_m_rep$", "EXECUTE $exec_im$ DO $retour_m_rep$").replace("$retour_m_rep$;", "$retour_m_rep$ $exec_im$;")}
{test('T8', 'l inverse rend les deux empreintes', f"md5(replace(pg_get_functiondef('{FN_G}'::regprocedure), chr(13), '')) = '{AVANT_G}' and md5(replace(pg_get_functiondef('{FN_M}'::regprocedure), chr(13), '')) = '{AVANT_M}'", "'empreinte differente'")}

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
