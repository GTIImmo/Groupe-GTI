# Genere les 3 fichiers du patch 8a-B2 (le controle au retour s'etend a la CREATION de contact)
# depuis LES MEMES ancres, posees sur le texte EXACT de la fonction en production (b64 a cote).
#     python -I phase2/checks/gen_patch_8a6_contact_creation_controle.py
import base64, hashlib, pathlib

ICI = pathlib.Path(__file__).resolve().parent
OUT = ICI.parents[1] / "supabase"
BASE = "patch_8a6_contact_creation_controle_2026-10-22"
FN = "public.app_contact_saisie_modif_job_trg()"
md5 = lambda t: hashlib.md5(t.encode("utf-8")).hexdigest()

AVANT_TXT = base64.b64decode(ICI.joinpath("b64_8a6_job_trg_avant.txt").read_text()).decode("utf-8")
AVANT = md5(AVANT_TXT)
assert AVANT == "4af27d6a8dd2aa1153c1b1426db6a563", AVANT

# Les ancres : UNE SEULE LIGNE chacune (lecon 30), chacune presente UNE fois.
ANCRES = [
    ("    if coalesce(new.result_json->>'status', '') <> 'updated' then return null; end if;  -- held_conflict, etc.",
     "    -- 8a-B2 (22/10) : la CREATION aussi -- created (contact), created_and_linked (mandant).\n"
     "    if coalesce(new.result_json->>'status', '') not in ('updated', 'created', 'created_and_linked') then return null; end if;  -- held_conflict, etc."),
    ("    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', '')), '');",
     "    -- a la creation, notre numero est dans la charge (app_identite), celui de Hektor dans le resultat\n"
     "    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', new.payload_json->>'app_identite', new.result_json->>'hektor_contact_id', '')), '');"),
    ("     where c.hektor_contact_id = ident or c.hektor_target_id = ident",
     "     where c.hektor_contact_id = ident or c.hektor_target_id = ident\n"
     "        or c.hektor_target_id = nullif(trim(coalesce(new.result_json->>'hektor_contact_id', '')), '')"),
]
APRES_TXT = AVANT_TXT
for a, n in ANCRES:
    assert AVANT_TXT.count(a) == 1, (a, AVANT_TXT.count(a))
    APRES_TXT = APRES_TXT.replace(a, n)
for a, n in ANCRES:
    assert APRES_TXT.count(n) == 1, n
RETOUR = APRES_TXT
for a, n in ANCRES:
    RETOUR = RETOUR.replace(n, a)
assert md5(RETOUR) == AVANT
APRES = md5(APRES_TXT)

TRIG_AVANT = "CREATE TRIGGER app_contact_saisie_modif_job_trg AFTER UPDATE ON public.app_console_job FOR EACH ROW WHEN (((new.status = 'done'::text) AND (old.status IS DISTINCT FROM 'done'::text) AND (new.job_type = ANY (ARRAY['update_hektor_contact'::text, 'update_hektor_mandant_contact'::text])))) EXECUTE FUNCTION app_contact_saisie_modif_job_trg()"
TYPES_AVANT = "('update_hektor_contact', 'update_hektor_mandant_contact')"
TYPES_APRES = "('update_hektor_contact', 'update_hektor_mandant_contact', 'create_hektor_contact', 'create_hektor_mandant_contact')"


def lit(t, i, cote):
    tag = f"${cote}{i}$"
    assert tag not in t
    return f"replace({tag}{t}{tag}, chr(13), '')"


def bloc(nom, sens):
    a = ",\n        ".join(lit(x, i + 1, "a") for i, (x, _) in enumerate(ANCRES))
    n = ",\n        ".join(lit(y, i + 1, "n") for i, (_, y) in enumerate(ANCRES))
    if sens == "pose":
        de, vers, cherche, remplace, deja = AVANT, APRES, "ancres", "neufs", APRES
        types = TYPES_APRES
    else:
        de, vers, cherche, remplace, deja = APRES, AVANT, "neufs", "ancres", AVANT
        types = TYPES_AVANT
    return f"""DO ${nom}$
DECLARE
    d text := replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '');
    ancres text[] := array[
        {a}];
    neufs text[] := array[
        {n}];
    i int;
    nb int;
BEGIN
    IF md5(d) = '{deja}' THEN
        RAISE NOTICE '%', 'Deja dans l''etat voulu ({deja[:8]}) : la fonction n''est pas reecrite.';
    ELSE
        IF md5(d) <> '{de}' THEN
            RAISE EXCEPTION '%', format('ARRET : app_contact_saisie_modif_job_trg a l''empreinte %s, attendu {de[:8]}. Rien n''est ecrit.', md5(d));
        END IF;
        FOR i IN 1 .. array_length({cherche}, 1) LOOP
            nb := (length(d) - length(replace(d, {cherche}[i], ''))) / length({cherche}[i]);
            IF nb <> 1 THEN
                RAISE EXCEPTION '%', format('ARRET : le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
            END IF;
            d := replace(d, {cherche}[i], {remplace}[i]);
        END LOOP;
        IF md5(d) <> '{vers}' THEN
            RAISE EXCEPTION '%', format('ARRET : le texte obtenu a l''empreinte %s, attendu {vers[:8]} (calcule d''avance). Rien n''est ecrit.', md5(d));
        END IF;
        EXECUTE d;
    END IF;
    -- le declencheur : sa clause WHEN porte la liste des travaux
    EXECUTE 'drop trigger if exists app_contact_saisie_modif_job_trg on public.app_console_job';
    EXECUTE $t$create trigger app_contact_saisie_modif_job_trg
  after update on public.app_console_job
  for each row
  when (new.status = 'done' and old.status is distinct from 'done'
        and new.job_type in {types})
  execute function public.app_contact_saisie_modif_job_trg()$t$;
END
${nom}$;"""


def controles(empreinte, nb_types):
    return f"""SELECT 1 AS "#", 'la fonction de garde porte l''empreinte {empreinte[:8]}' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{empreinte}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'le declencheur existe, un seul, sur {nb_types} types de travail',
       CASE WHEN (SELECT count(*) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') = 1
             AND (SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') LIKE '%update_hektor_mandant_contact%'
             AND ((SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') LIKE '%create_hektor_contact%') = {'true' if nb_types == 4 else 'false'}
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur du controle est inchange',
       CASE WHEN EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_retour_controle') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;"""


ENTETE = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- CHANTIER ⑧ · 8a-B2 — LE CONTRÔLE AU RETOUR S'ÉTEND À LA CRÉATION DE CONTACT  22/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md (« Clôturer 8a »)
--
-- LE DÉFAUT (audit du 22/10) : B (patch 8a5) ne garde que les MODIFICATIONS. Un contact CRÉÉ
-- dans l'app part chez Hektor ; si Hektor ne garde pas un champ (une ville sans son code
-- postal, une ville contraire au code postal — prouvé ce jour), la relecture le remplace
-- en silence, exactement comme avant B.
--
-- CE QUE FAIT CE PATCH — CHIRURGICAL, trois ancres d'une ligne dans la fonction de garde :
--   · elle accepte aussi « created » (contact) et « created_and_linked » (mandant) ;
--   · elle retrouve le contact aussi par notre numéro dans la charge (app_identite) et par
--     celui de Hektor dans le résultat ;
--   · le déclencheur est recréé avec les deux types de création en plus.
-- Rien d'autre : la table, le verdict, la vue, la sentinelle et l'interrupteur
-- (contact_retour_controle) sont ceux de B.
--
-- ⛔ GARDE : la fonction n'est modifiée que si son empreinte est {AVANT[:8]} (posée le 22/10 à
--    13:05) et le texte neuf porte l'empreinte {APRES[:8]} CALCULÉE D'AVANCE.
-- RETOUR ARRIÈRE : supabase/{BASE}_INVERSE.sql (rend {AVANT[:8]} et le déclencheur à 2 types).
-- ═══════════════════════════════════════════════════════════════════════════
"""

pose = f"""{ENTETE}
BEGIN;

{bloc("pose", "pose")}

-- LES CONTRÔLES — tous doivent dire OK
{controles(APRES, 4)}

COMMIT;
"""

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a-B2 — le contrôle au retour revient aux seules modifications  22/10/2026
-- Rend à app_contact_saisie_modif_job_trg son texte de 13:05 ({AVANT[:8]}) et au déclencheur
-- ses 2 types de travail. Aucune donnée n'est touchée : les saisies de création déjà gardées
-- restent dans la table et seront jugées comme les autres.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

{bloc("retour", "retour")}

{controles(AVANT, 2)}

COMMIT;
"""

ESSAIS = r"""DO $essai$
DECLARE
    cid  text := '20000007';
    tgt  text;
    j1 uuid; j2 uuid; j3 uuid; j4 uuid; j5 uuid;
    n int;
    v jsonb;
    paris text;
    avant_on text;
BEGIN
    select hektor_target_id into tgt from public.app_contact_current where hektor_contact_id = cid;
    IF tgt IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai 20000007 n''a pas de numero Hektor -- la repetition ne prouverait rien.';
    END IF;
    select value into avant_on from public.app_setting where key = 'contact_retour_controle';
    update public.app_setting set value = 'on' where key = 'contact_retour_controle';
    delete from public.app_contact_saisie_modif where hektor_contact_id = cid and etat = 'attente';

    -- (1) une CREATION de contact : notre numero dans la charge, celui de Hektor dans le resultat
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('create_hektor_contact', 'running',
            jsonb_build_object('app_identite', cid, 'creation_token', gen_random_uuid()::text,
                               'last_name', 'ESSAI 8A BIS', 'civilite', 'Mme.', 'city', 'Firminy', 'postal_code', '42000',
                               'comments', 'Creation B2', 'birth_date', '03-05-1982', 'company_name', 'X'),
            now() - interval '10 seconds')
    returning id into j1;
    update public.app_console_job set status = 'done', finished_at = now(),
           result_json = jsonb_build_object('status', 'created', 'hektor_contact_id', tgt) where id = j1;
    select saisie into v from public.app_contact_saisie_modif where job_id = j1 and hektor_contact_id = cid and etat = 'attente';
    insert into _m values (1, 'creation de contact (created) : la saisie est gardee par notre cle, sans naissance ni societe',
        case when v->>'ville' = 'Firminy' and v->>'code_postal' = '42000' and v->>'civilite' = 'Mme.' and v->>'commentaires' = 'Creation B2'
                  and not v ? 'birth_date' and not v ? 'company_name' then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (2) le retour de Hektor apres la creation : la ville recalculee d'apres le code postal
    paris := to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS');
    update public.app_contact_current set refreshed_at = now() + interval '1 second', date_maj = paris,
           nom = 'ESSAI 8A BIS', civilite = 'Mme.', ville = 'Saint-Étienne', code_postal = '42000', commentaires = 'Creation B2'
     where hektor_contact_id = cid;
    select verdict into v from public.app_contact_saisie_modif where job_id = j1 and etat = 'juge';
    insert into _m values (2, 'le retour de la creation est juge : ville remplace, le reste identique',
        case when v->'ville'->>'etat' = 'remplace' and v->'code_postal'->>'etat' = 'identique' and v->'nom'->>'etat' = 'identique'
                  and v->'commentaires'->>'etat' = 'identique' then 'OK' else 'ECHEC ' || coalesce(v::text, 'pas juge') end);
    select count(*) into n from public.app_v_contact_modif_ecarts where job_id = j1 and champ = 'ville' and etat = 'remplace';
    insert into _m values (3, 'la vue montre l''ecart de la creation', case when n = 1 then 'OK' else 'ECHEC ' || n end);

    -- (4) une creation de MANDANT (created_and_linked) : PAS de numero de l'app dans la charge, seulement Hektor dans le resultat
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('create_hektor_mandant_contact', 'running',
            jsonb_build_object('app_dossier_id', 3828957, 'hektor_annonce_id', '62774', 'last_name', 'ESSAI 8A BIS', 'email', 'b2.mandant@example.invalid'),
            now() - interval '5 seconds')
    returning id into j2;
    update public.app_console_job set status = 'done', finished_at = now(),
           result_json = jsonb_build_object('status', 'created_and_linked', 'hektor_contact_id', tgt, 'hektor_annonce_id', '62774') where id = j2;
    select hektor_contact_id into v from (select to_jsonb(s.hektor_contact_id) as hektor_contact_id from public.app_contact_saisie_modif s where job_id = j2) x;
    insert into _m values (4, 'creation de mandant (created_and_linked) : retrouvee par le numero Hektor du resultat, rangee par NOTRE cle',
        case when v #>> '{}' = cid then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (5) la MODIFICATION marche toujours comme avant (non-regression de B)
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('update_hektor_contact', 'running', jsonb_build_object('hektor_contact_id', cid, 'from_pending', true, 'city', 'Lyon'), now())
    returning id into j3;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j3;
    select saisie into v from public.app_contact_saisie_modif where job_id = j3;
    insert into _m values (5, 'la modification (updated) est toujours gardee', case when v->>'ville' = 'Lyon' then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (6) une creation qui ECHOUE ou un conflit ne garde rien
    select count(*) into n from public.app_contact_saisie_modif;
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('create_hektor_contact', 'running', jsonb_build_object('app_identite', cid, 'last_name', 'Z'), now())
    returning id into j4;
    update public.app_console_job set status = 'done', result_json = '{"status":"duplicate_found"}'::jsonb, finished_at = now() where id = j4;
    insert into _m values (6, 'un autre resultat (pas created) ne garde rien', case when (select count(*) from public.app_contact_saisie_modif) = n then 'OK' else 'ECHEC' end);

    -- (7) ETEINT : une creation ne garde rien
    update public.app_setting set value = 'off' where key = 'contact_retour_controle';
    select count(*) into n from public.app_contact_saisie_modif;
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('create_hektor_contact', 'running', jsonb_build_object('app_identite', cid, 'last_name', 'Y'), now())
    returning id into j5;
    update public.app_console_job set status = 'done', result_json = jsonb_build_object('status', 'created', 'hektor_contact_id', tgt), finished_at = now() where id = j5;
    insert into _m values (7, 'interrupteur eteint : une creation ne garde rien (temoin inverse)', case when (select count(*) from public.app_contact_saisie_modif) = n then 'OK' else 'ECHEC' end);
    update public.app_setting set value = avant_on where key = 'contact_retour_controle';
END
$essai$;"""

repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a-B2 — la création de contact entre dans le contrôle — TOUT EST ANNULÉ
--                                                                    22/10/2026
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … ». Elle pose LE VRAI PATCH, joue 7 essais
-- (fausses créations, faux retours, sur le contact d'essai 20000007), puis LE VRAI RETOUR
-- ARRIÈRE. Rien ne reste. Fichier GÉNÉRÉ (phase2/checks/gen_patch_8a6_contact_creation_controle.py).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

{bloc("pose", "pose")}

{ESSAIS}

{bloc("retour", "retour")}

DO $fin$
DECLARE
    r text;
    ok int;
    total int;
BEGIN
    insert into _m values (8, 'l''inverse rend {AVANT[:8]} et le declencheur a 2 types',
        case when md5(replace(pg_get_functiondef('{FN}'::regprocedure), chr(13), '')) = '{AVANT}'
                  AND (SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') NOT LIKE '%create_hektor_contact%'
                  AND (SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') LIKE '%update_hektor_mandant_contact%'
             then 'OK' else 'ECHEC' end);
    select count(*) filter (where valeur = 'OK'), count(*), string_agg(n || ' ' || valeur || ' ' || cle, ' | ' order by n)
      into ok, total, r from _m;
    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s | %s', ok, total, r);
END
$fin$;
"""

for nom, texte in ((BASE + ".sql", pose), (BASE + "_INVERSE.sql", inverse), (BASE + "_REPETITION.sql", repetition)):
    OUT.joinpath(nom).write_text(texte, encoding="utf-8", newline="\n")
    print("ecrit", nom, len(texte))
print("avant", AVANT, "apres", APRES)
