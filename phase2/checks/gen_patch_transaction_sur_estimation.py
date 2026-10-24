# Genere les 3 fichiers du patch E-ST (pas de transaction sur un bien en ESTIMATION).
#     python phase2/checks/gen_patch_transaction_sur_estimation.py          -> la requete d'empreinte (lecture seule)
#     python phase2/checks/gen_patch_transaction_sur_estimation.py <apres>  -> les 3 fichiers
# Meme patron que gen_patch_v_compromis_verrouille.py : l'empreinte d'apres se calcule dans la base.
# Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, sections 45 et 46.
import pathlib, sys

OUT = pathlib.Path(__file__).resolve().parents[2] / "supabase"
BASE = "patch_transaction_sur_estimation_2026-10-24"
CLE = "transaction_refusee_sur_estimation"
INTER = f"coalesce((select s.value from public.app_setting s where s.key = '{CLE}'), 'off') = 'on'"

FN = "public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)"
NOM = "app_change_annonce_status_optimistic"
AVANT = "44697dd59587c644cdc021bd8f52108d"      # mesuree le 24/10 (apres le patch N du 23/10)

MESSAGE = ("'transaction_sur_estimation: ce bien est en Estimation. Une offre, un compromis ou une vente se font "
           "sur un bien Actif : passez-le d''abord en Actif.'")

# L'ancre : la fin du repli vers l'historique. A cet endroit `d` porte la fiche, du parc vivant OU de
# l'historique ; l'historique a deja refuse toute transaction juste au-dessus (transaction_hors_parc_vivant).
ANC = "  -- @repli-fin"
NEUF = "\n".join([
    ANC,
    "",
    "  -- ⛔ ─── ⑧ (24/10/2026) : PAS DE TRANSACTION SUR UN BIEN EN ESTIMATION ─── ⛔",
    "  -- La regle de Frederic : « pas de transaction pour les biens en etat Vendu, Clos ou Estimation ; si",
    "  -- l'etat revient a Actif, possibilite de refaire une nouvelle chaine ». Vendu et Clos sont refuses",
    "  -- juste au-dessus (hors parc vivant) ; l'Estimation, elle, est DANS le parc vivant (12 781 biens le",
    "  -- 24/10) et passait. On ne regarde que l'ETAT du bien, jamais ses anciennes transactions.",
    "  -- « Actif » et « Clos » (le chemin pour sortir de l'estimation) ne sont pas touches.",
    f"  -- Interrupteur '{CLE}'.",
    "  if target_status in ('offer', 'compromise', 'sold')",
    "     and lower(btrim(coalesce(d.statut_annonce, ''))) like '%estimation%'",
    f"     and {INTER} then",
    f"    raise exception {MESSAGE} using errcode = '22023';",
    "  end if;",
])


def lit(t, tag):
    assert f"${tag}$" not in t
    return f"replace(${tag}${t}${tag}$, chr(13), '')"


def requete_empreinte():
    d = f"replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')"
    return (f"select md5({d}) avant,\n"
            f"       md5(replace({d}, {lit(ANC, 'a1')}, {lit(NEUF, 'n1')})) apres;")


sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 2:
    print(requete_empreinte())
    sys.exit(0)
APRES = sys.argv[1]
assert len(APRES) == 32 and APRES != AVANT


def bloc(etiquette, sens):
    if sens == "pose":
        de, vers, src, dst, test_deja = AVANT, APRES, "ancres", "neufs", APRES
        deja = f"RAISE NOTICE '%', 'Deja pose : {NOM} porte deja l''empreinte {APRES[:8]}. Rien n''est ecrit.'; RETURN;"
    else:
        de, vers, src, dst, test_deja = APRES, AVANT, "neufs", "ancres", AVANT
        deja = f"RAISE NOTICE '%', 'Rien a retirer : {NOM} porte deja l''empreinte d''avant ({AVANT[:8]}).'; RETURN;"
    return f"""DO ${etiquette}$
DECLARE
    d text := replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '');
    ancres text[] := array[
        {lit(ANC, 'a1')}];
    neufs text[] := array[
        {lit(NEUF, 'n1')}];
    i int;
    nb int;
BEGIN
    IF md5(d) = '{test_deja}' THEN
        {deja}
    END IF;
    IF md5(d) <> '{de}' THEN
        RAISE EXCEPTION '%', format('ARRET : {NOM} a l''empreinte %s, attendu {de[:8]}. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length({src}, 1) LOOP
        nb := (length(d) - length(replace(d, {src}[i], ''))) / length({src}[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : {NOM}, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, {src}[i], {dst}[i]);
    END LOOP;
    IF md5(d) <> '{vers}' THEN
        RAISE EXCEPTION '%', format('ARRET : {NOM}, le texte rendu a l''empreinte %s, attendu {vers[:8]} (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) <> '{vers}' THEN
        RAISE EXCEPTION '%', 'ARRET : {NOM}, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
${etiquette}$;"""


INTERRUPTEUR = f"""insert into public.app_setting (key, value, description, updated_at)
values ('{CLE}', 'off',
        'Chantier 8 / 24/10/2026 : on = la creation d''une OFFRE, d''un COMPROMIS ou d''une VENTE est refusee sur un bien en ESTIMATION (« pas de transaction pour les biens Vendu, Clos ou Estimation » -- regle de Frederic ; Vendu et Clos sont deja refuses hors parc vivant). Voir supabase/{BASE}.sql. off = comportement d''avant.',
        now())
on conflict (key) do nothing;"""

CONTROLES = f"""SELECT 1 AS "#", '{NOM} porte l''empreinte {APRES[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{APRES}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, '{NOM} : droits d''appel inchanges, SECURITY DEFINER',
       CASE WHEN has_function_privilege('authenticated', '{FN}', 'EXECUTE') AND (SELECT prosecdef FROM pg_proc WHERE oid = '{FN}'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;"""

ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ — PAS DE TRANSACTION SUR UN BIEN EN ESTIMATION                       24/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (sections 45 et 46). Règle de
-- Frédéric (24/10) : « pas de transaction pour les biens en état Vendu, Clos ou Estimation ; si l'état revient
-- à Actif, possibilité de refaire une nouvelle chaîne ».
--
-- LE CONSTAT (mesure du 24/10). La création refuse déjà Vendu et Clos (hors parc vivant,
-- `transaction_hors_parc_vivant`) et l'archive. Mais l'ESTIMATION est DANS le parc vivant (12 781 biens) :
-- une offre, un compromis ou une vente y passaient, sans rien pour les arrêter. L'écran les cache depuis le
-- 24/10 ; ce patch est la SERRURE (« l'écran prévient, la base refuse »).
--
-- CE QUE FAIT CE PATCH — UNE ANCRE D'UNE LIGNE, ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting '{CLE}', posé à 'off' ;
--   2. {NOM} : créer une offre, un compromis ou une vente sur un bien en Estimation est REFUSÉ
--      (`transaction_sur_estimation`, traduit à l'écran). « Actif » et « Clos » passent toujours.
--   Rien d'autre ne change : Actif / Sous offre / Sous compromis, la MODIFICATION (autre fonction), les gestes.
--
-- ⛔ GARDE : empreinte {AVANT[:8]} exigée, ancre trouvée UNE fois, texte neuf {APRES[:8]} CALCULÉ D'AVANCE.
--    Sinon : ARRÊT, rien n'est écrit.
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
{bloc("pose", "pose")}

-- 3. LES CONTRÔLES — tous doivent dire OK
{CONTROLES}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — pas de transaction sur un bien en estimation   24/10/2026
-- Il rend à {NOM} son texte d'avant ({AVANT[:8]}), par la MÊME ancre, et retire l'interrupteur.
-- Il ne touche aucune donnée. Pour seulement SUSPENDRE : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

{bloc("retour", "inverse")}

delete from public.app_setting where key = '{CLE}';

SELECT 1 AS "#", '{NOM} a retrouve {AVANT[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
"""


def test(num, libelle, condition, detail):
    return f"""    total := total + 1;
    IF {condition} THEN ok := ok + 1; r := r || ' | {num} OK {libelle}';
    ELSE r := r || ' | {num} ECHEC {libelle} : ' || coalesce({detail}, 'null'); END IF;"""


def essai(cible, statut):
    """Appelle la creation COMME L'ECRAN et rend dans `err` le message (ou '') ; le travail cree est retire.
    ⚠ La creation est OPTIMISTE : elle passe aussitot le bien « Sous offre » chez nous (mesure du 24/10).
      Sans remise en Estimation avant chaque appel, T2-T4 ne visaient plus une estimation -- 1re repetition
      a 4 sur 7, rattrapee ainsi."""
    remise = (f"    update public.app_dossier_current set statut_annonce = 'Estimation' where app_dossier_id = {cible};\n"
              if isinstance(cible, int) else "")
    return remise + f"""    err := '';
    BEGIN
      res := public.{NOM}({cible}, '{statut}', jsonb_build_object('amount', '100000', 'sale_price', '100000'), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;"""


ESTIM = 10000009      # annonce 63331, bien d'essai du 22/10, statut Estimation

repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — pas de transaction sur un bien en estimation    24/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni la fonction
--   modifiée, ni l'interrupteur, ni les travaux, ni les lignes du registre.
-- Le VRAI PATCH, puis la création appelée COMME L'ÉCRAN, au nom de Frédéric :
--   sur le bien d'essai {ESTIM} (annonce 63331, Estimation) et sur un bien ACTIF choisi par la répétition.
--   T1 ÉTEINT : offre sur l'Estimation → acceptée (le témoin inverse : le défaut)
--   T2 allumé : offre sur l'Estimation → REFUSÉE « transaction_sur_estimation »
--   T3 allumé : compromis → REFUSÉ   · T4 allumé : vente → REFUSÉE
--   T5 allumé : « Actif » sur l'Estimation → accepté (le chemin pour en sortir)
--   T6 allumé : offre sur un bien ACTIF → acceptée (rien d'autre ne change)
--   T7 l'inverse rend {AVANT[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    actif bigint;
    res jsonb;
    err text;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.app_dossier_current WHERE app_dossier_id = {ESTIM} AND statut_annonce = 'Estimation') THEN
        RAISE EXCEPTION '%', 'ARRET : le bien d''essai {ESTIM} n''est plus en Estimation -- la repetition ne prouverait rien.';
    END IF;
    SELECT d.app_dossier_id INTO actif FROM public.app_dossier_current d
     WHERE d.statut_annonce = 'Actif' AND btrim(coalesce(d.negociateur_email, '')) <> ''
       AND NOT EXISTS (SELECT 1 FROM public.app_console_job j
                        WHERE j.app_dossier_id = d.app_dossier_id AND j.status IN ('pending', 'running'))
     ORDER BY d.app_dossier_id LIMIT 1;
    IF actif IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : aucun bien Actif libre pour le temoin.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc("pose_rep", "pose").replace("DO $pose_rep$", "EXECUTE $exec_p$ DO $pose_rep$").replace("$pose_rep$;", "$pose_rep$ $exec_p$;")}

    -- T1 ETEINT
{essai(ESTIM, 'offer')}
{test('T1', 'eteint : une offre sur l estimation est acceptee', "err = ''", "err")}

    update public.app_setting set value = 'on' where key = '{CLE}';
    -- T2
{essai(ESTIM, 'offer')}
{test('T2', 'allume : offre sur l estimation refusee', "err like 'transaction_sur_estimation:%'", "nullif(err, '')")}
    -- T3
{essai(ESTIM, 'compromise')}
{test('T3', 'allume : compromis sur l estimation refuse', "err like 'transaction_sur_estimation:%'", "nullif(err, '')")}
    -- T4
{essai(ESTIM, 'sold')}
{test('T4', 'allume : vente sur l estimation refusee', "err like 'transaction_sur_estimation:%'", "nullif(err, '')")}
    -- T5
{essai(ESTIM, 'active')}
{test('T5', 'allume : passer l estimation en Actif reste accepte', "err = ''", "err")}
    -- T6
{essai('actif', 'offer')}
{test('T6', 'allume : une offre sur un bien Actif reste acceptee', "err = ''", "err || ' (bien ' || actif || ')'")}

    -- T7 L'INVERSE
    {bloc("retour_rep", "inverse").replace("DO $retour_rep$", "EXECUTE $exec_i$ DO $retour_rep$").replace("$retour_rep$;", "$retour_rep$ $exec_i$;")}
{test('T7', 'l inverse rend l empreinte d avant', f"md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}'", "'empreinte differente'")}

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
