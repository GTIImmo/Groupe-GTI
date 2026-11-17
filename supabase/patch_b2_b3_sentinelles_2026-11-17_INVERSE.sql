-- ═══════════════════════════════════════════════════════════════════════════
-- LE RETOUR ARRIERE DE B2 ET B3 -- 17/11/2026
--
-- ⭐ Il ne retire QUE les deux vues que le patch a creees. Le patch n'avait
--   modifie AUCUNE donnee, AUCUNE table, AUCUN droit existant -- il n'y a donc
--   rien d'autre a defaire.
--
-- ⚠ ET IL NE TOUCHE PAS AU MONITEUR : les deux lignes de check_gti_health.py
--   sont du CODE, pas de la base. Les retirer est un geste git
--   (commit b2/b3), pas un geste SQL. Si on joue cet inverse SANS retirer le
--   code, les deux sentinelles passeront en « unknown » -- ce qui est le bon
--   comportement : une lecture ratee n'est JAMAIS un vert.
--
-- ⛔ ET IL JUGE SA PROPRE PART (lecon 31) : il verifie que les deux vues ont
--   disparu, ET que la voisine en service est intacte.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

drop view if exists public.app_v_classeur_ligne_sans_lien;
drop view if exists public.app_v_affaire_note_condition_orpheline;

do $$
declare n integer;
begin
  select count(*) into n from pg_class c join pg_namespace x on x.oid = c.relnamespace
   where x.nspname = 'public'
     and c.relname in ('app_v_classeur_ligne_sans_lien',
                       'app_v_affaire_note_condition_orpheline');
  if n <> 0 then raise exception '⛔ il reste % vue(s) du patch', n; end if;

  -- ⭐ LA VOISINE, PROUVEE INTACTE
  select count(*) into n from pg_class c join pg_namespace x on x.oid = c.relnamespace
   where x.nspname = 'public' and c.relname = 'app_v_repartition_orpheline';
  if n <> 1 then raise exception '⛔ app_v_repartition_orpheline a disparu'; end if;

  -- ⭐⭐ ET AUCUNE DONNEE N'A BOUGE : le patch n'ecrivait rien, l'inverse non plus
  select count(*) into n from public.app_affaire_note;
  if n < 4000 then raise exception '⛔ les notes ont bouge : % lignes', n; end if;
  select count(*) into n from public.app_affaire_condition;
  if n < 30 then raise exception '⛔ les conditions ont bouge : % lignes', n; end if;

  raise notice '✅ RETOUR ARRIERE COMPLET : 2 vues retirees, voisine intacte, 0 donnee touchee';
end $$;

commit;
