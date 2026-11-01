-- ═══════════════════════════════════════════════════════════════════════════
-- REGISTRE DES TRANSACTIONS, ÉTAPE 2 : LA LISTE « UNE LIGNE PAR DOSSIER » ET SES DROITS       31/10/2026
-- Décisions de Frédéric :
--   30/10 « une ligne = un dossier (une chaîne) » ; pilotage réservé aux admins (étape à part) ;
--   31/10 « chacun ses dossiers : un négociateur voit les siens, un admin voit tout » ;
--   31/10 « il voit les dossiers où il est nommé en 1 ou 2 » et « il faut que la répartition soit
--         ENTIÈREMENT visible même si une part n'est pas à son nom ».
--
-- CE QUI EXISTE (mesuré le 31/10) :
--   . les transactions (app_affaire_ledger) : un admin / manager / lecture voit tout
--     (is_app_global_reader), un négociateur voit celles de SES BIENS (app_mes_biens_portefeuille :
--     vivants, archivés, vendus, par son e-mail). Réponse « B » du chantier ② (12/10), empreinte de la
--     règle 73d92b58.
--   . la répartition (app_affaire_repartition) : lisible par TOUT compte connecté (USING true, posée
--     le 14/09, AVANT le chantier ② qui ne l'a pas couverte).
--
-- LE TROU : un négociateur nommé dans la répartition sans être le négociateur du bien ne voit pas le
--   dossier où il touche une part -- 2026 : 17 ventes sur 282 (2022-2026 : 263). Ex. chaîne 1011,
--   bien 1993 (FORLICO sur la fiche et au registre des mandats), parts entrée ET sortie à PEREIRA.
--
-- CE QUE FAIT CE PATCH (additif ; rien n'est retiré à personne, sauf la répartition des dossiers
-- qu'on ne voit pas) :
--   1. app_mes_chaines_nommees()  : les dossiers où je suis nommé (entrée ou sortie, rang 1 ou 2),
--      par TOUS mes numéros de l'annuaire (un même e-mail en porte jusqu'à 3, un par agence).
--   2. la règle des TRANSACTIONS : + « ou le dossier est un de ceux où je suis nommé ».
--      Effet : la fiche du bien 1993 montre ses transactions à PEREIRA. ⚠ Les vues en lecture
--      « security_invoker » qui lisent le registre (app_contact_relations_current,
--      app_ecart_statut_regle, app_v_affaire_carnet_ecarts, app_v_affaire_partie_ecarts) suivent :
--      même élargissement, voulu.
--   3. la règle de la RÉPARTITION : visible si on voit le DOSSIER (au moins une de ses transactions,
--      sous la règle du 2) -- donc ENTIÈRE dans ses dossiers, et plus rien ailleurs. L'écran ne la
--      demande déjà que pour les dossiers qu'il a lus (api.ts loadRepartition /
--      loadRepartitionsDesChaines, par app_chaine_id) : rien ne change pour lui.
--      Les écrivains (app_repartition_commission_set, _absorber, _purger_orphelines) et la vue
--      app_v_repartition_orpheline sont SECURITY DEFINER : non touchés.
--   4. app_registre_dossiers(p_annee) : la liste, une ligne par dossier, filtrée par EXACTEMENT la
--      règle du 2 (même prédicat, ligne à ligne), avec le bien retrouvé par ses 4 sources (vivant →
--      app_dossier_current ; vendu → app_historical_annonce_index_current.app_historical_id ; archivé
--      → index archive par n° d'annonce ; registre des mandats par n° d'annonce).
--      ÉTAPE = états de Hektor seulement (décision du 30/10), par priorité :
--        vendu > compromis (en cours) > compromis_annule > offre_acceptee > offre_proposee > offre_refusee
--      (une offre sans état compte comme proposée : 49 lignes, défaut d'import connu du 29/10).
--      HONORAIRES = entrée + sortie (vérifié 287/287 le 30/10), de la transaction de référence
--      (la vente, sinon le compromis en cours, sinon le dernier compromis, sinon la dernière offre).
--      Les 17 transactions supprimées chez Hektor sont écartées, comme au chaînage.
--
-- GARDES : s'arrête si la règle des transactions n'a pas l'empreinte du 31/10 (73d92b58), si celle de
--          la répartition n'est plus « true », ou si une des deux fonctions existe déjà.
-- Retour arrière : patch_registre_dossiers_droits_2026-10-31_INVERSE.sql
-- Contrôle       : patch_registre_dossiers_droits_2026-10-31_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

DO $garde$
BEGIN
    IF (SELECT md5(qual) FROM pg_policies WHERE schemaname = 'public' AND tablename = 'app_affaire_ledger'
          AND policyname = 'app_affaire_ledger_select_active_users') IS DISTINCT FROM '73d92b58e78ee20e7b249416929fba53' THEN
        RAISE EXCEPTION '%', 'ARRET : la regle de lecture du registre a change depuis le 31/10 (empreinte 73d92b58 attendue). Rien n''est change.';
    END IF;
    IF (SELECT qual FROM pg_policies WHERE schemaname = 'public' AND tablename = 'app_affaire_repartition'
          AND policyname = 'app_affaire_repartition_read') IS DISTINCT FROM 'true' THEN
        RAISE EXCEPTION '%', 'ARRET : la regle de lecture de la repartition n''est plus « true ». Rien n''est change.';
    END IF;
    IF to_regprocedure('public.app_mes_chaines_nommees()') IS NOT NULL
       OR to_regprocedure('public.app_registre_dossiers(integer)') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : une des fonctions du registre existe deja. Rien n''est change.';
    END IF;
END
$garde$;

-- 1. LES DOSSIERS OÙ JE SUIS NOMMÉ
CREATE FUNCTION public.app_mes_chaines_nommees()
RETURNS SETOF bigint
LANGUAGE sql
STABLE SECURITY DEFINER
SET search_path TO 'public'
AS $fn$
    -- Registre des transactions, 31/10/2026 : « il voit les dossiers où il est nommé en 1 ou 2 ».
    -- Tous les numéros de l'annuaire qui portent mon e-mail (un par agence, actifs ou non : les parts
    -- anciennes sont au nom d'anciens numéros). Voir supabase/patch_registre_dossiers_droits_2026-10-31.sql
    with moi as (
        select lower(trim(coalesce(p.email, ''))) as adresse
          from public.app_user_profile p
         where p.id = auth.uid() and p.is_active = true
         limit 1
    ), mes_numeros as (
        select distinct d.hektor_user_id
          from public.app_hektor_negotiator_agency_directory d, moi
         where nullif(moi.adresse, '') is not null
           and lower(trim(coalesce(d.email, ''))) = moi.adresse
           and nullif(trim(coalesce(d.hektor_user_id, '')), '') is not null
    )
    select distinct r.app_chaine_id
      from public.app_affaire_repartition r
     where r.hektor_user_id in (select hektor_user_id from mes_numeros)
       and r.app_chaine_id is not null;
$fn$;

REVOKE ALL ON FUNCTION public.app_mes_chaines_nommees() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_mes_chaines_nommees() TO authenticated, service_role;

-- 2. LA RÈGLE DES TRANSACTIONS : + les dossiers où je suis nommé
ALTER POLICY app_affaire_ledger_select_active_users ON public.app_affaire_ledger
USING (
    (( SELECT is_app_global_reader() AS is_app_global_reader)
     OR (app_dossier_id IN ( SELECT m.id FROM app_mes_biens_portefeuille() m(id, hid)))
     OR ((hektor_annonce_id)::text IN ( SELECT m.hid FROM app_mes_biens_portefeuille() m(id, hid)))
     OR (app_chaine_id IN ( SELECT c.id FROM app_mes_chaines_nommees() c(id))))
);

-- 3. LA RÈGLE DE LA RÉPARTITION : entière dans les dossiers qu'on voit, rien ailleurs
--    (la sous-requête lit le registre SOUS la règle du 2 : c'est voulu, c'est elle qui décide)
ALTER POLICY app_affaire_repartition_read ON public.app_affaire_repartition
USING (
    (( SELECT is_app_global_reader() AS is_app_global_reader)
     OR (EXISTS ( SELECT 1 FROM app_affaire_ledger l WHERE l.app_chaine_id = app_affaire_repartition.app_chaine_id)))
);

-- 4. LA LISTE, UNE LIGNE PAR DOSSIER
CREATE FUNCTION public.app_registre_dossiers(p_annee integer DEFAULT NULL)
RETURNS TABLE (
    app_chaine_id          bigint,
    app_dossier_id         bigint,
    hektor_annonce_id      bigint,
    etape                  text,
    date_offre             text,
    date_compromis         text,
    date_acte_prevue       text,
    date_vente             text,
    date_dernier_evenement text,
    montant                numeric,
    honoraires_entree      numeric,
    honoraires_sortie      numeric,
    honoraires             numeric,
    hektor_acquereur_id    text,
    acquereur_nom          text,
    numero_mandat          text,
    ville                  text,
    code_postal            text,
    type_bien              text,
    photo_url_listing      text,
    agence_nom             text,
    negociateur_email      text,
    statut_annonce         text,
    nb_transactions        integer,
    je_suis_nomme          boolean
)
LANGUAGE sql
STABLE SECURITY DEFINER
SET search_path TO 'public'
AS $fn$
    -- Registre des transactions, 31/10/2026. Voir supabase/patch_registre_dossiers_droits_2026-10-31.sql
    -- ⚠ Le filtre de droits est le MÊME prédicat que la règle de lecture du registre (policy
    --   app_affaire_ledger_select_active_users) : la liste ne montre jamais un dossier dont la fiche
    --   cacherait les transactions, ni l'inverse.
    with glob as (
        select public.is_app_global_reader() as tout
    ), port as (
        select m.id, m.hid from public.app_mes_biens_portefeuille() m(id, hid)
    ), nom as (
        select c.id from public.app_mes_chaines_nommees() c(id)
    ), l as (
        select l.*,
               case when l.montant ~ '^-?\d+(\.\d+)?$' then l.montant::numeric end           as m,
               case when l.honoraires_entree ~ '^-?\d+(\.\d+)?$' then l.honoraires_entree::numeric end as he,
               case when l.honoraires_sortie ~ '^-?\d+(\.\d+)?$' then l.honoraires_sortie::numeric end as hs
          from public.app_affaire_ledger l, glob
         where l.app_chaine_id is not null
           and not (btrim(coalesce(l.hektor_affaire_id, '')) <> '' and l.present_in_hektor is false)
           and (glob.tout
                or l.app_dossier_id in (select id from port)
                or l.hektor_annonce_id::text in (select hid from port)
                or l.app_chaine_id in (select id from nom))
    ), ch as (
        select l.app_chaine_id,
               bool_or(l.kind = 'vente')                                         as a_vente,
               bool_or(l.kind = 'compromis' and l.state = 'active')              as a_compromis,
               bool_or(l.kind = 'compromis')                                     as a_compromis_tout,
               bool_or(l.kind = 'offre' and l.state = 'accepted')                as a_offre_acceptee,
               bool_or(l.kind = 'offre' and coalesce(l.state, 'proposed') = 'proposed') as a_offre_proposee,
               min(l.date) filter (where l.kind = 'offre')                        as date_offre,
               max(l.date) filter (where l.kind = 'compromis')                    as date_compromis,
               max(l.date_acte) filter (where l.kind = 'compromis' and l.state = 'active') as date_acte_prevue,
               max(l.date) filter (where l.kind = 'vente')                        as date_vente,
               max(l.date)                                                        as date_dernier_evenement,
               count(*)::integer                                                  as nb
          from l
         group by l.app_chaine_id
    ), ref as (
        select distinct on (l.app_chaine_id)
               l.app_chaine_id, l.app_dossier_id, l.hektor_annonce_id, l.m, l.he, l.hs,
               l.hektor_acquereur_id, l.numero_mandat
          from l
         order by l.app_chaine_id,
                  case l.kind when 'vente' then 1
                              when 'compromis' then case when l.state = 'active' then 2 else 3 end
                              else 4 end,
                  l.date desc nulls last, l.app_affaire_id desc
    ), ct as (
        select distinct on (c.hektor_target_id) c.hektor_target_id,
               nullif(concat_ws(' ', nullif(trim(c.civilite), ''), nullif(trim(c.prenom), ''), nullif(trim(c.nom), '')), '') as nom_complet,
               nullif(trim(c.display_name), '') as display_name
          from public.app_contact_current c
         where c.hektor_target_id in (select ref.hektor_acquereur_id from ref)
         order by c.hektor_target_id
    ), reg as (
        select distinct on (r.hektor_annonce_id) r.hektor_annonce_id, r.numero_mandat, r.ville, r.code_postal,
               r.type_bien, r.photo_url_listing, r.agence_nom, r.negociateur_email, r.statut_annonce
          from public.app_mandat_register_current r
         order by r.hektor_annonce_id, r.mandat_date_debut desc nulls last
    )
    select ch.app_chaine_id,
           ref.app_dossier_id,
           ref.hektor_annonce_id,
           case when ch.a_vente          then 'vendu'
                when ch.a_compromis      then 'compromis'
                when ch.a_compromis_tout then 'compromis_annule'
                when ch.a_offre_acceptee then 'offre_acceptee'
                when ch.a_offre_proposee then 'offre_proposee'
                else 'offre_refusee' end,
           ch.date_offre, ch.date_compromis, ch.date_acte_prevue, ch.date_vente, ch.date_dernier_evenement,
           ref.m, ref.he, ref.hs, coalesce(ref.he, 0) + coalesce(ref.hs, 0),
           ref.hektor_acquereur_id,
           coalesce(ct.nom_complet, ct.display_name),
           coalesce(nullif(ref.numero_mandat, ''), d.numero_mandat, h.numero_mandat, a.numero_mandat, reg.numero_mandat),
           coalesce(d.ville, h.ville, a.ville, reg.ville),
           coalesce(d.code_postal, h.code_postal, a.code_postal, reg.code_postal),
           coalesce(d.type_bien, h.type_bien, a.type_bien, reg.type_bien),
           coalesce(d.photo_url_listing, h.photo_url_listing, a.photo_url_listing, reg.photo_url_listing),
           coalesce(d.agence_nom, h.agence_nom, a.agence_nom, reg.agence_nom),
           coalesce(d.negociateur_email, h.negociateur_email, a.negociateur_email, reg.negociateur_email),
           coalesce(d.statut_annonce, h.statut_annonce, a.statut_annonce, reg.statut_annonce),
           ch.nb,
           ch.app_chaine_id in (select id from nom)
      from ch
      join ref on ref.app_chaine_id = ch.app_chaine_id
      left join public.app_dossier_current d                  on d.app_dossier_id = ref.app_dossier_id
      left join public.app_historical_annonce_index_current h on d.app_dossier_id is null and h.app_historical_id = ref.app_dossier_id
      left join public.app_archive_annonce_index_current a    on d.app_dossier_id is null and h.app_historical_id is null
                                                              and a.hektor_annonce_id = ref.hektor_annonce_id
      left join reg                                           on reg.hektor_annonce_id = ref.hektor_annonce_id
      left join ct                                            on ct.hektor_target_id = ref.hektor_acquereur_id
     where p_annee is null
        or left(ch.date_dernier_evenement, 4) = p_annee::text;
$fn$;

REVOKE ALL ON FUNCTION public.app_registre_dossiers(integer) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_registre_dossiers(integer) TO authenticated, service_role;

-- 5. LA PREUVE, DANS LA MÊME TRANSACTION : sinon rien n'est gardé.
DO $preuve$
BEGIN
    IF position('app_mes_chaines_nommees' in (SELECT qual FROM pg_policies WHERE schemaname = 'public'
          AND tablename = 'app_affaire_ledger' AND policyname = 'app_affaire_ledger_select_active_users')) = 0 THEN
        RAISE EXCEPTION 'ARRET : la regle du registre ne porte pas les dossiers nommes. Rien n''est garde.';
    END IF;
    IF (SELECT qual FROM pg_policies WHERE schemaname = 'public' AND tablename = 'app_affaire_repartition'
          AND policyname = 'app_affaire_repartition_read') = 'true' THEN
        RAISE EXCEPTION 'ARRET : la repartition est toujours ouverte a tous. Rien n''est garde.';
    END IF;
    -- en tant que postgres (sans utilisateur), la liste rend 0 ligne : la règle tient même sans compte
    IF (SELECT count(*) FROM public.app_registre_dossiers(NULL)) <> 0 THEN
        RAISE EXCEPTION 'ARRET : sans utilisateur, la liste rend des lignes. Rien n''est garde.';
    END IF;
END
$preuve$;

COMMIT;
