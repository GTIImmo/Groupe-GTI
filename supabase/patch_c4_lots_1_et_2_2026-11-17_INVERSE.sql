-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (3e patch) -- LE RETOUR ARRIERE DES LOTS 1 ET 2
-- Genere le 2026-11-17
--
-- ⭐⭐ IL RESTAURE LE TEXTE EXACT D'AVANT depuis la sauvegarde datee, et il ne
--   touche que : les notes PORTANT LA MARQUE, les notes d'origine
--   'classeur:F-en-cours', et les conditions d'origine 'classeur:F-credit'.
--   Il ne PEUT PAS toucher les 195 notes de C5, les 4 325 du 2e patch, ni les
--   5 conditions saisies dans l'app.
--
-- ⛔ ET IL JUGE SA PROPRE PART (lecon 31) : il verifie qu'il ne reste AUCUNE
--   trace de la marque, ET que les voisins sont intacts.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① les notes CREEES par le patch : on les retire
delete from app_affaire_note where origine = 'classeur:F-en-cours';

-- ② les notes COMPLETEES : on restaure le texte EXACT d'avant
update app_affaire_note a
   set texte = s.texte
  from app_c4_note_avant_20261117 s
 where a.app_affaire_id = s.app_affaire_id
   and a.texte <> s.texte;

-- ③ les conditions posees par le patch
delete from app_affaire_condition where origine = 'classeur:F-credit';

do $$
declare n integer;
begin
  select count(*) into n from app_affaire_note
   where position('[classeur F, suivi en cours au 17/11/2026]' in texte) > 0;
  if n <> 0 then raise exception '⛔ il reste % notes marquees', n; end if;
  select count(*) into n from app_affaire_note where origine = 'classeur:F-en-cours';
  if n <> 0 then raise exception '⛔ il reste % notes creees', n; end if;
  select count(*) into n from app_affaire_condition where origine = 'classeur:F-credit';
  if n <> 0 then raise exception '⛔ il reste % conditions', n; end if;

  -- ⭐⭐ LE TEXTE EST REVENU A L'IDENTIQUE, pas seulement « sans la marque »
  select count(*) into n
    from app_c4_note_avant_20261117 s
    join app_affaire_note a on a.app_affaire_id = s.app_affaire_id
   where a.texte <> s.texte;
  if n <> 0 then raise exception '⛔ % notes ne sont pas revenues a l identique', n; end if;

  -- ⭐ LES VOISINS, PROUVES INTACTS
  select count(*) into n from app_affaire_note where origine = 'classeur';
  if n <> 195 then raise exception '⛔ LES 195 NOTES DE C5 ONT BOUGE : %', n; end if;
  select count(*) into n from app_affaire_note
   where origine in ('classeur:F', 'classeur:G', 'classeur:F+G');
  if n <> 4325 then raise exception '⛔ LES 4 325 NOTES DU 2e PATCH ONT BOUGE : %', n; end if;
  select count(*) into n from app_affaire_condition where origine = 'saisie';
  if n <> 5 then raise exception '⛔ LES 5 CONDITIONS SAISIES ONT BOUGE : %', n; end if;

  raise notice '✅ RETOUR ARRIERE COMPLET, texte restaure a l identique';
end $$;

commit;
