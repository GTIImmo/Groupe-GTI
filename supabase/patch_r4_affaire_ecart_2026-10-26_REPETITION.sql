-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE R4 — les écarts du carnet et la réponse de l'humain — TOUT EST ANNULÉ        26/10/2026
-- Fichier GÉNÉRÉ (phase2/checks/gen_patch_r4_affaire_ecart.py).
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … ». Elle pose LE VRAI PATCH, fabrique des lignes de carnet
-- d'essai sur les transactions d'essai de 24113 (compromis 1001394, offre 1001393), joue la fonction comme un
-- admin puis comme un non-admin, puis LE VRAI RETOUR ARRIÈRE. Rien ne reste.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

DO $garde$
BEGIN
    IF to_regclass('public.app_affaire_carnet_decision') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la table app_affaire_carnet_decision existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regclass('public.app_v_affaire_carnet_ecarts') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la vue app_v_affaire_carnet_ecarts existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regprocedure('public.app_affaire_carnet_ecart_trancher(bigint,text,text)') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction app_affaire_carnet_ecart_trancher existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regclass('public.app_affaire_champ_app') IS NULL OR to_regprocedure('public.app_console_current_role()') IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : le carnet ou app_console_current_role() manque. Rien n''est ecrit.';
    END IF;
END
$garde$;

-- 1. LES DÉCISIONS DE L'HUMAIN — une table à part : le carnet n'est pas touché (il a déjà quatre écrivains :
--    la création, la modification, R3, R2). « Une saisie ne se perd jamais » : quand l'humain prend la
--    valeur de Hektor, notre saisie est RANGÉE ici avant d'être retirée du carnet.
create table public.app_affaire_carnet_decision (
  id              bigserial primary key,
  app_affaire_id  bigint      not null,
  champ           text        not null,
  ecrit_le        timestamptz,                  -- la saisie DÉCIDÉE : une saisie réécrite après sonne de nouveau
  decision        text        not null check (decision in ('hektor', 'app', 'attendre')),
  valeur_app      text,                         -- notre valeur, telle que le carnet la portait
  valeur_hektor   text,                         -- celle que R3 a relue chez Hektor
  etat            text,                         -- le verdict au moment de la décision
  origine         text,
  decide_le       timestamptz not null default now(),
  decide_par      uuid
);
create index app_affaire_carnet_decision_ligne on public.app_affaire_carnet_decision (app_affaire_id, champ);
comment on table public.app_affaire_carnet_decision is
  'Chantier 8 / R4 (26/10/2026) : la reponse de l''humain a un ecart du carnet des transactions (conflit, echec, attente de plus de 48 h). hektor = notre saisie rangee ici puis retiree du carnet (la nuit reprend Hektor) ; app = on garde la notre (l''alerte se tait) ; attendre = idem pour une attente. Ecrite uniquement par app_affaire_carnet_ecart_trancher.';
alter table public.app_affaire_carnet_decision enable row level security;
revoke all on public.app_affaire_carnet_decision from public, anon, authenticated;
revoke all on sequence public.app_affaire_carnet_decision_id_seq from public, anon, authenticated;
grant select on public.app_affaire_carnet_decision to authenticated;
grant select, insert, update, delete on public.app_affaire_carnet_decision to service_role;
create policy app_affaire_carnet_decision_lecture on public.app_affaire_carnet_decision
  for select to authenticated using (public.is_app_user_active());

-- 2. LES ÉCARTS — une ligne par transaction ET par champ, jamais « N sur M » (leçon du 14/10).
--    Une saisie PARTIE chez Hektor (création ou modification) dont le verdict est « conflit » ou « échec »,
--    ou « en attente » / « inconnu » depuis plus de 48 h (le rattrapage de R3 passe chaque matin : après deux
--    matins, la preuve n'arrivera pas seule). a_traiter = aucune décision pour CETTE saisie (cet ecrit_le).
--    security_invoker : elle ne montre que ce que le lecteur a déjà le droit de lire (carnet, registre).
create view public.app_v_affaire_carnet_ecarts
  with (security_invoker = true) as
select c.app_affaire_id, l.kind, l.hektor_annonce_id, l.hektor_affaire_id, c.champ,
       c.valeur_app, c.valeur_hektor_relue as valeur_hektor, c.etat, c.origine, c.ecrit_le, c.constate_le,
       case when c.etat in ('conflit', 'echec') then c.etat else 'attente_longue' end as ecart,
       d.decision, d.decide_le,
       (d.id is null) as a_traiter
  from public.app_affaire_champ_app c
  join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id
  left join lateral (
        select x.id, x.decision, x.decide_le
          from public.app_affaire_carnet_decision x
         where x.app_affaire_id = c.app_affaire_id and x.champ = c.champ
           and x.ecrit_le is not distinct from c.ecrit_le
         order by x.decide_le desc
         limit 1) d on true
 where c.origine in ('creation_app', 'modification_app')
   and (c.etat in ('conflit', 'echec')
        or (c.etat in ('en_attente', 'inconnu') and c.ecrit_le < now() - interval '48 hours'));
comment on view public.app_v_affaire_carnet_ecarts is
  'Chantier 8 / R4 (26/10/2026) : les ecarts du carnet des transactions, une ligne par champ. Lue par la sentinelle data.affaire_ecart (a_traiter) et par la rubrique Affaires (les deux gestes).';
revoke all on public.app_v_affaire_carnet_ecarts from public, anon;
grant select on public.app_v_affaire_carnet_ecarts to authenticated, service_role;

-- 3. LA RÉPONSE DE L'HUMAIN — admin seulement.
--    hektor   : la saisie est rangée, puis RETIRÉE du carnet -> R2 ne la protège plus, l'écran retombe sur le
--               registre, la nuit met la valeur de Hektor. Rien n'est envoyé chez Hektor.
--    app      : (conflit, échec) la décision est rangée, l'alerte se tait ; la saisie reste, R2 la protège.
--               Corriger AUSSI Hektor, c'est le geste « Modifier », quand il est disponible.
--    attendre : (attente) la décision est rangée, l'alerte se tait ; R3 continue d'essayer chaque matin.
create or replace function public.app_affaire_carnet_ecart_trancher(p_app_affaire_id bigint, p_champ text, p_decision text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  c public.app_affaire_champ_app%rowtype;
  v_id bigint;
begin
  if coalesce(public.app_console_current_role(), '') <> 'admin' then
    raise exception 'admin_requis' using errcode = '42501';
  end if;
  if p_decision is null or p_decision not in ('hektor', 'app', 'attendre') then
    raise exception 'decision_inconnue' using errcode = '22023';
  end if;
  select * into c from public.app_affaire_champ_app
   where app_affaire_id = p_app_affaire_id and champ = p_champ
   for update;
  if not found then
    raise exception 'ligne_introuvable' using errcode = '22023';
  end if;
  if coalesce(c.origine, '') not in ('creation_app', 'modification_app')
     or coalesce(c.etat, '') not in ('conflit', 'echec', 'en_attente', 'inconnu') then
    raise exception 'pas_un_ecart' using errcode = '22023';
  end if;
  if p_decision = 'attendre' and c.etat not in ('en_attente', 'inconnu') then
    raise exception 'attendre_reserve_a_l_attente' using errcode = '22023';
  end if;
  if p_decision = 'app' and c.etat not in ('conflit', 'echec') then
    raise exception 'garder_reserve_au_conflit_et_a_l_echec' using errcode = '22023';
  end if;
  insert into public.app_affaire_carnet_decision
         (app_affaire_id, champ, ecrit_le, decision, valeur_app, valeur_hektor, etat, origine, decide_par)
  values (c.app_affaire_id, c.champ, c.ecrit_le, p_decision, c.valeur_app, c.valeur_hektor_relue, c.etat, c.origine, auth.uid())
  returning id into v_id;
  if p_decision = 'hektor' then
    delete from public.app_affaire_champ_app where app_affaire_id = p_app_affaire_id and champ = p_champ;
  end if;
  return jsonb_build_object('decision_id', v_id, 'decision', p_decision, 'retiree_du_carnet', p_decision = 'hektor');
end
$f$;
revoke all on function public.app_affaire_carnet_ecart_trancher(bigint, text, text) from public, anon;
grant execute on function public.app_affaire_carnet_ecart_trancher(bigint, text, text) to authenticated;

DO $essai$
DECLARE
    v_admin uuid;
    v_autre uuid;
    v_err text;
    v_r jsonb;
    n int;
BEGIN
    SELECT id INTO v_admin FROM public.app_user_profile WHERE is_active AND role::text = 'admin' ORDER BY id LIMIT 1;
    SELECT id INTO v_autre FROM public.app_user_profile WHERE is_active AND role::text <> 'admin' ORDER BY id LIMIT 1;
    IF v_admin IS NULL OR v_autre IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : il faut un admin actif et un non-admin actif pour l''essai.';
    END IF;
    IF (SELECT count(*) FROM public.app_affaire_ledger WHERE app_affaire_id IN (1001393, 1001394)) <> 2 THEN
        RAISE EXCEPTION '%', 'ARRET : les transactions d''essai 1001393 / 1001394 n''existent plus.';
    END IF;

    -- les lignes d'essai (le carnet de 1001394 ne porte aucun de ces champs aujourd'hui)
    delete from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ in ('sequestre', 'montant', 'date_acte', 'date');
    delete from public.app_affaire_champ_app where app_affaire_id = 1001393 and champ = 'montant';
    insert into public.app_affaire_champ_app (app_affaire_id, champ, valeur_app, valeur_hektor_au_moment, valeur_hektor_relue, origine, ecrit_le, etat, constate_le)
    values (1001394, 'sequestre', '6000', null, '5000', 'creation_app', now() - interval '1 hour', 'conflit', now()),
           (1001394, 'montant', '135000', '130000', null, 'modification_app', now() - interval '3 hours', 'echec', now()),
           (1001394, 'date_acte', '2027-01-15', null, null, 'creation_app', now() - interval '72 hours', 'en_attente', now() - interval '20 hours'),
           (1001394, 'date', '2026-10-22', null, null, 'creation_app', now() - interval '2 hours', 'en_attente', now()),
           (1001393, 'montant', '160000', null, '16000', 'saisie_app', now() - interval '5 hours', 'conflit', now());

    SELECT count(*) INTO n FROM public.app_v_affaire_carnet_ecarts WHERE app_affaire_id IN (1001393, 1001394) AND a_traiter;
    insert into _m values (1, 'la vue montre EXACTEMENT conflit + echec + attente > 48 h (3)', case when n = 3
        and exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'sequestre' and ecart = 'conflit' and valeur_hektor = '5000' and kind = 'compromis')
        and exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'montant' and ecart = 'echec')
        and exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'date_acte' and ecart = 'attente_longue')
        then 'OK' else 'ECHEC (' || n || ')' end);
    insert into _m values (2, 'pas dans la vue : attente de 2 h, saisie_app, lignes arrivee / sans objet', case when
        not exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'date')
        and not exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001393 and champ = 'montant')
        and not exists (select 1 from public.app_v_affaire_carnet_ecarts v join public.app_affaire_champ_app c using (app_affaire_id, champ) where c.etat in ('arrivee', 'sans_objet'))
        then 'OK' else 'ECHEC' end);

    -- un NON-admin est refusé
    PERFORM set_config('request.jwt.claim.sub', v_autre::text, true);
    PERFORM set_config('request.jwt.claims', json_build_object('sub', v_autre::text, 'role', 'authenticated')::text, true);
    v_err := '';
    BEGIN
        PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'sequestre', 'hektor');
    EXCEPTION WHEN others THEN v_err := sqlerrm;
    END;
    insert into _m values (3, 'un non-admin est refuse (admin_requis), rien ne bouge', case when v_err = 'admin_requis'
        and exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'sequestre')
        and (select count(*) from public.app_affaire_carnet_decision) = 0 then 'OK' else 'ECHEC (' || v_err || ')' end);

    -- l'admin : « garder la nôtre » sur le conflit
    PERFORM set_config('request.jwt.claim.sub', v_admin::text, true);
    PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin::text, 'role', 'authenticated')::text, true);
    v_r := public.app_affaire_carnet_ecart_trancher(1001394, 'sequestre', 'app');
    insert into _m values (4, '« garder la notre » : decision rangee (par l''admin), la ligne RESTE au carnet, l''alerte se tait', case when
        (v_r->>'retiree_du_carnet')::boolean = false
        and exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'sequestre' and valeur_app = '6000')
        and exists (select 1 from public.app_affaire_carnet_decision where app_affaire_id = 1001394 and champ = 'sequestre' and decision = 'app' and decide_par = v_admin and valeur_hektor = '5000')
        and not exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'sequestre' and a_traiter)
        then 'OK' else 'ECHEC ' || v_r::text end);

    -- la saisie est RÉÉCRITE après la décision : elle sonne de nouveau
    update public.app_affaire_champ_app set valeur_app = '6500', ecrit_le = now() where app_affaire_id = 1001394 and champ = 'sequestre';
    insert into _m values (5, 'une saisie reecrite apres la decision SONNE de nouveau', case when
        exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'sequestre' and a_traiter)
        then 'OK' else 'ECHEC' end);

    -- « prendre la valeur de Hektor » sur l'échec
    v_r := public.app_affaire_carnet_ecart_trancher(1001394, 'montant', 'hektor');
    insert into _m values (6, '« prendre Hektor » : la saisie est RANGEE (valeur, verdict, origine) puis RETIREE du carnet', case when
        (v_r->>'retiree_du_carnet')::boolean = true
        and not exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'montant')
        and exists (select 1 from public.app_affaire_carnet_decision where app_affaire_id = 1001394 and champ = 'montant' and decision = 'hektor'
                    and valeur_app = '135000' and etat = 'echec' and origine = 'modification_app')
        then 'OK' else 'ECHEC ' || v_r::text end);

    -- « attendre encore » sur l'attente longue ; refusé sur un conflit ; « garder » refusé sur une attente
    v_r := public.app_affaire_carnet_ecart_trancher(1001394, 'date_acte', 'attendre');
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'sequestre', 'attendre'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (7, '« attendre » : accepte sur une attente (la ligne reste), refuse sur un conflit', case when
        exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'date_acte')
        and not exists (select 1 from public.app_v_affaire_carnet_ecarts where app_affaire_id = 1001394 and champ = 'date_acte' and a_traiter)
        and v_err = 'attendre_reserve_a_l_attente' then 'OK' else 'ECHEC (' || v_err || ')' end);
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'date_acte', 'app'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (8, '« garder la notre » refuse sur une attente', case when v_err = 'garder_reserve_au_conflit_et_a_l_echec' then 'OK' else 'ECHEC (' || v_err || ')' end);

    -- les refus de forme
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'notaire_id', 'hektor'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (9, 'une ligne « arrivee » n''est pas un ecart (pas_un_ecart), elle reste', case when v_err = 'pas_un_ecart'
        and exists (select 1 from public.app_affaire_champ_app where app_affaire_id = 1001394 and champ = 'notaire_id') then 'OK' else 'ECHEC (' || v_err || ')' end);
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001393, 'montant', 'hektor'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (10, 'une saisie gardee chez nous (saisie_app) n''est pas un ecart', case when v_err = 'pas_un_ecart' then 'OK' else 'ECHEC (' || v_err || ')' end);
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'champ_qui_n_existe_pas', 'hektor'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (11, 'une ligne absente : ligne_introuvable', case when v_err = 'ligne_introuvable' then 'OK' else 'ECHEC (' || v_err || ')' end);
    v_err := '';
    BEGIN PERFORM public.app_affaire_carnet_ecart_trancher(1001394, 'date', 'supprimer'); EXCEPTION WHEN others THEN v_err := sqlerrm; END;
    insert into _m values (12, 'une decision inconnue est refusee', case when v_err = 'decision_inconnue' then 'OK' else 'ECHEC (' || v_err || ')' end);

    -- ce que compterait la sentinelle data.affaire_ecart : a_traiter = la seule ligne reecrite
    SELECT count(*) INTO n FROM public.app_v_affaire_carnet_ecarts WHERE a_traiter AND app_affaire_id IN (1001393, 1001394);
    insert into _m values (13, 'la sentinelle compterait 1 (le sequestre reecrit), rien d''autre', case when n = 1 then 'OK' else 'ECHEC (' || n || ')' end);
END
$essai$;

drop function if exists public.app_affaire_carnet_ecart_trancher(bigint, text, text);
drop view if exists public.app_v_affaire_carnet_ecarts;

DO $garde_decisions$
DECLARE
    n int;
    nom text := 'app_affaire_carnet_decision_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_affaire_carnet_decision') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_affaire_carnet_decision n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_affaire_carnet_decision' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_affaire_carnet_decision';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_affaire_carnet_decision rename to %I', nom);
        RAISE NOTICE '%', format('%s decision(s) gardee(s) sous public.%s (les saisies rangees par « prendre Hektor » y sont)', n, nom);
    END IF;
END
$garde_decisions$;

DO $nettoie$
DECLARE t text;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'app_affaire_carnet_decision_avant_inverse_%' LOOP
        EXECUTE format('drop table public.%I', t);
    END LOOP;
END
$nettoie$;

DO $fin$
DECLARE
    r text;
    ok int;
    total int;
BEGIN
    insert into _m values (14, 'le retour arriere a tout retire, le carnet est intact',
        case when to_regclass('public.app_affaire_carnet_decision') IS NULL
                  AND to_regclass('public.app_v_affaire_carnet_ecarts') IS NULL
                  AND to_regprocedure('public.app_affaire_carnet_ecart_trancher(bigint,text,text)') IS NULL
                  AND to_regclass('public.app_affaire_champ_app') IS NOT NULL
             then 'OK' else 'ECHEC' end);
    select count(*) filter (where valeur = 'OK'), count(*), string_agg(n || ' ' || valeur || ' ' || cle, ' | ' order by n)
      into ok, total, r from _m;
    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s | %s', ok, total, r);
END
$fin$;
