# Genere les 3 fichiers du patch « les personnes d'une transaction portent nos deux numeros » (piece 1).
#     python phase2/checks/gen_patch_personnes_deux_numeros.py          -> la requete d'empreinte (lecture seule)
#     python phase2/checks/gen_patch_personnes_deux_numeros.py <apres>  -> les 3 fichiers
# Meme patron que gen_patch_transaction_sur_estimation.py.
# Note : notice/ETUDE_NUMEROS_PERSONNES_REGISTRE_TRANSACTIONS_2026-10-24.md, sections 8 a 10.
import pathlib, sys

OUT = pathlib.Path(__file__).resolve().parents[2] / "supabase"
BASE = "patch_personnes_deux_numeros_2026-10-24"
CLE = "affaire_personnes_deux_numeros"

FN = "public.app_acquereurs_json(text[])"
NOM = "app_acquereurs_json"
AVANT = "1b82fddad4387a5965b6cf16c49a9b1a"      # mesuree le 24/10

# L'ancre : le corps entier de la fonction (SQL, une seule requete).
ANC = """  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        c.hektor_contact_id,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      )
      order by array_position(p_ids, c.hektor_contact_id)
    ),
    '[]'::jsonb)
  from app_contact_current c
  where c.hektor_contact_id = any(p_ids);"""

NEUF = """  -- ⑧ (24/10/2026) : LES PERSONNES D'UNE TRANSACTION PORTENT NOS DEUX NUMEROS.
  -- Regle de Frederic : « l'id Hektor pour communiquer avec Hektor, mon id app pour le registre ».
  -- AVANT : on ne trouvait une personne que par NOTRE identite (`hektor_contact_id`, nom trompeur depuis
  --   la bascule du 23/09) ; passee sous son numero de Hektor -- ce que la modale preremplit depuis le
  --   registre -- elle DISPARAISSAIT de la liste, en silence (mesure : ['605976'] -> 0 personne).
  -- ALLUME : on la trouve par ses DEUX numeros ; `id` porte le numero de HEKTOR, comme la relecture du
  --   worker et la nuit le rangent deja (une seule signification pour `id`, du clic au lendemain) ;
  --   `app_contact_id` porte le NOTRE. Une meme personne donnee deux fois ne sort qu'une fois.
  --   Inconnue : rien (on n'invente pas). Sans numero de Hektor encore : `id` garde notre identite.
  -- Sert a la creation (acquereurs, principal en tete) et a la modification (mandants).
  -- Interrupteur 'affaire_personnes_deux_numeros'. Etude : ETUDE_NUMEROS_PERSONNES_..._2026-10-24.md.
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        case when s.allume
                          then coalesce(nullif(btrim(c.hektor_target_id), ''), c.hektor_contact_id)
                          else c.hektor_contact_id end,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      ) || case when s.allume then jsonb_build_object('app_contact_id', c.app_contact_id) else '{}'::jsonb end
      order by coalesce(array_position(p_ids, c.hektor_contact_id),
                        case when s.allume then array_position(p_ids, c.hektor_target_id) end)
    ),
    '[]'::jsonb)
  from app_contact_current c
  cross join (select coalesce((select v.value from public.app_setting v
                                where v.key = 'affaire_personnes_deux_numeros'), 'off') = 'on' as allume) s
  where c.hektor_contact_id = any(p_ids)
     or (s.allume and c.hektor_target_id = any(p_ids));"""


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
        'Chantier 8 / 24/10/2026 : on = les personnes d''une transaction (acquereurs a la creation, mandants a la modification) sont trouvees par leurs DEUX numeros et portent les deux : id = numero de Hektor, app_contact_id = le notre. off = comportement d''avant (une personne passee sous son numero de Hektor disparaissait). Voir supabase/{BASE}.sql.',
        now())
on conflict (key) do nothing;"""

CONTROLES = f"""SELECT 1 AS "#", '{NOM} porte l''empreinte {APRES[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{APRES}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, '{NOM} : toujours SECURITY DEFINER, toujours fermee a authenticated',
       CASE WHEN (SELECT prosecdef FROM pg_proc WHERE oid = '{FN}'::regprocedure) AND NOT has_function_privilege('authenticated', '{FN}', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'eteint : le comportement d''avant (605976 introuvable, 20000015 trouve sans app_contact_id)',
       CASE WHEN jsonb_array_length({FN.split('(')[0]}(array['605976'])) = 0
             AND NOT (({FN.split('(')[0]}(array['20000015'])->0) ? 'app_contact_id') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;"""

ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ — LES PERSONNES D'UNE TRANSACTION PORTENT NOS DEUX NUMÉROS (pièce 1)   24/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Étude : notice/ETUDE_NUMEROS_PERSONNES_REGISTRE_TRANSACTIONS_2026-10-24.md (§8 à §10). Règle de Frédéric :
-- « l'id Hektor pour communiquer avec Hektor, et mon id app pour le registre ».
--
-- LE DÉFAUT (mesuré le 24/10). {NOM} fabrique la liste des personnes d'une transaction : les acquéreurs à la
-- CRÉATION (le principal en tête), les mandants à la MODIFICATION. Il ne trouvait une personne que par NOTRE
-- identité ; passée sous son numéro de Hektor — ce que la modale préremplit depuis le registre — elle
-- DISPARAISSAIT de la liste, sans un mot (['605976'] → 0 personne ; ['20000015'] → 1). Et `id` changeait de sens
-- dans la journée : notre identité au clic, le numéro de Hektor quelques minutes après (relecture du worker), puis
-- la nuit.
--
-- CE QUE FAIT CE PATCH — UNE ANCRE (le corps de la fonction), ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting '{CLE}', posé à 'off' ;
--   2. allumé : la personne est trouvée par ses DEUX numéros ; `id` = numéro de HEKTOR (comme la relecture et la
--      nuit) ; `app_contact_id` = le NÔTRE ; une même personne donnée deux fois ne sort qu'une fois ; inconnue :
--      rien. Éteint : exactement le texte d'avant.
--   Rien d'autre ne change : le principal (`hektor_acquereur_id` / `app_contact_id`, 1b), le chaînage, le worker.
--
-- ⛔ GARDE : empreinte {AVANT[:8]} exigée, ancre trouvée UNE fois, texte neuf {APRES[:8]} CALCULÉ D'AVANCE.
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

-- 2. LA FONCTION
{bloc("pose", "pose")}

-- 3. LES CONTRÔLES — tous doivent dire OK
{CONTROLES}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — les personnes d'une transaction portent nos deux numéros   24/10/2026
-- Il rend à {NOM} son texte d'avant ({AVANT[:8]}), par la MÊME ancre, et retire l'interrupteur.
-- Il ne touche aucune donnée : les listes déjà écrites gardent leur `app_contact_id` (une clé de plus, que
-- personne ne lit encore). Pour seulement SUSPENDRE : éteindre l'interrupteur.
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


F = "public.app_acquereurs_json"
ESTIM = 10000009      # annonce 63331, bien d'essai (Estimation, la creation y passe tant que l'autre patch n'est pas pose)

repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — les personnes d'une transaction portent nos deux numéros    24/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste.
-- Personnes d'essai : l'acquéreur de l'essai 5 (nous 20000015 / Hektor 605976) et les deux notaires
-- (10355906 / 605227, 10064499 / 122190), pris comme simples contacts.
--   T1 ÉTEINT : 605976 introuvable (le défaut), 20000015 trouvé, id = 20000015, sans app_contact_id
--   T2 allumé : 605976 trouvé, id = 605976, app_contact_id = 20000015
--   T3 allumé : 20000015 trouvé, id = 605976 (le numéro de Hektor), app_contact_id = 20000015
--   T4 allumé : la même personne donnée sous ses deux numéros ne sort qu'une fois
--   T5 allumé : l'ordre demandé est gardé, quel que soit le numéro (605227 puis 10064499)
--   T6 allumé : un numéro inconnu ne fabrique personne
--   T7 allumé : LA CRÉATION, appelée comme l'écran sur le bien d'essai {ESTIM}, avec l'acquéreur sous son numéro
--      de Hektor : la ligne du registre porte l'acquéreur (id 605976, app_contact_id 20000015) — avant, rien
--   T8 l'inverse rend {AVANT[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    res jsonb;
    j jsonb;
    lig record;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.app_contact_current WHERE hektor_contact_id = '20000015' AND hektor_target_id = '605976') THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai 20000015 / 605976 a change -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc("pose_rep", "pose").replace("DO $pose_rep$", "EXECUTE $exec_p$ DO $pose_rep$").replace("$pose_rep$;", "$pose_rep$ $exec_p$;")}

    -- T1 ETEINT
    j := {F}(array['20000015']);
{test('T1', 'eteint : comportement d avant', f"jsonb_array_length({F}(array['605976'])) = 0 and j->0->>'id' = '20000015' and not (j->0 ? 'app_contact_id')", "j::text")}

    update public.app_setting set value = 'on' where key = '{CLE}';
    -- T2
    j := {F}(array['605976']);
{test('T2', 'allume : trouve par le numero de Hektor', "jsonb_array_length(j) = 1 and j->0->>'id' = '605976' and j->0->>'app_contact_id' = '20000015'", "j::text")}
    -- T3
    j := {F}(array['20000015']);
{test('T3', 'allume : trouve par notre numero, id = Hektor', "jsonb_array_length(j) = 1 and j->0->>'id' = '605976' and j->0->>'app_contact_id' = '20000015'", "j::text")}
    -- T4
    j := {F}(array['20000015', '605976']);
{test('T4', 'allume : une personne sous ses deux numeros sort une fois', "jsonb_array_length(j) = 1", "j::text")}
    -- T5
    j := {F}(array['605227', '10064499']);
{test('T5', 'allume : l ordre demande est garde', "jsonb_array_length(j) = 2 and j->0->>'app_contact_id' = '10355906' and j->1->>'app_contact_id' = '10064499'", "j::text")}
    -- T6
    j := {F}(array['999999999']);
{test('T6', 'allume : un inconnu ne fabrique personne', "jsonb_array_length(j) = 0", "j::text")}
    -- T7 LA CREATION, comme l'ecran
    res := public.app_change_annonce_status_optimistic({ESTIM}, 'offer',
             jsonb_build_object('amount', '100000', 'buyer_contact_id', '605976', 'buyer_contact_ids', jsonb_build_array('605976')), 9);
    delete from public.app_console_job where id::text = res->>'job_id';
    SELECT acquereur_json::jsonb AS a1, acquereurs_json::jsonb AS al, app_contact_id, hektor_acquereur_id INTO lig
      FROM public.app_affaire_ledger WHERE app_dossier_id = {ESTIM} ORDER BY app_affaire_id DESC LIMIT 1;
{test('T7', 'la creation range l acquereur passe sous son numero de Hektor', "lig.a1->>'id' = '605976' and lig.a1->>'app_contact_id' = '20000015' and jsonb_array_length(lig.al) = 1 and lig.app_contact_id = 20000015 and lig.hektor_acquereur_id = '605976'", "coalesce(lig.a1::text, 'acquereur_json vide') || ' / ' || coalesce(lig.al::text, '-')")}

    -- T8 L'INVERSE
    {bloc("retour_rep", "inverse").replace("DO $retour_rep$", "EXECUTE $exec_i$ DO $retour_rep$").replace("$retour_rep$;", "$retour_rep$ $exec_i$;")}
{test('T8', 'l inverse rend l empreinte d avant', f"md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}'", "'empreinte differente'")}

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
