# Genere les 3 fichiers du patch E (la modification n'inscrit au carnet que ce qui a ete TAPE).
#     python -I phase2/checks/gen_patch_e_modif_champs_touches.py              -> la requete d'empreinte
#     python -I phase2/checks/gen_patch_e_modif_champs_touches.py <empreinte>  -> les 3 fichiers
# Meme patron que gen_patch_1b_affaire_acquereur_numero_hektor.py : l'empreinte d'apres se calcule dans la base.
import pathlib, sys

OUT = pathlib.Path(__file__).resolve().parents[2] / "supabase"
AVANT = "a5297281686c699b89ac2fbc61864fe4"     # app_modifier_affaire_optimistic, mesuree le 23/10
FN = "public.app_modifier_affaire_optimistic(bigint,jsonb,integer)"
BASE = "patch_e_modif_champs_touches_2026-10-23"
CLE = "affaire_modif_champs_touches"

BLOC_TOUCHES = """  v_payload := coalesce(job_payload, '{}'::jsonb);

  -- ─── POINT E (23/10/2026, chantier 8) : CE QUI A ETE TAPE, PAS CE QUI ETAIT AFFICHE ───
  -- La modale s'ouvre PREREMPLIE et la charge part ENTIERE (le worker de l'offre reconstruit
  -- le formulaire de Hektor avec elle : on ne l'allege pas). Mais tout champ non vide entrait
  -- au carnet -- et le carnet PRIME a l'ecran. Mesure : offre 33094 (13/10), 6 lignes dont au
  -- moins 4 de prerempli (prix de l'annonce 180 000, 10 jours de retractation sur une offre).
  -- L'ecran envoie desormais `champs_touches` : les cles qu'une SAISIE a changees.
  -- Allume ET liste presente : seules ces cles vont au carnet et au registre (montant, date).
  -- Liste absente (ecran d'avant, en cache) ou eteint : comportement d'avant.
  -- ⚠ Le montant se juge sur la PAIRE amount / sale_price : l'une touchee, on garde les deux
  --   comme avant (coalesce(amount, sale_price)) -- sinon un prix de vente touche seul
  --   deviendrait le montant d'un compromis.
  if coalesce((select s.value from public.app_setting s
                where s.key = 'affaire_modif_champs_touches'), 'off') = 'on'
     and jsonb_typeof(v_payload->'champs_touches') = 'array' then
    v_touches := v_payload->'champs_touches';
  end if;
  v_maj := v_payload;
  if v_touches is not null then
    if not (v_touches ?| array['amount', 'sale_price']) then
      v_maj := v_maj - array['amount', 'sale_price'];
    end if;
    if not (v_touches ? 'transaction_date') then
      v_maj := v_maj - 'transaction_date';
    end if;
  end if;"""

CONDITION = """    if v_valeur is not null
       -- point E : allume avec une liste, seul ce qui a ete TAPE entre au carnet
       and (v_touches is null or v_touches ?| (case v_champ.champ
             when 'montant'            then array['amount', 'sale_price']
             when 'date'               then array['transaction_date']
             when 'date_acte'          then array['signature_date']
             when 'sequestre'          then array['sequestration']
             when 'prix_net_vendeur'   then array['net_seller_price']
             when 'prix_publique'      then array['sale_price']
             when 'honoraires'         then array['buyer_fees']
             when 'honoraires_entree'  then array['seller_fees']
             when 'numero_mandat'      then array['selected_mandat']
             when 'jours_validite'     then array['validity_days']
             when 'jours_retractation' then array['retraction_days']
             when 'notaire_id'         then array['buyer_notary_id']
             when 'taux_honoraires'    then array['buyer_fees_rate']
             else array['--champ-inconnu--'] end)) then"""

ANCRES = [
    ("  v_cible     text;",
     "  v_cible     text;\n  v_touches   jsonb;   -- point E 23/10/2026 (interrupteur affaire_modif_champs_touches)\n  v_maj       jsonb;"),
    ("  v_payload := coalesce(job_payload, '{}'::jsonb);", BLOC_TOUCHES),
    ("     set montant = coalesce(nullif(btrim(coalesce(v_payload->>'amount',",
     "     set montant = coalesce(nullif(btrim(coalesce(v_maj->>'amount',"),
    ("                                                  v_payload->>'sale_price', '')), ''), montant),",
     "                                                  v_maj->>'sale_price', '')), ''), montant),"),
    ("         date    = coalesce(nullif(btrim(coalesce(v_payload->>'transaction_date', '')), ''), date)",
     "         date    = coalesce(nullif(btrim(coalesce(v_maj->>'transaction_date', '')), ''), date)"),
    ("    if v_valeur is not null then", CONDITION),
    ("                            'champs_au_carnet', v_au_carnet);",
     "                            'champs_au_carnet', v_au_carnet,\n                            'champs_touches',   v_touches);"),
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
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte {APRES[:8]}. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '{AVANT}' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu {AVANT[:8]} (mesuree le 23/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
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
        'Chantier 8 / point E 23/10/2026 : on = en MODIFICATION d''une transaction, seuls les champs que l''ecran declare TAPES (champs_touches) entrent au carnet et au registre ; le prerempli n''y entre plus (voir supabase/{BASE}.sql). off, ou liste absente = comportement d''avant.',
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
ORDER BY 1;"""

ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · POINT E — LA MODIFICATION N'INSCRIT AU CARNET QUE CE QUI A ÉTÉ TAPÉ   23/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (section 7)
--
-- LE DÉFAUT. app_modifier_affaire_optimistic met au carnet TOUT champ non vide de la charge.
-- Or la modale s'ouvre préremplie, et la charge part entière. Le carnet PRIME à l'écran et au
-- préremplissage suivant : du prérempli que personne n'a tapé y devenait « notre saisie ».
-- Mesure : offre 33094 (13/10), 6 lignes au carnet dont au moins 4 de prérempli.
--
-- CE QUE FAIT CE PATCH — SEPT ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   allumé, et si l'écran envoie `champs_touches` (les clés qu'une saisie a changées), seules
--   ces clés entrent au carnet ET au registre (montant, date). Liste absente (écran d'avant) ou
--   éteint : comportement d'avant. ⚠ LA CHARGE DU TRAVAIL N'EST PAS TOUCHÉE : le worker reçoit
--   exactement ce qu'il recevait (il ignore `champs_touches`).
--
-- ⛔ GARDE : empreinte {AVANT[:8]} exigée (mesurée le 23/10), chaque ancre trouvée UNE fois,
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

-- 2. LA FONCTION, PAR SES SEPT ANCRES
{bloc_pose("pose")}

-- 3. LES CONTRÔLES — tous doivent dire OK
{CONTROLES}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DU POINT E — la modification n'inscrit que ce qui a été tapé   23/10/2026
-- Il rend à app_modifier_affaire_optimistic son texte d'avant (empreinte {AVANT[:8]}), par les
-- MÊMES ancres, et retire l'interrupteur. Il ne touche aucune donnée.
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

# La charge d'essai : ce que la modale envoie en modifiant l'offre d'essai 33026 (bac a sable
# 62774) -- prerempli compris, comme l'ecran.
CHARGE = ("'amount', '151234', 'sale_price', '180000', 'transaction_date', '2026-08-31', "
          "'validity_days', '10', 'retraction_days', '10', 'selected_mandat', '18836'")


def appel(liste):
    extra = "" if liste is None else f", 'champs_touches', '{liste}'::jsonb"
    return (f"public.app_modifier_affaire_optimistic(aid, jsonb_build_object({CHARGE}{extra}), 0)")


def test(num, libelle, condition, detail):
    return f"""    total := total + 1;
    IF {condition} THEN ok := ok + 1; r := r || ' | {num} OK {libelle}';
    ELSE r := r || ' | {num} ECHEC {libelle} : ' || coalesce({detail}, 'null'); END IF;"""


def cas(num, libelle, liste, champs_attendus, montant_change, date_change):
    attendu = "array[" + ", ".join(f"'{c}'" for c in sorted(champs_attendus)) + "]::text[]" if champs_attendus else "array[]::text[]"
    m = "l.montant::numeric = 151234" if montant_change else "l.montant = orig.montant"
    dd = "l.date::date = date '2026-08-31'" if date_change else "l.date = orig.date"
    return f"""    delete from public.app_affaire_champ_app where app_affaire_id = aid;
    update public.app_affaire_ledger set montant = orig.montant, date = orig.date where app_affaire_id = aid;
    res := {appel(liste)};
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select coalesce(array_agg(champ order by champ), array[]::text[]) into vus from public.app_affaire_champ_app where app_affaire_id = aid;
{test(num, libelle, f"vus = {attendu} and {m} and {dd} and (res->>'ok')::boolean", "array_to_string(vus, ',') || ' / montant ' || coalesce(l.montant::text, 'null') || ' / date ' || coalesce(l.date::text, 'null')")}"""


TOUS = ["date", "jours_retractation", "jours_validite", "montant", "numero_mandat", "prix_publique"]

repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DU POINT E — la modification n'inscrit que ce qui a été tapé    23/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni la
--   fonction modifiée, ni l'interrupteur, ni le carnet, ni le registre, ni les travaux.
-- Le VRAI PATCH, puis la fonction appelée COMME L'ÉCRAN, au nom de Frédéric, sur l'offre
-- d'essai 33026 (app_affaire_id 1000001, bac à sable 62774), avec une charge PRÉREMPLIE :
--   T1 ÉTEINT, liste ['amount']           → les 6 champs au carnet (le témoin inverse : le défaut)
--   T2 ALLUMÉ, liste ['amount']           → le montant SEUL au carnet, montant changé, date non
--   T3 ALLUMÉ, liste vide                 → rien au carnet, registre inchangé
--   T4 ALLUMÉ, SANS liste (écran d'avant) → les 6 champs, comme avant
--   T5 ALLUMÉ, date + validité            → ces deux-là seuls, date changée, montant non
--   T6 ALLUMÉ, prix de vente seul         → montant ET prix public (la paire), montant changé
--   T7 le retour porte `champs_touches` · T8 l'inverse rend {AVANT[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    aid bigint := 1000001;
    orig public.app_affaire_ledger%rowtype;
    l public.app_affaire_ledger%rowtype;
    res jsonb;
    vus text[];
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    select * into orig from public.app_affaire_ledger where app_affaire_id = aid;
    IF orig.app_affaire_id IS NULL OR coalesce(orig.hektor_affaire_id, '') = '' OR orig.present_in_hektor IS NOT TRUE THEN
        RAISE EXCEPTION '%', 'ARRET : l''offre d''essai 1000001 n''est plus modifiable (numero Hektor ou presence) -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc_pose("pose_rep").replace("DO $pose_rep$", "EXECUTE $exec_pose$ DO $pose_rep$").replace("$pose_rep$;", "$pose_rep$ $exec_pose$;")}

    update public.app_setting set value = 'off' where key = '{CLE}';
{cas('T1', 'eteint : les 6 champs, le defaut d avant', '["amount"]', TOUS, True, True)}

    update public.app_setting set value = 'on' where key = '{CLE}';
{cas('T2', 'allume, montant seul', '["amount"]', ["montant"], True, False)}
{cas('T3', 'allume, liste vide : rien', '[]', [], False, False)}
{cas('T4', 'allume, sans liste : comme avant', None, TOUS, True, True)}
{cas('T5', 'allume, date et validite seules', '["transaction_date", "validity_days"]', ["date", "jours_validite"], False, True)}
{cas('T6', 'allume, prix de vente seul : la paire', '["sale_price"]', ["montant", "prix_publique"], True, False)}
{test('T7', 'le retour porte champs_touches', "res->'champs_touches' = '[\"sale_price\"]'::jsonb", "res::text")}

    -- T8 L'INVERSE
    {bloc_inverse().replace("DO $retour$", "EXECUTE $exec_inv$ DO $retour$").replace("$retour$;", "$retour$ $exec_inv$;")}
{test('T8', 'l inverse rend ' + AVANT[:8], f"md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}'", "'empreinte differente'")}

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
