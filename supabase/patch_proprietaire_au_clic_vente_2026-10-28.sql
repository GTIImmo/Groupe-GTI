-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES §52 C — « PROPRIÉTAIRE DEPUIS LE … » POSÉ AU CLIC DE LA VENTE, COMME LES AUTRES GESTES           28/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §52.11.
--
-- POURQUOI : au clic d'une vente faite dans l'app, le type de l'acheteur devient « Acheteur — Vente » tout de suite (§45),
--   mais son lien au bien « Propriétaire depuis le … » n'arrivait qu'à la nuit, en reclassant le lien que Hektor ajoute.
--   Frédéric (28/10) : « oui, dès le clic » ; « fais comme les autres gestes ».
-- LE PATRON : `app_link_mandant_optimistic` (lier un mandant) — la ligne est écrite AU CLIC dans le registre des liens,
--   `source = 'app'`, `present_in_hektor = false` (Hektor ne la connaît pas encore), une clé `app:…` ; la vue la montre ;
--   la nuit l'ADOPTE en gardant son numéro quand Hektor la redescend (relation_ledger, `app_relation__sb`), et la règle de
--   nuit lui repose `origine = 'vente'` (le lien que Hektor ajoute à chaque vente).
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE (1 bloc ajouté, juste avant le recalcul du type, dans `app_change_annonce_status_optimistic`) :
--   pour une VENTE, chaque acquéreur de la transaction (la table des parties, que le déclencheur vient de remplir) reçoit son
--   lien au bien : `origine = 'vente'`, `proprietaire_depuis` = la date de la vente (sinon le jour).
--   · Le couple existe déjà ? On NE RÉÉCRIT PAS une ligne connue (comme `link_mandant`) — sauf une ligne marquée « acheteur »
--     (sa vente avait été supprimée, §52 A) : elle redevient « née de la vente ».
--   · BEST-EFFORT, comme `link_mandant` : une erreur ici ne fait jamais échouer la vente ; elle est dite (WARNING).
--   Le recalcul du type qui suit lit ce lien : l'acheteur est « Propriétaire » tout de suite.
-- ⚠ CE QUE ÇA NE FAIT PAS : rien chez Hektor ; ni l'offre ni le compromis (D2 : propriétaire à l'acte seulement).
-- Le bloc vérifie l'empreinte de la fonction (celle du 27/10, type au geste) et S'ARRÊTE si elle a changé.
-- Retour arrière : patch_proprietaire_au_clic_vente_2026-10-28_INVERSE.sql
-- Contrôle       : patch_proprietaire_au_clic_vente_2026-10-28_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $p$
DECLARE
    d   text := pg_get_functiondef('public.app_change_annonce_status_optimistic'::regproc);
    -- ⚠ ancre sur UNE SEULE LIGNE (leçon 30) ; le bloc ajouté ne porte que des LF ; les CR du corps sont gardés
    ancre text := 'perform public.app_recalculer_type_du_bien(d.hektor_annonce_id::text, target_dossier_id);';
    bloc  text := E'-- @C-proprio-au-clic (28/10/2026, types §52 C) : l''acheteur d''une VENTE reçoit son lien au bien au clic.\n'
        || E'  if v_kind = ''vente'' and v_affaire_id is not null then\n'
        || E'    begin\n'
        || E'      insert into public.app_relation as ar\n'
        || E'        (app_relation_id, app_contact_id, app_dossier_id, hektor_annonce_id, hektor_contact_id,\n'
        || E'         fait, role_hektor, source, relation_key, first_seen_at, last_seen_at,\n'
        || E'         present_in_hektor, absent_depuis, origine, proprietaire_depuis)\n'
        || E'      select nextval(''public.app_relation_id_app_seq''), p.app_contact_id, target_dossier_id,\n'
        || E'             d.hektor_annonce_id::text, p.hektor_contact_id,\n'
        || E'             ''proprietaire_du_bien'', null, ''app'', ''app:vente:'' || v_affaire_id || '':'' || p.app_contact_id,\n'
        || E'             now()::text, now()::text, false, null, ''vente'',\n'
        || E'             left(coalesce(nullif(trim(coalesce(l.date, '''')), ''''), current_date::text), 10)\n'
        || E'        from public.app_affaire_partie p\n'
        || E'        join public.app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id\n'
        || E'       where p.app_affaire_id = v_affaire_id and p.role = ''acquereur'' and p.app_contact_id is not null\n'
        || E'      on conflict (app_contact_id, hektor_annonce_id) do update\n'
        || E'         set origine = ''vente'',\n'
        || E'             proprietaire_depuis = coalesce(ar.proprietaire_depuis, excluded.proprietaire_depuis),\n'
        || E'             retire_le = null, retire_par = null, absent_depuis = null\n'
        || E'       where ar.origine = ''acheteur'';\n'
        || E'    exception when others then\n'
        || E'      raise warning ''proprietaire au clic de la vente % : non pose (%)'', v_affaire_id, sqlerrm;\n'
        || E'    end;\n'
        || E'  end if;\n'
        || E'  -- @C-fin\n  ';
    n int;
BEGIN
    IF md5(d) <> 'fce35139d02f8f4f995392a9f8566891' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a change depuis l''audit du 28/10 (empreinte %s au lieu de fce35139...) ; rien n''est ecrit.', md5(d));
    END IF;
    n := (length(d) - length(replace(d, ancre, ''))) / length(ancre);
    IF n <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre est trouvee %s fois (1 attendue) ; rien n''est ecrit.', n);
    END IF;
    EXECUTE replace(d, ancre, bloc || ancre);
END
$p$;

COMMIT;
