-- ============================================================================
-- INVERSE de la reparation des 103 masquees
-- 19/10/2026
-- ============================================================================
-- Il remet les 103 photos exactement dans l'etat ou le patch les a trouvees :
--     present_in_hektor = false
--     absent_depuis     = 2026-10-15 21:23:23.635+00
--
-- ⭐ CETTE DATE N'EST PAS INVENTEE : les 103 portaient UNE SEULE date distincte,
--   a la milliseconde pres (mesure du 19/10). C'est la signature d'une ecriture
--   unique -- celle de la ligne 4/4, le 15/10 a 23:23 heure locale.
--
-- ⚠ IL NE DEFAIT QUE SA PROPRE PART (lecon du 15/10). Il agit sur les photos
--   `visible = false AND present_in_hektor = true` -- exactement ce que le patch
--   a produit. Si ce nombre n'est plus 103, c'est qu'AUTRE CHOSE est arrive
--   depuis (le futur bouton « masquer », par exemple) : il s'arrete et le DIT,
--   plutot que de remettre a l'etat « absent » des photos qu'un humain vient de
--   masquer volontairement.
--
-- ⚠ CE QU'IL NE PEUT PAS DEFAIRE, et il faut le savoir : `updated_at` aura bouge
--   deux fois (le patch, puis lui). Sans consequence -- cette colonne sert de
--   curseur a la descente, qui re-descendra 103 lignes.
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $do$
declare
  v_cibles  integer;
  v_ecrites integer;
  v_reste   integer;
  v_date    constant timestamptz := '2026-10-15 21:23:23.635+00';
begin
  select count(*) into v_cibles
    from public.app_console_photo
   where visible is false and present_in_hektor is true;

  if v_cibles = 0 then
    raise notice 'RIEN A DEFAIRE : aucune photo masquee n est marquee presente';
    return;
  end if;

  -- ⚠ LA GARDE QUI COMPTE : on ne remet pas a « absent » des photos qu'un humain
  --   aurait masquees depuis. 103 est exactement ce que le patch a produit.
  if v_cibles <> 103 then
    raise exception 'STOP : % photos masquees et presentes (attendu 103). Autre chose est arrive depuis le patch -- ne PAS defaire a l aveugle.', v_cibles;
  end if;

  update public.app_console_photo
     set present_in_hektor = false,
         absent_depuis = v_date
   where visible is false and present_in_hektor is true;
  get diagnostics v_ecrites = row_count;

  select count(*) into v_reste
    from public.app_console_photo
   where visible is false and present_in_hektor is true;

  if v_reste <> 0 then
    raise exception 'STOP : il reste % masquees presentes apres le retour arriere', v_reste;
  end if;

  raise notice 'DEFAIT : % photos remises a « absente », date d origine restauree (%).', v_ecrites, v_date;
end
$do$;

commit;
