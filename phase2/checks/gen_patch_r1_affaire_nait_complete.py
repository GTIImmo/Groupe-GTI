# Genere les 3 fichiers du patch R1 (la transaction nait complete) depuis LES MEMES ancres.
#     python -I phase2/checks/gen_patch_r1_affaire_nait_complete.py              -> la requete d'empreinte
#     python -I phase2/checks/gen_patch_r1_affaire_nait_complete.py <empreinte>  -> les 3 fichiers
# L'empreinte d'apres se CALCULE dans la base, en lecture seule, avec la requete que ce script imprime :
# le texte de la fonction n'est jamais recopie ici, seules les deux ancres le sont.
import pathlib, sys

OUT = pathlib.Path(__file__).resolve().parents[2] / "supabase"
AVANT = "3eec3f85ad9bcd5ed4b519e229936a23"
FN = "public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)"
BASE = "patch_r1_affaire_nait_complete_2026-10-22"
CLE = "affaire_nait_complete"

BLOC_R1 = r"""
    -- ─── R1 (22/10/2026, chantier 8) : LA TRANSACTION NAIT COMPLETE ───
    -- Avant, 4 champs sur 15 entraient au registre au clic (montant, date, acquereurs,
    -- mandat) ; les autres attendaient la nuit, ou ne vivaient qu'au carnet. Allume, chaque
    -- champ saisi entre dans SA colonne, et SEULEMENT pour le genre ou Hektor le porte
    -- (notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 4 D) :
    --   offre      validite, honoraires acquereur, taux
    --   compromis  date d'acte, sequestre, fin de retractation (date + jours), net vendeur,
    --              honoraires vendeur et acquereur, taux, les deux notaires, les mandants
    --   vente      net vendeur, honoraires vendeur et acquereur, taux, les deux notaires,
    --              les mandants
    -- ⚠ Les notaires vont dans notaire_acquereur_* / notaire_mandant_*, PAS dans notaire_id
    --   (colonne inerte depuis le 15/09), et SANS notaires_origine = 'saisie', qui figerait la
    --   ligne pour toujours : la console doit pouvoir la confirmer ou la corriger.
    -- ⚠ Les mandants SEULEMENT s'ils sont affirmes (un tableau) : sinon Hektor les deduit du
    --   mandat (regle du 16/09, decision de Frederic du 22/10).
    -- ⚠ Le carnet ne change pas. Une erreur ici ne fait JAMAIS echouer le geste (WARNING).
    -- Interrupteur eteint : RIEN NE CHANGE.
    v_nait_complete := coalesce((select s.value from public.app_setting s
                                  where s.key = 'affaire_nait_complete'), 'off') = 'on';
    if v_nait_complete then
      begin
        update public.app_affaire_ledger l set
          jours_validite        = case when v_kind = 'offre'
                                       then nullif(btrim(coalesce(v_payload->>'validity_days', '')), '')
                                       else l.jours_validite end,
          date_acte             = case when v_kind = 'compromis'
                                       then nullif(btrim(coalesce(v_payload->>'signature_date', '')), '')
                                       else l.date_acte end,
          sequestre             = case when v_kind = 'compromis'
                                       then nullif(btrim(coalesce(v_payload->>'sequestration', '')), '')
                                       else l.sequestre end,
          date_fin_retractation = case when v_kind = 'compromis'
                                        and coalesce(v_payload->>'transaction_date', '') ~ '^\d{4}-\d{2}-\d{2}'
                                        and btrim(coalesce(v_payload->>'retraction_days', '')) ~ '^\d{1,3}$'
                                       then to_char(left(v_payload->>'transaction_date', 10)::date
                                                    + btrim(v_payload->>'retraction_days')::int, 'YYYY-MM-DD')
                                       else l.date_fin_retractation end,
          prix_net_vendeur      = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'net_seller_price', '')), '')
                                       else l.prix_net_vendeur end,
          honoraires_entree     = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'seller_fees', '')), '')
                                       else l.honoraires_entree end,
          honoraires_sortie     = nullif(btrim(coalesce(v_payload->>'buyer_fees', '')), ''),
          taux_honoraires       = nullif(btrim(coalesce(v_payload->>'buyer_fees_rate', '')), ''),
          notaire_acquereur_id  = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '')
                                       else l.notaire_acquereur_id end,
          notaire_acquereur_nom = case when v_kind in ('compromis', 'vente')
                                        and nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '') is not null
                                       then nullif(btrim(coalesce(v_payload->>'buyer_notary_nom', '')), '')
                                       else l.notaire_acquereur_nom end,
          notaire_mandant_id    = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '')
                                       else l.notaire_mandant_id end,
          notaire_mandant_nom   = case when v_kind in ('compromis', 'vente')
                                        and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                       then nullif(btrim(coalesce(v_payload->>'seller_notary_nom', '')), '')
                                       else l.notaire_mandant_nom end,
          mandants_json         = case when v_kind in ('compromis', 'vente')
                                        and jsonb_typeof(v_payload->'mandant_contact_ids') = 'array'
                                        and jsonb_array_length(v_payload->'mandant_contact_ids') > 0
                                       then public.app_acquereurs_json(array(
                                              select nullif(btrim(e), '')
                                                from jsonb_array_elements_text(v_payload->'mandant_contact_ids') e
                                               where nullif(btrim(e), '') is not null))
                                       else l.mandants_json end
         where l.app_affaire_id = v_affaire_id;
      exception when others then
        raise warning 'R1 affaire_nait_complete : colonnes non posees pour l''affaire % (%)', v_affaire_id, sqlerrm;
      end;
    end if;"""

ANCRES = [
    ("  v_acq_json      jsonb;",
     "  v_acq_json      jsonb;\n  -- R1 22/10/2026 : interrupteur affaire_nait_complete\n  v_nait_complete boolean := false;"),
    ("    end loop;",
     "    end loop;\n" + BLOC_R1),
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
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu {AVANT[:8]} (22/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
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
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte du 22/10 ({AVANT[:8]}).';
        RETURN;
    END IF;
    IF md5(d) <> '{APRES}' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, ni {APRES[:8]} (posee) ni {AVANT[:8]} (d''avant). Rien n''est ecrit.', md5(d));
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
        'Chantier 8 / R1 22/10/2026 : on = une offre, un compromis ou une vente cree dans l''app pose TOUS ses champs saisis dans leurs colonnes du registre au clic, par genre (voir supabase/{BASE}.sql). off = comportement d''avant (4 champs au clic).',
        now())
on conflict (key) do nothing;"""

CONTROLES = f"""SELECT 1 AS "#", 'app_change_annonce_status_optimistic porte l''empreinte {APRES[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{APRES}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'l''interrupteur existe, ETEINT',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = '{CLE}' AND value = 'off') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'les droits d''appel sont inchanges (authenticated peut appeler)',
       CASE WHEN has_function_privilege('authenticated', '{FN}', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;"""

ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · R1 — LA TRANSACTION NAÎT COMPLÈTE AU CLIC                      22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md (R1, et § 4)
--
-- LE DÉFAUT (audit du 22/10). En créant une offre, un compromis ou une vente, la RPC ne
-- posait que 4 champs sur 15 dans le registre (montant, date, acquéreurs, mandat). Les
-- autres attendaient la nuit (si Hektor les avait pris), ou ne vivaient qu'au carnet.
--
-- CE QUE FAIT CE PATCH — CHIRURGICAL, DEUX ANCRES D'UNE LIGNE, ÉTEINT AU DÉPART :
--   1. un INTERRUPTEUR, app_setting '{CLE}', posé à 'off' ;
--   2. dans app_change_annonce_status_optimistic, juste après le carnet : allumé, chaque
--      champ saisi est écrit dans SA colonne, PAR GENRE (voir le commentaire du bloc).
--      Notaires dans notaire_acquereur_* / notaire_mandant_* SANS 'saisie' ; mandants
--      SEULEMENT s'ils sont affirmés. Une erreur ne fait jamais échouer le geste.
--   Rien d'autre ne change : le carnet, le travail pour Hektor, la chaîne, l'état.
--
-- ⚠ CE QUE CE PATCH NE FAIT PAS ENCORE (pièces suivantes) : la nuit réécrit toujours ces
--   colonnes depuis Hektor (R2) ; le notaire posé au clic est remis à vide entre le push du
--   registre (l. 912) et celui de la console (l. 1253) si la console ne l'a pas lu ; la
--   modification d'une transaction n'est pas touchée (point E).
--
-- ⛔ GARDE : la fonction n'est modifiée que si son empreinte est {AVANT[:8]} (relevée le
--    22/10), chaque ancre trouvée UNE fois, et le texte neuf porte l'empreinte {APRES[:8]}
--    CALCULÉE D'AVANCE. Sinon : ARRÊT, rien n'est écrit.
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

-- 2. LA FONCTION, PAR SES DEUX ANCRES
{bloc_pose("pose")}

-- 3. LES CONTRÔLES — tous doivent dire OK
{CONTROLES}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE R1 — la transaction naît complète                       22/10/2026
-- Il rend à app_change_annonce_status_optimistic son texte du 22/10 (empreinte {AVANT[:8]}),
-- par les MÊMES ancres, et retire l'interrupteur. Il ne touche aucune donnée : les colonnes
-- déjà posées au clic restent (la nuit les remplace par la valeur de Hektor, comme avant).
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

# ─── LA RÉPÉTITION : le vrai patch, puis la fonction appelée COMME L'ÉCRAN ───
CHARGE_COMMUNE = """'amount', '170000', 'sale_price', '180000', 'transaction_date', '2026-10-22',
        'buyer_contact_id', '20000008', 'buyer_fees', '5000', 'buyer_fees_rate', '3',
        'validity_days', '12', 'signature_date', '2027-01-15', 'sequestration', '9000',
        'retraction_days', '10', 'net_seller_price', '160000', 'seller_fees', '10000',
        'buyer_notary_id', '122190', 'buyer_notary_nom', 'Me. ESSAI ACQUEREUR',
        'seller_notary_id', '300465', 'seller_notary_nom', 'Me. ESSAI VENDEUR',
        'numero_mandat', '99999', 'titre_bien', 'ESSAI R1'"""


def appel(cible, extra=""):
    return (f"(public.app_change_annonce_status_optimistic(dossier, '{cible}', jsonb_build_object({CHARGE_COMMUNE}{extra}), 0)"
            f"->>'app_affaire_id')::bigint")


def test(num, libelle, condition, detail):
    return f"""    total := total + 1;
    IF {condition} THEN ok := ok + 1; r := r || ' | {num} OK {libelle}';
    ELSE r := r || ' | {num} ECHEC {libelle} : ' || coalesce({detail}, 'null'); END IF;"""


repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE R1 — la transaction naît complète                         22/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE : tout se passe dans UN bloc qui finit par une erreur
--   volontaire (« ESSAI ANNULE -- … ») ; le message porte le résultat. Rien ne reste :
--   ni la fonction modifiée, ni l'interrupteur, ni les transactions, ni les travaux.
--   (Seule la séquence des numéros avance de 6 : une séquence ne recule jamais.)
-- Elle joue LE VRAI PATCH (mêmes ancres), puis appelle la fonction COMME L'ÉCRAN, au nom
-- de Frédéric, sur l'annonce d'essai 63331 (dossier 10000009, « ESSAI 8A3 ») :
--   T1 ÉTEINT, compromis  → seuls les 4 champs d'avant (le témoin inverse) ;
--   T2 ALLUMÉ, offre      → validité, honoraires acquéreur, taux ; RIEN d'un compromis ;
--   T3 ALLUMÉ, compromis  → les 11 champs du compromis, fin de rétractation = date + 10,
--                           les deux notaires SANS 'saisie', PAS de mandants (non affirmés) ;
--   T4 ALLUMÉ, compromis, mandants AFFIRMÉS → mandants_json porte les deux ;
--   T5 ALLUMÉ, vente      → net, honoraires, notaires ; PAS d'acte, de séquestre, de fin ;
--   T6 le carnet reçoit le même nombre de lignes éteint et allumé ;
--   T7 une date impossible ne fait PAS échouer le geste ;
--   T8 l'inverse rend l'empreinte {AVANT[:8]}.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    dossier bigint := 10000009;
    aid bigint;
    n_eteint int;
    n_allume int;
    l public.app_affaire_ledger%rowtype;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (select 1 from public.app_dossier_current where app_dossier_id = dossier) THEN
        RAISE EXCEPTION '%', 'ARRET : le dossier d''essai 10000009 n''est plus dans le parc vivant -- la repetition ne prouverait rien.';
    END IF;
    IF sub IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : le compte admin de Frederic est introuvable.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    {INTERRUPTEUR.replace(chr(10), chr(10) + '    ')}
    {bloc_pose("pose_rep").replace("DO $pose_rep$", "EXECUTE $exec_pose$ DO $pose_rep$").replace("$pose_rep$;", "$pose_rep$ $exec_pose$;")}

    -- T1 ETEINT
    update public.app_setting set value = 'off' where key = '{CLE}';
    aid := {appel('compromise')};
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select count(*) into n_eteint from public.app_affaire_champ_app where app_affaire_id = aid;
{test('T1', 'eteint : date d acte, net, notaires restent VIDES', "l.date_acte is null and l.prix_net_vendeur is null and l.notaire_mandant_id is null and l.montant = '170000'", "row_to_json(l)::text")}

    -- T2 ALLUME, OFFRE
    update public.app_setting set value = 'on' where key = '{CLE}';
    aid := {appel('offer')};
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
{test('T2a', 'offre : validite 12, honoraires acquereur 5000, taux 3', "l.jours_validite = '12' and l.honoraires_sortie = '5000' and l.taux_honoraires = '3'", "row_to_json(l)::text")}
{test('T2b', 'offre : ni acte, ni sequestre, ni net, ni vendeur, ni notaire', "l.date_acte is null and l.sequestre is null and l.prix_net_vendeur is null and l.honoraires_entree is null and l.notaire_acquereur_id is null and l.notaire_mandant_id is null and l.date_fin_retractation is null", "row_to_json(l)::text")}

    -- T3 ALLUME, COMPROMIS, mandants NON affirmes
    aid := {appel('compromise')};
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select count(*) into n_allume from public.app_affaire_champ_app where app_affaire_id = aid;
{test('T3a', 'compromis : acte, sequestre, net, vendeur, acquereur, taux', "l.date_acte = '2027-01-15' and l.sequestre = '9000' and l.prix_net_vendeur = '160000' and l.honoraires_entree = '10000' and l.honoraires_sortie = '5000' and l.taux_honoraires = '3'", "row_to_json(l)::text")}
{test('T3b', 'compromis : fin de retractation = 2026-11-01 (date + 10)', "l.date_fin_retractation = '2026-11-01'", "l.date_fin_retractation")}
{test('T3c', 'compromis : les deux notaires avec leur nom, SANS saisie', "l.notaire_acquereur_id = '122190' and l.notaire_acquereur_nom = 'Me. ESSAI ACQUEREUR' and l.notaire_mandant_id = '300465' and l.notaire_mandant_nom = 'Me. ESSAI VENDEUR' and l.notaires_origine is null and l.notaire_id is null", "row_to_json(l)::text")}
{test('T3d', 'compromis : pas de validite, pas de mandants (non affirmes)', "l.jours_validite is null and l.mandants_json is null", "row_to_json(l)::text")}
{test('T6', 'le carnet recoit autant de lignes eteint et allume', "n_eteint = n_allume and n_allume > 0", "n_eteint || ' / ' || n_allume")}

    -- T4 ALLUME, COMPROMIS, mandants AFFIRMES
    aid := {appel('compromise', ", 'mandant_contact_ids', jsonb_build_array('20000009', '20000007')")};
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
{test('T4', 'compromis : les 2 mandants affirmes, dans l ordre', "jsonb_array_length(l.mandants_json) = 2 and l.mandants_json->0->>'id' = '20000009'", "l.mandants_json::text")}

    -- T5 ALLUME, VENTE
    aid := {appel('sold')};
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
{test('T5a', 'vente : net, vendeur, acquereur, notaires', "l.prix_net_vendeur = '160000' and l.honoraires_entree = '10000' and l.honoraires_sortie = '5000' and l.notaire_mandant_id = '300465'", "row_to_json(l)::text")}
{test('T5b', 'vente : ni acte, ni sequestre, ni fin, ni validite', "l.date_acte is null and l.sequestre is null and l.date_fin_retractation is null and l.jours_validite is null", "row_to_json(l)::text")}

    -- T7 UNE DATE IMPOSSIBLE NE FAIT PAS ECHOUER LE GESTE
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object({CHARGE_COMMUNE}) || jsonb_build_object('transaction_date', '2026-13-45'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
{test('T7', 'date impossible : le geste passe, la ligne existe', "l.app_affaire_id is not null", "aid::text")}

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
