-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DE LA CASCADE DE L'ANNULATION            11/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⭐ IL Y A DEUX NIVEAUX, ET LE PREMIER SUFFIT PRESQUE TOUJOURS.
--
--   NIVEAU 1 -- ETEINDRE (2 secondes, sans toucher au code)
--     La cascade ne s'execute QUE si l'interrupteur vaut 'on'. L'eteindre la rend
--     inerte immediatement : le geste « annuler un compromis » redevient
--     EXACTEMENT ce qu'il etait avant le 11/11.
--     ⭐ C'EST LE RETOUR ARRIERE A PREFERER : rien n'est reecrit, donc rien ne
--       peut etre casse en route.
--
--   NIVEAU 2 -- RETIRER LE CODE (si on veut vraiment la fonction d'avant)
--     Il faut reconstruire app_geste_affaire_optimistic sans le bloc. Le patch
--     n'avait pas a reecrire la fonction : il l'avait LUE puis modifiee. Le retour
--     fait l'inverse, par la meme methode.
--     ⚠ EMPREINTE ATTENDUE APRES : 56df3dbef42cae791bb9d804be270ae3 (10 307 car.)
--
-- ⛔⛔ CE QUE LE RETOUR ARRIERE NE DEFAIT PAS, ET NE PEUT PAS DEFAIRE :
--   les offres DEJA refusees par la cascade. Elles sont refusees chez Hektor,
--   et les remettre « acceptees » serait un geste a part, a decider une par une.
--   ➡ AVANT DE LANCER, SAVOIR COMBIEN :
--     select count(*) from public.app_console_job
--      where job_type = 'change_hektor_offre_status'
--        and payload_json->>'origine' in ('cascade_annulation_compromis',
--                                         'rattrapage_cascade_annulation');
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── NIVEAU 1 : ETEINDRE ───────────────────────────────────────────────────
update public.app_setting
   set value = 'off'
 where key = 'cascade_annulation_compromis';

select 'niveau 1 -- extinction' as controle,
       coalesce((select value from public.app_setting
                  where key = 'cascade_annulation_compromis'), '(absent)') as interrupteur_attendu_off,
       (select count(*) from public.app_console_job
         where job_type = 'change_hektor_offre_status'
           and payload_json->>'origine' in ('cascade_annulation_compromis',
                                            'rattrapage_cascade_annulation')) as offres_deja_refusees_NON_DEFAITES;

-- ─── NIVEAU 2 : RETIRER LE CODE ────────────────────────────────────────────
-- ⛔ A NE LANCER QUE SI LE NIVEAU 1 NE SUFFIT PAS. Decommenter le bloc entier.
/*
do $patch$
declare
  texte text;
  debut int;
  fin   int;
begin
  select pg_get_functiondef(p.oid) into texte
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_geste_affaire_optimistic';

  if position('cascade_annulation_compromis' in texte) = 0 then
    raise notice 'la cascade n''est pas la -- rien a retirer.'; return;
  end if;

  texte := replace(texte, chr(13), '');

  -- Le bloc va de son commentaire d'ouverture jusqu'a la ligne qui le suivait.
  debut := position('  -- LA CASCADE DE L''ANNULATION (11/11/2026)' in texte);
  fin   := position('  PERFORM public.app_recalculer_type_du_bien' in texte);
  if debut = 0 or fin = 0 or fin <= debut then
    raise exception 'bornes du bloc introuvables : NE PAS FORCER, retirer a la main';
  end if;
  texte := substring(texte from 1 for debut - 1) || substring(texte from fin);

  -- Les deux variables, et la ligne du retour.
  texte := replace(texte,
    '  cascade_offre app_affaire_ledger%rowtype;' || chr(10) ||
    '  cascade_faites int := 0;' || chr(10), '');
  texte := replace(texte,
    '    ''job_type'', type_job,' || chr(10) ||
    '    ''offres_refusees_en_cascade'', cascade_faites' || chr(10),
    '    ''job_type'', type_job' || chr(10));

  execute texte;
  raise notice 'cascade retiree. Verifier l''empreinte : 56df3dbef42cae791bb9d804be270ae3';
end $patch$;

-- ─── LE TEMOIN DU NIVEAU 2 ─────────────────────────────────────────────────
-- Attendu : la cascade absente, ET LES DEUX GARDES D'AVANT TOUJOURS LA
-- (un retour arriere ne juge que SA part -- lecon 31).
select 'niveau 2 -- retrait du code' as controle,
       (position('cascade_annulation_compromis' in pg_get_functiondef(p.oid)) > 0) as cascade_attendu_false,
       (position('offre_verrouillee' in pg_get_functiondef(p.oid)) > 0)            as temoin_garde_16_09_attendu_true,
       (position('compromis_verrouille' in pg_get_functiondef(p.oid)) > 0)         as temoin_garde_23_10_attendu_true,
       (position('app_recalculer_type_du_bien' in pg_get_functiondef(p.oid)) > 0)  as temoin_recalcul_attendu_true,
       md5(pg_get_functiondef(p.oid))    as empreinte_attendue_56df3dbe,
       length(pg_get_functiondef(p.oid)) as taille_attendue_10307
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public' and p.proname = 'app_geste_affaire_optimistic';
*/
