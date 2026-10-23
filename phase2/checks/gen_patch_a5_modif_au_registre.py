# Genere les 3 fichiers du patch A5 (la MODIFICATION d'une transaction ecrit au registre ce qu'elle envoie).
#     python phase2/checks/gen_patch_a5_modif_au_registre.py              -> la requete d'empreinte (lecture seule)
#     python phase2/checks/gen_patch_a5_modif_au_registre.py <empreinte>  -> les 3 fichiers
# Meme patron que gen_patch_e_modif_champs_touches.py : l'empreinte d'apres se calcule dans la base.
import pathlib, sys

OUT = pathlib.Path(__file__).resolve().parents[2] / "supabase"
AVANT = "049643b8a2042904544586f400eb8fe3"     # app_modifier_affaire_optimistic apres E2, mesuree le 23/10
FN = "public.app_modifier_affaire_optimistic(bigint,jsonb,integer)"
BASE = "patch_a5_modif_au_registre_2026-10-23"
CLE = "affaire_modif_au_registre"

ANCRE_CARNET = "  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───"


def col(colonne, cle, genres=None, extra=""):
    """Une colonne : ecrite seulement si la cle a ete TAPEE (et le genre le permet). Vide ne gagne pas."""
    garde = f"v_touches ? '{cle}'"
    if genres:
        garde = f"a.kind in ({', '.join(repr(g) for g in genres)}) and " + garde
    return (f"        {colonne} = case when {garde}{extra}\n"
            f"                                     then coalesce(nullif(btrim(coalesce(v_payload->>'{cle}', '')), ''), l.{colonne})\n"
            f"                                     else l.{colonne} end,")


def notaire(cote, cle_id, cle_nom):
    garde = f"a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'{cote}') = 'true'"
    prefixe = "notaire_acquereur" if cote == "acquereur" else "notaire_mandant"
    return (f"        {prefixe}_id = case when {garde}\n"
            f"                                     then coalesce(nullif(btrim(coalesce(v_payload->>'{cle_id}', '')), ''), l.{prefixe}_id)\n"
            f"                                     else l.{prefixe}_id end,\n"
            f"        {prefixe}_nom = case when {garde}\n"
            f"                                      and nullif(btrim(coalesce(v_payload->>'{cle_id}', '')), '') is not null\n"
            f"                                     then nullif(btrim(coalesce(v_payload->>'{cle_nom}', '')), '')\n"
            f"                                     else l.{prefixe}_nom end,")


BLOC_A5 = "\n".join([
    "  -- ─── A5 (23/10/2026, chantier 8) : LA MODIFICATION ECRIT AU REGISTRE CE QU'ELLE ENVOIE ───",
    "  -- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 20.",
    "  -- R1 (22/10) l'avait promis « creation + modification » : la modification n'ecrivait que le",
    "  -- montant et la date. Interrupteur 'affaire_modif_au_registre', ET la liste du point E : seul",
    "  -- ce qui a ete TAPE ; les notaires s'ils sont AFFIRMES, les mandants s'ils sont DESIGNES --",
    "  -- exactement ce que le worker envoie comme intention. « Vide ne gagne pas ».",
    "  -- ⚠ ON N'ECRIT QUE CE QUE HEKTOR RELIT au retour, ou ce qu'aucun verdict ne juge sur le",
    "  --   registre : sinon l'ancien verdict (marquerLeCarnetRestant) comparerait la saisie A ELLE-MEME.",
    "  --   D'ou : PAS le net vendeur d'une VENTE (Hektor n'en a pas), PAS le numero de mandat (relu",
    "  --   la nuit seulement).",
    "  -- ⚠ La photo du carnet, plus bas, se prend dans `a`, lu AVANT : elle reste la valeur d'avant.",
    "  -- ⚠ Une erreur ici ne fait JAMAIS echouer le geste (WARNING), comme R1.",
    "  if v_touches is not null",
    "     and coalesce((select s.value from public.app_setting s",
    f"                    where s.key = '{CLE}'), 'off') = 'on' then",
    "    begin",
    "      update public.app_affaire_ledger l set",
    col("jours_validite", "validity_days", ["offre"]),
    col("date_acte", "signature_date", ["compromis"]),
    col("sequestre", "sequestration", ["compromis"]),
    col("prix_net_vendeur", "net_seller_price", ["compromis"]),
    col("honoraires_entree", "seller_fees", ["compromis", "vente"]),
    col("honoraires_sortie", "buyer_fees"),
    col("taux_honoraires", "buyer_fees_rate"),
    "        date_fin_retractation = case when a.kind = 'compromis' and v_touches ? 'retraction_days'",
    r"                                      and btrim(coalesce(v_payload->>'retraction_days', '')) ~ '^\d{1,3}$'",
    r"                                      and coalesce(l.date, '') ~ '^\d{4}-\d{2}-\d{2}'",
    "                                     then to_char(left(l.date, 10)::date",
    "                                                  + btrim(v_payload->>'retraction_days')::int, 'YYYY-MM-DD')",
    "                                     else l.date_fin_retractation end,",
    notaire("acquereur", "buyer_notary_id", "buyer_notary_nom"),
    notaire("mandant", "seller_notary_id", "seller_notary_nom"),
    "        mandants_json = case when a.kind in ('compromis', 'vente')",
    "                              and jsonb_typeof(v_payload->'mandant_contact_ids') = 'array'",
    "                              and jsonb_array_length(v_payload->'mandant_contact_ids') > 0",
    "                             then public.app_acquereurs_json(array(",
    "                                    select nullif(btrim(e), '')",
    "                                      from jsonb_array_elements_text(v_payload->'mandant_contact_ids') e",
    "                                     where nullif(btrim(e), '') is not null))",
    "                             else l.mandants_json end",
    "       where l.app_affaire_id = a.app_affaire_id;",
    "    exception when others then",
    "      raise warning 'A5 affaire_modif_au_registre : colonnes non posees pour l''affaire % (%)', a.app_affaire_id, sqlerrm;",
    "    end;",
    "  end if;",
    "",
    ANCRE_CARNET,
])

ANCRES = [(ANCRE_CARNET, BLOC_A5)]


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
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte {APRES[:8]}. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '{AVANT}' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu {AVANT[:8]} (mesuree le 23/10, apres E2). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
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
        RAISE NOTICE '%', 'Rien a retirer : app_modifier_affaire_optimistic porte deja l''empreinte d''avant ({AVANT[:8]}).';
        RETURN;
    END IF;
    IF md5(d) <> '{APRES}' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, ni {APRES[:8]} (posee) ni {AVANT[:8]} (avant). Rien n''est ecrit.', md5(d));
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
        'Chantier 8 / A5 23/10/2026 : on = en MODIFICATION d''une transaction, ce qui a ete TAPE (liste champs_touches du point E) est ecrit AUSSI au registre, colonne par colonne, au clic (voir supabase/{BASE}.sql). off, ou liste absente = comportement d''avant (montant et date seulement).',
        now())
on conflict (key) do nothing;"""

CONTROLES = f"""SELECT 1 AS "#", 'app_modifier_affaire_optimistic porte l''empreinte {APRES[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{APRES}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les droits d''appel sont inchanges (authenticated peut appeler)',
       CASE WHEN has_function_privilege('authenticated', '{FN}', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'la fonction reste SECURITY DEFINER',
       CASE WHEN (SELECT prosecdef FROM pg_proc WHERE oid = '{FN}'::regprocedure) THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'le point E est toujours allume (A5 en depend)',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_modif_champs_touches' AND value = 'on') THEN 'OK' ELSE '⚠ E ETEINT : A5 ne fera rien' END
ORDER BY 1;"""

ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · A5 — LA MODIFICATION D'UNE TRANSACTION ÉCRIT AU REGISTRE CE QU'ELLE ENVOIE   23/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (section 20)
--
-- LE DÉFAUT. app_modifier_affaire_optimistic n'écrit au registre que le montant et la date. Une
-- validité, une date d'acte, un séquestre, des honoraires, un taux, une rétractation, des notaires
-- ou des mandants modifiés n'existaient que dans le carnet jusqu'au retour de Hektor (ou la nuit).
-- R1 (22/10) l'avait promis « création + modification » ; seule la création l'était.
--
-- CE QUE FAIT CE PATCH — UNE ANCRE D'UNE LIGNE, ÉTEINT AU DÉPART :
--   allumé ET avec la liste `champs_touches` du point E : chaque colonne n'est écrite que si sa
--   clé a été TAPÉE ; les notaires seulement s'ils sont AFFIRMÉS, les mandants seulement s'ils
--   sont DÉSIGNÉS. « Vide ne gagne pas ». Éteint, ou liste absente : rien ne change.
--   ⚠ PAS le net vendeur d'une VENTE, PAS le numéro de mandat : Hektor ne les relit pas au retour,
--     et l'ancien verdict comparerait la saisie à elle-même.
--   ⚠ LA CHARGE DU TRAVAIL ET LE CARNET NE SONT PAS TOUCHÉS (la photo reste la valeur d'avant).
--
-- ⛔ GARDE : empreinte {AVANT[:8]} exigée (après E2, mesurée le 23/10), l'ancre trouvée UNE fois,
--    texte neuf {APRES[:8]} CALCULÉ D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
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

-- 2. LA FONCTION, PAR SON ANCRE
{bloc_pose("pose")}

-- 3. LES CONTRÔLES — tous doivent dire OK
{CONTROLES}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE A5 — la modification écrit au registre ce qu'elle envoie   23/10/2026
-- Il rend à app_modifier_affaire_optimistic son texte d'avant (empreinte {AVANT[:8]}), par la
-- MÊME ancre, et retire l'interrupteur. Il ne touche aucune donnée : les colonnes déjà écrites
-- restent (la nuit les relit chez Hektor comme toujours).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

{bloc_inverse()}

delete from public.app_setting where key = '{CLE}';

SELECT 1 AS "#", 'app_modifier_affaire_optimistic a retrouve l''empreinte {AVANT[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
"""

COLS = ["montant", "date", "jours_validite", "date_acte", "sequestre", "prix_net_vendeur", "honoraires_entree",
        "honoraires_sortie", "taux_honoraires", "date_fin_retractation", "notaire_acquereur_id", "notaire_acquereur_nom",
        "notaire_mandant_id", "notaire_mandant_nom", "mandants_json"]


def remise(var, aid):
    return (f"    update public.app_affaire_ledger set "
            + ", ".join(f"{c} = {var}.{c}" for c in COLS)
            + f" where app_affaire_id = {aid};")


def test(num, libelle, condition, detail):
    return f"""    total := total + 1;
    IF {condition} THEN ok := ok + 1; r := r || ' | {num} OK {libelle}';
    ELSE r := r || ' | {num} ECHEC {libelle} : ' || coalesce({detail}, 'null'); END IF;"""


def appel(aid, charge, touches):
    extra = "" if touches is None else f" || jsonb_build_object('champs_touches', '{touches}'::jsonb)"
    return f"    res := public.app_modifier_affaire_optimistic({aid}, ({charge}){extra}, 0);\n    select * into l from public.app_affaire_ledger where app_affaire_id = {aid};"


# Les charges : celles que la modale envoie (preremplie, ENTIERE), plus ce qu'on a tape.
OFFRE = ("jsonb_build_object('amount', '120000', 'sale_price', '128787', 'transaction_date', '2026-08-29', "
         "'validity_days', '17', 'retraction_days', '10', 'buyer_fees', '3000', 'buyer_fees_rate', '2.5', 'selected_mandat', '18836')")
COMPROMIS = ("jsonb_build_object('amount', '120000', 'sale_price', '115000', 'transaction_date', '2026-10-23', "
             "'signature_date', '2027-02-01', 'sequestration', '7000', 'net_seller_price', '106000', 'seller_fees', '9000', "
             "'buyer_fees', '4000', 'buyer_fees_rate', '3.33', 'retraction_days', '12', 'selected_mandat', '18787', "
             "'buyer_notary_id', '10064499', 'buyer_notary_nom', 'NOTAIRE ACQ ESSAI', "
             "'seller_notary_id', '10355906', 'seller_notary_nom', 'NOTAIRE VEND ESSAI', "
             "'notaires_affirmes', jsonb_build_object('acquereur', true, 'mandant', true), "
             "'mandant_contact_ids', jsonb_build_array('10354641'))")
TOUT_COMPROMIS = ('["signature_date", "sequestration", "net_seller_price", "seller_fees", "buyer_fees", '
                  '"buyer_fees_rate", "retraction_days", "buyer_notary_id"]')
VENTE = ("jsonb_build_object('amount', '120000', 'sale_price', '120000', 'transaction_date', '2026-10-23', "
         "'net_seller_price', '99999', 'seller_fees', '7777', 'selected_mandat', '18787')")

repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE A5 — la modification écrit au registre ce qu'elle envoie    23/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni la
--   fonction modifiée, ni l'interrupteur, ni le registre, ni le carnet, ni les travaux.
-- Le VRAI PATCH, puis la fonction appelée COMME L'ÉCRAN, au nom de Frédéric, sur trois
-- transactions d'essai : l'offre 33026 (1000001, bac à sable 62774), le compromis 50131 (1001379)
-- et la vente 23354 (1001380) de VA6482 (essai complet du 23/10).
--   T1 A5 ÉTEINT, validité tapée          → registre inchangé (le témoin inverse : le défaut)
--   T2 offre : validité, honoraires, taux  → les trois au registre
--   T3 liste vide                          → rien      · T4 SANS liste (écran d'avant) → rien
--   T5 compromis : tout tapé, notaires affirmés, mandant désigné → acte, séquestre, net, les deux
--      honoraires, taux, fin de rétractation = date + 12, les deux notaires et leurs noms, 1 mandant
--   T6 compromis : seule la date d'acte tapée → elle seule bouge (séquestre et net restent)
--   T7 compromis : notaire tapé mais NON affirmé → le notaire ne bouge pas
--   T8 vente : net vendeur ET commission tapés → la commission bouge, PAS le net vendeur
--   T9 séquestre tapé VIDE                 → « vide ne gagne pas »
--   T10 la photo du carnet reste la valeur d'AVANT · T11 l'inverse rend {AVANT[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    o_offre public.app_affaire_ledger%rowtype;
    o_comp  public.app_affaire_ledger%rowtype;
    o_vente public.app_affaire_ledger%rowtype;
    l public.app_affaire_ledger%rowtype;
    res jsonb;
    photo text;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    select * into o_offre from public.app_affaire_ledger where app_affaire_id = 1000001;
    select * into o_comp  from public.app_affaire_ledger where app_affaire_id = 1001379;
    select * into o_vente from public.app_affaire_ledger where app_affaire_id = 1001380;
    IF coalesce(o_offre.hektor_affaire_id, '') = '' OR coalesce(o_comp.hektor_affaire_id, '') = ''
       OR coalesce(o_vente.hektor_affaire_id, '') = '' OR o_offre.present_in_hektor IS FALSE
       OR o_comp.present_in_hektor IS FALSE OR o_vente.present_in_hektor IS FALSE THEN
        RAISE EXCEPTION '%', 'ARRET : une transaction d''essai n''est plus modifiable (numero Hektor ou presence) -- la repetition ne prouverait rien.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_modif_champs_touches' AND value = 'on') THEN
        RAISE EXCEPTION '%', 'ARRET : le point E est eteint -- A5 en depend, la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc_pose("pose_rep").replace("DO $pose_rep$", "EXECUTE $exec_pose$ DO $pose_rep$").replace("$pose_rep$;", "$pose_rep$ $exec_pose$;")}

    -- T1 ETEINT
    update public.app_setting set value = 'off' where key = '{CLE}';
{appel(1000001, OFFRE, '["validity_days"]')}
{test('T1', 'eteint : registre inchange', "l.jours_validite is not distinct from o_offre.jours_validite", "l.jours_validite")}
{remise('o_offre', 1000001)}

    update public.app_setting set value = 'on' where key = '{CLE}';
    -- T2 OFFRE
{appel(1000001, OFFRE, '["validity_days", "buyer_fees", "buyer_fees_rate"]')}
{test('T2', 'offre : validite, honoraires, taux', "l.jours_validite = '17' and l.honoraires_sortie = '3000' and l.taux_honoraires = '2.5'", "concat_ws(' / ', l.jours_validite, l.honoraires_sortie, l.taux_honoraires)")}
{remise('o_offre', 1000001)}
    -- T3 LISTE VIDE
{appel(1000001, OFFRE, '[]')}
{test('T3', 'liste vide : rien', "l.jours_validite is not distinct from o_offre.jours_validite and l.honoraires_sortie is not distinct from o_offre.honoraires_sortie", "concat_ws(' / ', l.jours_validite, l.honoraires_sortie)")}
{remise('o_offre', 1000001)}
    -- T4 SANS LISTE
{appel(1000001, OFFRE, None)}
{test('T4', 'sans liste : rien', "l.jours_validite is not distinct from o_offre.jours_validite and l.taux_honoraires is not distinct from o_offre.taux_honoraires", "concat_ws(' / ', l.jours_validite, l.taux_honoraires)")}
{remise('o_offre', 1000001)}

    -- T5 COMPROMIS, TOUT
    delete from public.app_affaire_champ_app where app_affaire_id = 1001379 and champ = 'date_acte';
{appel(1001379, COMPROMIS, TOUT_COMPROMIS)}
{test('T5', 'compromis : tout tape', "l.date_acte = '2027-02-01' and l.sequestre = '7000' and l.prix_net_vendeur = '106000' and l.honoraires_entree = '9000' and l.honoraires_sortie = '4000' and l.taux_honoraires = '3.33' and l.date_fin_retractation = '2026-11-04' and l.notaire_acquereur_id = '10064499' and l.notaire_acquereur_nom = 'NOTAIRE ACQ ESSAI' and l.notaire_mandant_id = '10355906' and l.notaire_mandant_nom = 'NOTAIRE VEND ESSAI' and jsonb_array_length(l.mandants_json) = 1", "concat_ws(' / ', l.date_acte, l.sequestre, l.prix_net_vendeur, l.honoraires_entree, l.honoraires_sortie, l.taux_honoraires, l.date_fin_retractation, l.notaire_acquereur_nom, l.notaire_mandant_nom, l.mandants_json::text)")}
    -- T10 LA PHOTO
    select valeur_hektor_au_moment into photo from public.app_affaire_champ_app where app_affaire_id = 1001379 and champ = 'date_acte';
{test('T10', 'la photo du carnet reste la valeur d avant', "photo is not distinct from o_comp.date_acte", "photo")}
{remise('o_comp', 1001379)}
    -- T6 SEULE LA DATE D'ACTE
{appel(1001379, COMPROMIS, '["signature_date"]')}
{test('T6', 'compromis : la date d acte seule', "l.date_acte = '2027-02-01' and l.sequestre is not distinct from o_comp.sequestre and l.prix_net_vendeur is not distinct from o_comp.prix_net_vendeur", "concat_ws(' / ', l.date_acte, l.sequestre, l.prix_net_vendeur)")}
{remise('o_comp', 1001379)}
    -- T7 NOTAIRE NON AFFIRME
{appel(1001379, COMPROMIS + " - 'notaires_affirmes' || jsonb_build_object('buyer_notary_id', '999999')", '["buyer_notary_id"]')}
{test('T7', 'compromis : notaire non affirme, inchange', "l.notaire_acquereur_id is not distinct from o_comp.notaire_acquereur_id", "l.notaire_acquereur_id")}
{remise('o_comp', 1001379)}
    -- T9 VIDE NE GAGNE PAS
{appel(1001379, COMPROMIS + " || jsonb_build_object('sequestration', '')", '["sequestration"]')}
{test('T9', 'sequestre vide : inchange', "l.sequestre is not distinct from o_comp.sequestre", "l.sequestre")}
{remise('o_comp', 1001379)}

    -- T8 VENTE
{appel(1001380, VENTE, '["net_seller_price", "seller_fees"]')}
{test('T8', 'vente : la commission oui, le net vendeur NON', "l.honoraires_entree = '7777' and l.prix_net_vendeur is not distinct from o_vente.prix_net_vendeur", "concat_ws(' / ', l.honoraires_entree, l.prix_net_vendeur)")}
{remise('o_vente', 1001380)}

    -- T11 L'INVERSE
    {bloc_inverse().replace("DO $retour$", "EXECUTE $exec_inv$ DO $retour$").replace("$retour$;", "$retour$ $exec_inv$;")}
{test('T11', 'l inverse rend ' + AVANT[:8], f"md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}'", "'empreinte differente'")}

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
