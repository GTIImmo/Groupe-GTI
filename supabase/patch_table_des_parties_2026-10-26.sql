-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES — LA TABLE DES PARTIES (app_affaire_partie)                                       26/10/2026
-- Décision de Frédéric (26/10 soir) : « oublie ma décision du 24/10 : le meilleur choix » → la vraie table des parties.
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md §15 (audit), §16 (proposition), §17 (le code).
--
-- UNE LIGNE PAR (TRANSACTION, PERSONNE, RÔLE) : acquéreur, vendeur, notaire de l'acquéreur, notaire du vendeur ; nos deux
-- numéros ; la place dans la liste (1 = le principal) ; les fiches « couple » de Hektor marquées ; une transaction retirée chez
-- Hektor garde ses parties, marquées (delete-never).
-- AUJOURD'HUI DÉRIVÉE des listes du registre par un DÉCLENCHEUR : elle ne peut pas les contredire ; rien ne change pour la nuit,
-- le worker, l'app ni l'écran. ⛔ Le déclencheur ne fait JAMAIS échouer l'écriture qui l'a appelé (journal + sentinelle).
-- La vue des liens d'un contact lit les acquéreurs dans cette table (par l'index de notre numéro).
-- ⛔ RIEN N'EST ÉCRIT CHEZ HEKTOR. Retour arrière : _INVERSE.sql (la vue d'avant à l'octet, puis tout est retiré : la table
-- est DÉRIVÉE, rien n'est perdu).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 1. LA TABLE DES PARTIES ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.app_affaire_partie (
    app_affaire_id        bigint  not null,
    role                  text    not null check (role in ('acquereur', 'vendeur', 'notaire_acquereur', 'notaire_vendeur')),
    rang                  integer not null,
    app_contact_id        bigint,
    hektor_contact_id     text,
    est_principal         boolean not null default false,
    fiche_sans_nom        boolean not null default false,
    transaction_presente  boolean not null,
    origine               text    not null default 'listes_du_registre' check (origine in ('listes_du_registre', 'app')),
    calcule_le            timestamptz not null default now(),
    primary key (app_affaire_id, role, rang)
);
comment on table public.app_affaire_partie is
  '⑧ 26/10 : LA TABLE DES PARTIES -- une ligne par (transaction, personne, role). Aujourd''hui DERIVEE des listes du registre des transactions par un declencheur (origine listes_du_registre) ; a la coupure (etape 3) les gestes de l''app y ecriront (origine app). Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md §15-17.';
-- l'index de la fiche d'un contact : NOTRE numero, en texte (meme expression que la vue)
create index if not exists idx_app_affaire_partie_contact_texte
    on public.app_affaire_partie (((app_contact_id)::text))
    where (app_contact_id is not null);
create index if not exists idx_app_affaire_partie_contact
    on public.app_affaire_partie (app_contact_id) where (app_contact_id is not null);

-- le journal des erreurs du declencheur (il ne fait JAMAIS echouer l'ecriture qui l'a appele)
create table if not exists public.app_affaire_partie_erreur (
    id              bigint generated always as identity primary key,
    app_affaire_id  bigint,
    erreur          text,
    le              timestamptz not null default now()
);

-- ── 2. LES DROITS ───────────────────────────────────────────────────────────────────────────────────────
alter table public.app_affaire_partie enable row level security;
alter table public.app_affaire_partie_erreur enable row level security;
revoke all on public.app_affaire_partie from anon, authenticated;
revoke all on public.app_affaire_partie_erreur from anon, authenticated;
grant select on public.app_affaire_partie to authenticated;
-- un negociateur ne voit que les parties des transactions qu'il voit : la politique RELIT le registre sous ses droits
drop policy if exists app_affaire_partie_select on public.app_affaire_partie;
create policy app_affaire_partie_select on public.app_affaire_partie for select to authenticated
    using (exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = app_affaire_partie.app_affaire_id));

-- ── 3. LE CALCUL : les parties d'UNE ligne du registre (les trois formes d'une liste : liste, objet seul, rien) ──
create or replace function public.app_affaire_partie_calculer(l public.app_affaire_ledger)
returns table (app_affaire_id bigint, role text, rang integer, app_contact_id bigint, hektor_contact_id text,
               est_principal boolean, fiche_sans_nom boolean, transaction_presente boolean)
language sql stable set search_path = public
as $c$
    SELECT l.app_affaire_id,
           'acquereur'::text AS role,
           x.ord::int AS rang,
           CASE WHEN (x.v ->> 'app_contact_id') ~ '^[0-9]+$' THEN (x.v ->> 'app_contact_id')::bigint END AS app_contact_id,
           nullif(btrim(coalesce(x.v ->> 'id', '')), '') AS hektor_contact_id,
           (x.ord = 1) AS est_principal,
           (btrim(coalesce(x.v ->> 'nom', '')) = '') AS fiche_sans_nom,
           coalesce(l.present_in_hektor, false) AS transaction_presente
      FROM jsonb_array_elements(CASE jsonb_typeof(l.acquereurs_json)
                                     WHEN 'array'  THEN l.acquereurs_json
                                     WHEN 'object' THEN jsonb_build_array(l.acquereurs_json)
                                     ELSE '[]'::jsonb END) WITH ORDINALITY x(v, ord)
     WHERE jsonb_typeof(x.v) = 'object'
    UNION ALL
    SELECT l.app_affaire_id, 'acquereur', 1, l.app_contact_id, nullif(btrim(coalesce(l.hektor_acquereur_id, '')), ''),
           true, false, coalesce(l.present_in_hektor, false)
     WHERE (l.app_contact_id IS NOT NULL OR nullif(btrim(coalesce(l.hektor_acquereur_id, '')), '') IS NOT NULL)
       AND (CASE jsonb_typeof(l.acquereurs_json) WHEN 'array' THEN jsonb_array_length(l.acquereurs_json)
                                                  WHEN 'object' THEN 1 ELSE 0 END) = 0
    UNION ALL
    SELECT l.app_affaire_id, 'vendeur', x.ord::int,
           CASE WHEN (x.v ->> 'app_contact_id') ~ '^[0-9]+$' THEN (x.v ->> 'app_contact_id')::bigint END,
           nullif(btrim(coalesce(x.v ->> 'id', '')), ''),
           false, (btrim(coalesce(x.v ->> 'nom', '')) = ''), coalesce(l.present_in_hektor, false)
      FROM jsonb_array_elements(CASE jsonb_typeof(l.mandants_json)
                                     WHEN 'array'  THEN l.mandants_json
                                     WHEN 'object' THEN jsonb_build_array(l.mandants_json)
                                     ELSE '[]'::jsonb END) WITH ORDINALITY x(v, ord)
     WHERE jsonb_typeof(x.v) = 'object'
    UNION ALL
    SELECT l.app_affaire_id, 'notaire_acquereur', 1, l.notaire_acquereur_id::bigint,
           (SELECT c.hektor_target_id FROM app_contact_current c WHERE c.hektor_contact_id = l.notaire_acquereur_id),
           false, false, coalesce(l.present_in_hektor, false)
     WHERE coalesce(l.notaire_acquereur_id, '') ~ '^[0-9]+$'
    UNION ALL
    SELECT l.app_affaire_id, 'notaire_vendeur', 1, l.notaire_mandant_id::bigint,
           (SELECT c.hektor_target_id FROM app_contact_current c WHERE c.hektor_contact_id = l.notaire_mandant_id),
           false, false, coalesce(l.present_in_hektor, false)
     WHERE coalesce(l.notaire_mandant_id, '') ~ '^[0-9]+$'
$c$;

-- ── 4. LE DECLENCHEUR : il recalcule les parties de LA transaction qui change -- et n'echoue jamais ──────
create or replace function public.app_affaire_partie_suivre()
returns trigger language plpgsql security definer set search_path = public
as $t$
begin
    begin
        if tg_op in ('UPDATE', 'DELETE') then
            delete from public.app_affaire_partie
             where app_affaire_id = old.app_affaire_id and origine = 'listes_du_registre';
        end if;
        if tg_op in ('INSERT', 'UPDATE') then
            if tg_op = 'INSERT' then
                delete from public.app_affaire_partie
                 where app_affaire_id = new.app_affaire_id and origine = 'listes_du_registre';
            end if;
            insert into public.app_affaire_partie (app_affaire_id, role, rang, app_contact_id, hektor_contact_id, est_principal, fiche_sans_nom, transaction_presente)
            select app_affaire_id, role, rang, app_contact_id, hektor_contact_id, est_principal, fiche_sans_nom, transaction_presente from public.app_affaire_partie_calculer(new);
        end if;
    exception when others then
        -- ⛔ JAMAIS d'echec pour l'ecrivain (la nuit, le worker, un geste de l'app) : on note, la sentinelle sonnera.
        begin
            insert into public.app_affaire_partie_erreur (app_affaire_id, erreur)
            values (coalesce(new.app_affaire_id, old.app_affaire_id), tg_op || ' : ' || sqlerrm);
        exception when others then
            raise warning 'app_affaire_partie_suivre : % (journal impossible : %)', sqlerrm, sqlerrm;
        end;
    end;
    return null;
end
$t$;

drop trigger if exists app_affaire_partie_apres_insert on public.app_affaire_ledger;
create trigger app_affaire_partie_apres_insert after insert on public.app_affaire_ledger
    for each row execute function public.app_affaire_partie_suivre();
drop trigger if exists app_affaire_partie_apres_update on public.app_affaire_ledger;
-- ⚠ SEULEMENT SI LES PERSONNES CHANGENT : la nuit renvoie les 31 103 transactions, presque toutes inchangees.
create trigger app_affaire_partie_apres_update after update on public.app_affaire_ledger
    for each row when (
           old.acquereurs_json      is distinct from new.acquereurs_json
        or old.mandants_json        is distinct from new.mandants_json
        or old.app_contact_id       is distinct from new.app_contact_id
        or old.hektor_acquereur_id  is distinct from new.hektor_acquereur_id
        or old.notaire_acquereur_id is distinct from new.notaire_acquereur_id
        or old.notaire_mandant_id   is distinct from new.notaire_mandant_id
        or old.present_in_hektor    is distinct from new.present_in_hektor
        or old.app_affaire_id       is distinct from new.app_affaire_id)
    execute function public.app_affaire_partie_suivre();
drop trigger if exists app_affaire_partie_apres_delete on public.app_affaire_ledger;
create trigger app_affaire_partie_apres_delete after delete on public.app_affaire_ledger
    for each row execute function public.app_affaire_partie_suivre();

-- ── 5. LA RECONSTRUCTION (tout, a l'identique) ─────────────────────────────────────────────────────────
create or replace function public.app_affaire_partie_reconstruire()
returns integer language plpgsql security definer set search_path = public
as $r$
declare n integer;
begin
    delete from public.app_affaire_partie where origine = 'listes_du_registre';
    insert into public.app_affaire_partie (app_affaire_id, role, rang, app_contact_id, hektor_contact_id, est_principal, fiche_sans_nom, transaction_presente)
    select q.app_affaire_id, q.role, q.rang, q.app_contact_id, q.hektor_contact_id, q.est_principal, q.fiche_sans_nom, q.transaction_presente
      from public.app_affaire_ledger l cross join lateral public.app_affaire_partie_calculer(l) q;
    get diagnostics n = row_count;
    return n;
end
$r$;
revoke all on function public.app_affaire_partie_reconstruire() from public, anon, authenticated;
revoke all on function public.app_affaire_partie_suivre() from public, anon, authenticated;

-- ── 6. LA SENTINELLE : la table contre un recalcul complet (+ les erreurs du declencheur des 24 dernieres heures) ──
-- ⚠ Le numero de HEKTOR d'un notaire vient de l'annuaire (refait chaque nuit) : on ne le compare pas, il peut arriver plus tard.
create or replace view public.app_v_affaire_partie_ecarts with (security_invoker = true) as
with attendu as (
    select q.app_affaire_id, q.role, q.rang, q.app_contact_id,
           case when q.role like 'notaire%' then null else q.hektor_contact_id end as hektor_contact_id,
           q.est_principal, q.fiche_sans_nom, q.transaction_presente
      from public.app_affaire_ledger l cross join lateral public.app_affaire_partie_calculer(l) q),
reel as (
    select p.app_affaire_id, p.role, p.rang, p.app_contact_id,
           case when p.role like 'notaire%' then null else p.hektor_contact_id end as hektor_contact_id,
           p.est_principal, p.fiche_sans_nom, p.transaction_presente
      from public.app_affaire_partie p where p.origine = 'listes_du_registre')
select 'manquante'::text as ecart, m.app_affaire_id, m.role, m.rang, m.app_contact_id, null::text as detail
  from (select * from attendu except select * from reel) m
union all
select 'en_trop', t.app_affaire_id, t.role, t.rang, t.app_contact_id, null
  from (select * from reel except select * from attendu) t
union all
select 'erreur_du_declencheur', e.app_affaire_id, null, null, null, e.erreur
  from public.app_affaire_partie_erreur e where e.le > now() - interval '24 hours';
revoke all on public.app_v_affaire_partie_ecarts from anon, authenticated;
grant select on public.app_v_affaire_partie_ecarts to service_role;

-- ── 7. LE REMPLISSAGE ──────────────────────────────────────────────────────────────────────────────────
select public.app_affaire_partie_reconstruire() as parties_posees;

-- ── 8. LA VUE DES LIENS D'UN CONTACT : la branche des acquereurs lit la table des parties ──────────────
DO $vue$
DECLARE
    d       text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    ancre   text := E'\nUNION ALL\n SELECT c.relation_key,';
    neuve   text := $b$ SELECT (('aff_'::text || (l.app_affaire_id)::text) || '_'::text) || (p.app_contact_id)::text AS relation_key,
    (p.app_contact_id)::text AS hektor_contact_id,
    (l.hektor_annonce_id)::text AS hektor_annonce_id,
    l.app_dossier_id,
    b.numero_dossier,
    l.numero_mandat,
    b.titre_bien,
    'acquereur_'::text || l.kind AS role_contact,
    k.date_maj AS contact_date_maj,
    'registre_transactions'::text AS relation_source,
    l.kind AS transaction_type,
    l.hektor_affaire_id AS transaction_id,
        CASE
            WHEN (l.kind = 'vente'::text) THEN 'vente'::text
            ELSE l.state
        END AS transaction_state,
    l.date AS transaction_date,
        CASE
            WHEN (l.kind = 'offre'::text) THEN NULL::text
            ELSE l.montant
        END AS transaction_amount,
    (NOT (EXISTS ( SELECT 1
           FROM app_archive_annonce_index_current x
          WHERE (x.hektor_annonce_id = l.hektor_annonce_id)))) AS is_active_annonce,
    (l.last_seen_at)::text AS last_seen_at,
    (l.last_seen_at)::text AS refreshed_at
   FROM (((app_affaire_partie p
     JOIN app_affaire_ledger l ON ((l.app_affaire_id = p.app_affaire_id)))
     LEFT JOIN app_contact_current k ON ((k.hektor_contact_id = (p.app_contact_id)::text)))
     LEFT JOIN LATERAL ( SELECT s.numero_dossier,
            s.titre_bien
           FROM ( SELECT d.numero_dossier,
                    d.titre_bien,
                    1 AS rang
                   FROM app_dossiers_current d
                  WHERE (d.hektor_annonce_id = l.hektor_annonce_id)
                UNION ALL
                 SELECT a.numero_dossier,
                    a.titre_bien,
                    2
                   FROM app_archive_annonce_index_current a
                  WHERE (a.hektor_annonce_id = l.hektor_annonce_id)
                UNION ALL
                 SELECT h.numero_dossier,
                    h.titre_bien,
                    3
                   FROM app_historical_annonce_index_current h
                  WHERE (h.hektor_annonce_id = l.hektor_annonce_id)) s
          ORDER BY s.rang
         LIMIT 1) b ON (true))
  WHERE ((p.role = 'acquereur'::text) AND p.transaction_presente AND (p.app_contact_id IS NOT NULL))$b$;
    p       int;
BEGIN
    IF position('app_affaire_partie' in d) > 0 THEN
        RAISE NOTICE '%', 'La vue lit deja la table des parties : rien a faire.';
        RETURN;
    END IF;
    IF md5(d) <> 'acf77be8aefe5d619f904a037871eb54' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis le 26/10 (empreinte %s au lieu de acf77be8...) ; rien n''est ecrit.', md5(d));
    END IF;
    IF (length(d) - length(replace(d, E'\nUNION ALL\n', ''))) / length(E'\nUNION ALL\n') <> 1
       OR (length(d) - length(replace(d, ancre, ''))) / length(ancre) <> 1 THEN
        RAISE EXCEPTION '%', 'ARRET : la branche des acquereurs n''est pas trouvee une seule fois ; rien n''est ecrit.';
    END IF;
    p := position(ancre in d);
    d := left(d, p - 1) || E'\nUNION ALL\n' || neuve;
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;
END
$vue$;

COMMIT;

SELECT 1 AS "#", 'la table, le journal, les trois declencheurs existent' AS controle,
       CASE WHEN to_regclass('public.app_affaire_partie') IS NOT NULL AND to_regclass('public.app_affaire_partie_erreur') IS NOT NULL
             AND (SELECT count(*) FROM pg_trigger WHERE tgrelid = 'public.app_affaire_ledger'::regclass AND tgname LIKE 'app_affaire_partie_%') = 3
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'environ 117 000 parties posees (26/10)',
       (SELECT CASE WHEN count(*) BETWEEN 110000 AND 125000 THEN 'OK (' || count(*) || ')' ELSE '⚠ A REGARDER (' || count(*) || ')' END FROM public.app_affaire_partie)
UNION ALL SELECT 3, 'la sentinelle ne voit aucun ecart',
       (SELECT CASE WHEN count(*) = 0 THEN 'OK' ELSE '⛔ ECHEC (' || count(*) || ')' END FROM public.app_v_affaire_partie_ecarts)
UNION ALL SELECT 4, 'la vue lit la table des parties, et reste security_invoker',
       CASE WHEN position('app_affaire_partie' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) > 0
             AND position('app_contact_relation_current' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) = 0
             AND (SELECT reloptions FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass) @> array['security_invoker=true']
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'les liens acquereurs de la vue : 35 008 attendus le 26/10',
       (SELECT CASE WHEN count(*) BETWEEN 34500 AND 36000 THEN 'OK (' || count(*) || ')' ELSE '⚠ A REGARDER (' || count(*) || ')' END
          FROM public.app_contact_relations_current WHERE role_contact LIKE 'acquereur%')
UNION ALL SELECT 6, 'la table n''est ouverte a personne en ecriture',
       CASE WHEN NOT has_table_privilege('authenticated', 'public.app_affaire_partie', 'INSERT')
             AND NOT has_table_privilege('authenticated', 'public.app_affaire_partie', 'UPDATE')
             AND NOT has_table_privilege('authenticated', 'public.app_affaire_partie', 'DELETE')
             AND NOT has_table_privilege('anon', 'public.app_affaire_partie', 'SELECT')
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;
