-- ═══════════════════════════════════════════════════════════════════════════
-- REPETITION : la pose des colonnes d'annulation, JOUEE PUIS ANNULEE  10/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Elle tourne DANS UNE TRANSACTION QUI FINIT PAR ROLLBACK : rien n'est pose.
-- Elle sert a repondre a une seule question AVANT la vraie pose : le patch
-- fait-il ce qu'il dit, et rien d'autre ?
--
--   a coller tel quel. Il doit rendre 6 lignes, toutes OK.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

create temporary table resultat_repetition (ordre int, controle text, verdict text) on commit drop;

-- ─── ① L'ETAT DE DEPART : les deux colonnes ne doivent PAS exister ──────────
insert into resultat_repetition
select 1, '① avant la pose : les deux colonnes sont absentes',
       case when count(*) = 0 then 'OK  (0 colonne)' else 'ECHEC  (' || count(*) || ' deja la)' end
from information_schema.columns
where table_schema = 'public' and table_name = 'app_affaire_ledger'
  and column_name in ('date_annulation_app', 'motif_annulation_app');

-- ─── LA POSE, a l'identique du patch ───────────────────────────────────────
alter table public.app_affaire_ledger
  add column if not exists date_annulation_app  text,
  add column if not exists motif_annulation_app text;

-- ─── ② LES DEUX COLONNES SONT LA, EN text, NULLABLES ───────────────────────
insert into resultat_repetition
select 2, '② apres la pose : 2 colonnes text nullables',
       case when count(*) = 2 then 'OK  (2 colonnes text, nullables)'
            else 'ECHEC  (' || count(*) || ')' end
from information_schema.columns
where table_schema = 'public' and table_name = 'app_affaire_ledger'
  and column_name in ('date_annulation_app', 'motif_annulation_app')
  and data_type = 'text' and is_nullable = 'YES';

-- ─── ③ TEMOIN POSITIF : les 3 autres colonnes _app sont INTACTES ───────────
insert into resultat_repetition
select 3, '③ temoin positif : les 3 autres colonnes _app intactes',
       case when count(*) = 3 then 'OK  (3 colonnes _app d''avant)'
            else 'ECHEC  (' || count(*) || ' au lieu de 3)' end
from information_schema.columns
where table_schema = 'public' and table_name = 'app_affaire_ledger'
  and column_name in ('charge_commission_app', 'honoraires_entree_app', 'honoraires_sortie_app');

-- ─── ④ LE PATCH NE REMPLIT RIEN : les deux colonnes sont vides partout ─────
insert into resultat_repetition
select 4, '④ le patch ne remplit rien : 0 valeur posee',
       case when count(*) = 0 then 'OK  (0 ligne portee)'
            else 'ECHEC  (' || count(*) || ' lignes portent une valeur)' end
from public.app_affaire_ledger
where date_annulation_app is not null or motif_annulation_app is not null;

-- ─── ⑤ AUCUNE LIGNE N'A DISPARU -- un ALTER ne touche pas les donnees, mais
--     on le VERIFIE plutot que de le supposer (31 145 attendues) ────────────
insert into resultat_repetition
select 5, '⑤ le registre garde toutes ses lignes',
       case when count(*) >= 31000 then 'OK  (' || count(*) || ' lignes)'
            else 'A REGARDER  (' || count(*) || ' lignes)' end
from public.app_affaire_ledger;

-- ─── ⑥ UNE ECRITURE D'ESSAI PASSE, ET LA CONTRAINTE text ACCEPTE `0000-00-00`
--     C'est la raison meme du choix de `text` : on l'eprouve ici. ────────────
do $$
declare
  cible bigint;
begin
  select app_affaire_id into cible from public.app_affaire_ledger
   where app_chaine_id is not null order by app_affaire_id limit 1;
  update public.app_affaire_ledger
     set date_annulation_app = '0000-00-00',
         motif_annulation_app = 'essai de repetition -- annule par le rollback'
   where app_affaire_id = cible;
end $$;

insert into resultat_repetition
select 6, '⑥ `0000-00-00` est accepte (c''est pourquoi la colonne est en text)',
       case when count(*) = 1 then 'OK  (la date vide de Hektor passe)'
            else 'ECHEC  (elle a ete refusee)' end
from public.app_affaire_ledger
where date_annulation_app = '0000-00-00';

select controle, verdict from resultat_repetition order by ordre;

rollback;   -- ⛔ RIEN N'EST POSE : la repetition ne laisse aucune trace.
