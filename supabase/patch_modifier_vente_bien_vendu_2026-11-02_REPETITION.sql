-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION de patch_modifier_vente_bien_vendu_2026-11-02.sql (4C, 02/11/2026)
-- Joue le patch PUIS son retour arrière dans UNE transaction ANNULÉE : rien n'est gardé.
-- Appels faits avec les droits de Frédéric (admin) ; les travaux créés disparaissent au ROLLBACK.
-- Résultat attendu (une ligne par appel) :
--   avant / 25595 (vente, bien de l'historique) : numero, titre, nego VIDES       <- le défaut
--   apres / 25595                               : VM66432, le titre, durand@...   <- le correctif
--   avant / 30666 et apres / 30666 (compromis, bien en annonce) : IDENTIQUES        <- le témoin
--   retour / 25595                              : de nouveau VIDES, empreinte 97b1b9d2
-- ⚠ La fonction est appelée UNE fois par ligne, dans pg_temp.essai : jamais dans un WHERE
--   (le 02/11, un appel dans un WHERE l'a rejouée pour chaque ligne de app_console_job).
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;
set local statement_timeout = '60s';
select set_config('request.jwt.claims', json_build_object('sub',(select id from auth.users where email='frederic.gerphagnon@gti-immobilier.fr'),'role','authenticated')::text, true);
create temp table t_essai(moment text, affaire bigint, charge jsonb, empreinte text) on commit drop;
create or replace function pg_temp.essai(m text, aff bigint, charge jsonb) returns void language plpgsql as $f$
declare r jsonb;
begin
  r := public.app_modifier_affaire_optimistic(aff, charge);
  insert into t_essai select m, aff, j.payload_json,
    md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), ''))
    from public.app_console_job j where j.id = (r->>'job_id')::uuid;
end $f$;

select pg_temp.essai('1 avant', 25595, '{}'::jsonb), pg_temp.essai('1 avant', 30666, '{}'::jsonb);

DO $pose$
DECLARE
    d      text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    a1     text := '      ''numero_dossier'',        d.numero_dossier,';
    a2     text := '      ''titre_bien'',            d.titre_bien,';
    a3     text := '      ''negociateur_email'',     d.negociateur_email);';
    n1     text := replace($n1$      -- 4C (02/11/2026) : un bien VENDU n'est plus dans app_dossier_current -> l'index historique,
      -- puis ce que l'ecran a envoye. Voir supabase/patch_modifier_vente_bien_vendu_2026-11-02.sql.
      'numero_dossier',        coalesce(d.numero_dossier,
                                 (select h.numero_dossier from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'numero_dossier', '')), '')),$n1$, chr(13), '');
    n2     text := replace($n2$      'titre_bien',            coalesce(d.titre_bien,
                                 (select h.titre_bien from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'titre_bien', '')), '')),$n2$, chr(13), '');
    n3     text := replace($n3$      'negociateur_email',     coalesce(d.negociateur_email,
                                 (select h.negociateur_email from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'negociateur_email', '')), '')));$n3$, chr(13), '');
    n      integer;
BEGIN
    IF md5(d) <> '97b1b9d28bffb7a9b5d2e6e92eea9bd4' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic a change depuis l''audit du 02/11 (empreinte 97b1b9d2 attendue). Rien n''est change.';
    END IF;
    n := (length(d) - length(replace(d, a1, ''))) / length(a1);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre numero_dossier trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;
    n := (length(d) - length(replace(d, a2, ''))) / length(a2);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre titre_bien trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;
    n := (length(d) - length(replace(d, a3, ''))) / length(a3);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre negociateur_email trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;

    EXECUTE replace(replace(replace(d, a1, n1), a2, n2), a3, n3);
END
$pose$;

select pg_temp.essai('2 apres', 25595, '{}'::jsonb), pg_temp.essai('2 apres', 30666, '{}'::jsonb);

DO $inverse$
DECLARE
    d      text;
    a1     text := '      ''numero_dossier'',        d.numero_dossier,';
    a2     text := '      ''titre_bien'',            d.titre_bien,';
    a3     text := '      ''negociateur_email'',     d.negociateur_email);';
    n1     text := replace($n1$      -- 4C (02/11/2026) : un bien VENDU n'est plus dans app_dossier_current -> l'index historique,
      -- puis ce que l'ecran a envoye. Voir supabase/patch_modifier_vente_bien_vendu_2026-11-02.sql.
      'numero_dossier',        coalesce(d.numero_dossier,
                                 (select h.numero_dossier from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'numero_dossier', '')), '')),$n1$, chr(13), '');
    n2     text := replace($n2$      'titre_bien',            coalesce(d.titre_bien,
                                 (select h.titre_bien from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'titre_bien', '')), '')),$n2$, chr(13), '');
    n3     text := replace($n3$      'negociateur_email',     coalesce(d.negociateur_email,
                                 (select h.negociateur_email from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'negociateur_email', '')), '')));$n3$, chr(13), '');
BEGIN
    d := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    IF md5(d) <> '176ee0df2aa45021777390b08d5763e7' THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction en ligne n''est pas celle du patch 4C (empreinte 176ee0df attendue). Rien n''est change.';
    END IF;
    EXECUTE replace(replace(replace(d, n1, a1), n2, a2), n3, a3);
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), ''))
       <> '97b1b9d28bffb7a9b5d2e6e92eea9bd4' THEN
        RAISE EXCEPTION '%', 'ARRET : l''empreinte d''origine 97b1b9d2 n''est pas retrouvee. Rien n''est garde.';
    END IF;
END
$inverse$;

select pg_temp.essai('3 retour', 25595, '{}'::jsonb);

select moment, affaire, charge->>'numero_dossier' numero, charge->>'titre_bien' titre,
       charge->>'negociateur_email' nego, coalesce(charge->>'vente_id', charge->>'compromis_id') cible, left(empreinte, 8) empreinte
  from t_essai order by affaire, moment;
ROLLBACK;
