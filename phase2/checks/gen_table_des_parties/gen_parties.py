import sys
S = sys.argv[1]
calc = open(S + r"\parties_calcul.sql", encoding="utf-8").read().replace("\r", "")
calc = "\n".join(x for x in calc.splitlines() if not x.lstrip().startswith("--")).rstrip()
branche = open(S + r"\parties_branche_vue.sql", encoding="utf-8").read().replace("\r", "").rstrip("\n")
assert "$c$" not in calc and "$b$" not in branche
EMP = "acf77be8aefe5d619f904a037871eb54"
ANCRE = "E'\\nUNION ALL\\n SELECT c.relation_key,'"
NL = "E'\\nUNION ALL\\n'"
ANCIENNE = ("\nUNION ALL\n SELECT c.relation_key,\n    c.hektor_contact_id,\n    c.hektor_annonce_id,\n    c.app_dossier_id,\n"
            "    c.numero_dossier,\n    c.numero_mandat,\n    c.titre_bien,\n    c.role_contact,\n    c.contact_date_maj,\n"
            "    c.relation_source,\n    c.transaction_type,\n    c.transaction_id,\n    c.transaction_state,\n    c.transaction_date,\n"
            "    c.transaction_amount,\n    c.is_active_annonce,\n    c.last_seen_at,\n    (c.refreshed_at)::text AS refreshed_at\n"
            "   FROM app_contact_relation_current c\n  WHERE (c.role_contact ~~ 'acquereur%'::text);")
COLS = "app_affaire_id, role, rang, app_contact_id, hektor_contact_id, est_principal, fiche_sans_nom, transaction_presente"

corps = f"""
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
language sql stable
-- ⚠ PAS de « set search_path » ici, et c'est VOULU : avec lui, Postgres ne peut pas DEPLIER la fonction dans la requete
--   et l'appelle ligne par ligne -- la sentinelle passait de 1,4 s a 4,1 s (7,4 s par l'API, limite 8 s). Les tables
--   sont donc nommees avec leur schema (public.).
as $c$
{calc}
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
            insert into public.app_affaire_partie ({COLS})
            select {COLS} from public.app_affaire_partie_calculer(new);
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
    insert into public.app_affaire_partie ({COLS})
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
select case when r.app_affaire_id is null then 'manquante'
            when a.app_affaire_id is null then 'en_trop'
            else 'differente' end::text as ecart,
       coalesce(a.app_affaire_id, r.app_affaire_id) as app_affaire_id,
       coalesce(a.role, r.role) as role,
       coalesce(a.rang, r.rang) as rang,
       coalesce(a.app_contact_id, r.app_contact_id) as app_contact_id,
       null::text as detail
  from attendu a full join reel r
    on r.app_affaire_id = a.app_affaire_id and r.role = a.role and r.rang = a.rang
 where a.app_affaire_id is null or r.app_affaire_id is null
    or (a.app_contact_id, a.hektor_contact_id, a.est_principal, a.fiche_sans_nom, a.transaction_presente)
       is distinct from (r.app_contact_id, r.hektor_contact_id, r.est_principal, r.fiche_sans_nom, r.transaction_presente)
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
    ancre   text := {ANCRE};
    neuve   text := $b${branche}$b$;
    p       int;
BEGIN
    IF position('app_affaire_partie' in d) > 0 THEN
        RAISE NOTICE '%', 'La vue lit deja la table des parties : rien a faire.';
        RETURN;
    END IF;
    IF md5(d) <> '{EMP}' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis le 26/10 (empreinte %s au lieu de acf77be8...) ; rien n''est ecrit.', md5(d));
    END IF;
    IF (length(d) - length(replace(d, {NL}, ''))) / length({NL}) <> 1
       OR (length(d) - length(replace(d, ancre, ''))) / length(ancre) <> 1 THEN
        RAISE EXCEPTION '%', 'ARRET : la branche des acquereurs n''est pas trouvee une seule fois ; rien n''est ecrit.';
    END IF;
    p := position(ancre in d);
    d := left(d, p - 1) || {NL} || neuve;
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;
END
$vue$;
"""

controles = """
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
"""

entete = """-- ═══════════════════════════════════════════════════════════════════════════
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
"""

patch = entete + "\nBEGIN;\n" + corps + "\nCOMMIT;\n" + controles

inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ types : la table des parties                                          26/10/2026
-- 1. la vue des liens d'un contact reprend sa définition d'avant À L'OCTET (empreinte acf77be8 vérifiée) ;
-- 2. les déclencheurs, les fonctions, la vue de la sentinelle, la table et son journal sont retirés.
-- La table est DÉRIVÉE des listes du registre : rien n'est perdu. ⚠ Retirer AUSSI la sentinelle du moniteur
-- (data.affaire_partie_ecart, monitoring/check_gti_health.py) : sinon elle lira une vue absente (un rouge).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $vue$
DECLARE
    d         text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    ancienne  text := $b${ANCIENNE}$b$;
    p         int;
BEGIN
    IF position('app_affaire_partie' in d) = 0 THEN
        RAISE NOTICE '%', 'La vue ne lit pas la table des parties : rien a retirer.';
        RETURN;
    END IF;
    p := position({NL} in d);
    IF p = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : frontiere des branches introuvable ; rien n''est ecrit.';
    END IF;
    d := left(d, p - 1) || ancienne;
    IF md5(d) <> '{EMP}' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue reconstituee n''a pas l''empreinte d''avant (%s) ; rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || rtrim(rtrim(d), ';');
END
$vue$;

drop trigger if exists app_affaire_partie_apres_insert on public.app_affaire_ledger;
drop trigger if exists app_affaire_partie_apres_update on public.app_affaire_ledger;
drop trigger if exists app_affaire_partie_apres_delete on public.app_affaire_ledger;
drop view if exists public.app_v_affaire_partie_ecarts;
drop function if exists public.app_affaire_partie_reconstruire();
drop function if exists public.app_affaire_partie_suivre();
drop function if exists public.app_affaire_partie_calculer(public.app_affaire_ledger);
drop table if exists public.app_affaire_partie;
drop table if exists public.app_affaire_partie_erreur;

COMMIT;

SELECT 1 AS "#", 'la vue a retrouve sa definition d''avant' AS controle,
       CASE WHEN md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)) = '{EMP}' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'plus aucun declencheur sur le registre',
       CASE WHEN (SELECT count(*) FROM pg_trigger WHERE tgrelid = 'public.app_affaire_ledger'::regclass AND tgname LIKE 'app_affaire_partie_%') = 0 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'la table et son journal sont retires',
       CASE WHEN to_regclass('public.app_affaire_partie') IS NULL AND to_regclass('public.app_affaire_partie_erreur') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;
"""

repetition = """-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ types : la table des parties                                              26/10/2026
-- Lecture seule. À rejouer après la pose, puis le lendemain de la première nuit.
-- ═══════════════════════════════════════════════════════════════════════════
WITH
neuf AS (SELECT * FROM public.app_contact_relations_current WHERE relation_source = 'registre_transactions'),
nuit AS (SELECT * FROM public.app_contact_relation_current WHERE role_contact LIKE 'acquereur%'),
j AS (SELECT n.*, v.relation_key vk, v.transaction_state vs, v.transaction_date vd, v.transaction_amount va,
             v.is_active_annonce vact, v.app_dossier_id vdos
        FROM nuit n LEFT JOIN neuf v ON v.hektor_contact_id = n.hektor_contact_id AND v.hektor_annonce_id = n.hektor_annonce_id
                                    AND v.role_contact = n.role_contact AND v.transaction_id = n.transaction_id)
SELECT 1 AS "#", 'la sentinelle ne voit aucun ecart (table contre recalcul, erreurs du declencheur)' AS controle,
       (SELECT CASE WHEN count(*) = 0 THEN 'OK' ELSE '⛔ ECHEC (' || count(*) || ')' END FROM public.app_v_affaire_partie_ecarts) AS verdict
UNION ALL SELECT 2, 'les parties par role',
       (SELECT string_agg(role || ' ' || n, ' · ' ORDER BY role) FROM (SELECT role, count(*) n FROM public.app_affaire_partie GROUP BY 1) x)
UNION ALL SELECT 3, 'chaque lien acquereur de la nuit se retrouve dans la vue',
       (SELECT CASE WHEN count(*) = count(vk) THEN 'OK (' || count(vk) || ' sur ' || count(*) || ')'
                    ELSE '⛔ ECHEC (' || count(vk) || ' sur ' || count(*) || ')' END FROM j)
UNION ALL SELECT 4, 'aucune cle en double dans la vue neuve',
       (SELECT CASE WHEN count(*) = count(DISTINCT relation_key) THEN 'OK' ELSE '⛔ ECHEC' END FROM neuf)
UNION ALL SELECT 5, 'dossier, etat, date, montant, bien actif : identiques a la nuit',
       (SELECT CASE WHEN count(*) FILTER (WHERE vk IS NOT NULL AND (vdos IS DISTINCT FROM app_dossier_id OR vs IS DISTINCT FROM transaction_state
                    OR vd IS DISTINCT FROM transaction_date OR va IS DISTINCT FROM transaction_amount OR vact IS DISTINCT FROM is_active_annonce)) = 0
                    THEN 'OK' ELSE '⛔ ECHEC' END FROM j)
UNION ALL SELECT 6, 'la branche des mandants / proprietaires est inchangee',
       CASE WHEN (SELECT count(*) FROM public.app_contact_relations_current WHERE relation_source <> 'registre_transactions')
                 = (SELECT count(*) FROM public.app_relation r WHERE (r.present_in_hektor OR (r.source = 'app' AND r.absent_depuis IS NULL)) AND r.retire_le IS NULL)
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 7, 'vendeurs sans notre numero (58 550 le 26/10 ; ~36 apres la nuit du 27/10, C4 allume)',
       (SELECT count(*)::text FROM public.app_affaire_partie WHERE role = 'vendeur' AND app_contact_id IS NULL)
ORDER BY 1;
-- LE TEMPS : explain analyze select * from public.app_contact_relations_current where hektor_contact_id = '10354701';
"""

base = r"C:\Hektor\Projet\supabase\patch_table_des_parties_2026-10-26"
for suf, txt in (("", patch), ("_INVERSE", inverse), ("_REPETITION", repetition)):
    open(base + suf + ".sql", "w", encoding="utf-8", newline="\n").write(txt)
# la version d'ESSAI : le meme corps, mais ROLLBACK a la fin (et les essais au milieu, ajoutes a part)
open(S + r"\parties_corps.sql", "w", encoding="utf-8", newline="\n").write(corps)
open(S + r"\parties_controles.sql", "w", encoding="utf-8", newline="\n").write(controles)
print("ecrits")
