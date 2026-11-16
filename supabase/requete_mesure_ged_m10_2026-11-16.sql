-- ═══════════════════════════════════════════════════════════════════════════════
-- GED MORCEAU 10 (lot 10c) : LE COMPTE RENDU DE LA MESURE -- LECTURE SEULE                16/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- À relancer au bout des deux semaines (et quand on veut). N'écrit rien. Note du chantier §12.20.
-- On compte le jugement LE PLUS RÉCENT de chaque ligne (une ligne rejugée ne compte qu'une fois).
-- Lecture d'une règle : beaucoup de « faux » -> resserrer ou retirer ; beaucoup de « déjà su » -> elle n'apprend rien
-- (la passer en information, ou la retirer) ; des « vrai » -> elle sert.

-- ① LES LIGNES « À REGARDER », RÈGLE PAR RÈGLE
with derniers as (
  select distinct on (hektor_annonce_id, cle) hektor_annonce_id, regle, cle, niveau, verdict, juge_le
    from public.app_ged_jugement
   order by hektor_annonce_id, cle, juge_le desc
)
select regle,
       count(*)                                        as lignes_jugees,
       count(distinct hektor_annonce_id)               as biens,
       count(*) filter (where verdict = 'vrai')        as vrai,
       count(*) filter (where verdict = 'faux')        as faux,
       count(*) filter (where verdict = 'deja_su')     as deja_su,
       round(100.0 * count(*) filter (where verdict = 'faux') / nullif(count(*), 0))    as pct_faux,
       round(100.0 * count(*) filter (where verdict = 'deja_su') / nullif(count(*), 0)) as pct_deja_su,
       min(juge_le)::date as premier, max(juge_le)::date as dernier
  from derniers
 group by regle
 order by lignes_jugees desc, regle;

-- ② LES « FAUX », mot pour mot (pour voir POURQUOI une règle se trompe)
with derniers as (
  select distinct on (hektor_annonce_id, cle) hektor_annonce_id, regle, cle, texte, verdict, commentaire, juge_le
    from public.app_ged_jugement
   order by hektor_annonce_id, cle, juge_le desc
)
select regle, hektor_annonce_id, texte, commentaire, juge_le::date
  from derniers where verdict = 'faux'
 order by regle, juge_le desc;

-- ③ LES PROPOSITIONS « REMPLIR » (morceau 8 et lot 9c) : la décision la plus récente de chaque proposition
with derniers as (
  select distinct on (hektor_annonce_id, cle, valeur) hektor_annonce_id, cle, decision
    from public.app_ged_decision
   order by hektor_annonce_id, cle, valeur, decide_le desc
)
select split_part(cle, '.', 1) as proposition, count(*) as decisions,
       count(*) filter (where decision = 'remplie') as remplies,
       count(*) filter (where decision = 'ignoree') as ignorees,
       count(*) filter (where decision = 'echec')   as echecs
  from derniers
 group by 1 order by decisions desc;

-- ④ LES LECTURES PAR L'IA, type par type (qualité et coût) -- hors biens d'essai connus
select l.type_code,
       count(*)                                        as lectures,
       count(*) filter (where l.etat = 'lu')           as lues,
       count(*) filter (where l.etat = 'incomplet')    as incompletes,
       count(*) filter (where l.etat = 'pas_ce_type')  as pas_ce_type,
       round(sum(coalesce(l.cout_usd, 0))::numeric, 4) as cout_usd
  from public.app_ged_lecture l
 where l.hektor_annonce_id not in ('62774', '63331', '61398')
 group by l.type_code
 order by lectures desc;
