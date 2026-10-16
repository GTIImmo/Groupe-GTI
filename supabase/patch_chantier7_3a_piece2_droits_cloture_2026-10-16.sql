-- ============================================================================
-- CHANTIER (7)-3a PIECE 2 -- LA DATE DE CLOTURE EST RESERVEE AU MANAGER / ADMIN
-- 16/10/2026
-- ============================================================================
-- POURQUOI. Demande de Frederic du 16/10 : « ce bouton doit etre accessible
-- uniquement par les admin / manager, sinon visible mais lie a la demande
-- annulation de mandat existante ».
--
-- ETAT MESURE AVANT (16/10) :
--   app_set_mandat_cloture_optimistic est SECURITY DEFINER, ouverte a
--   `authenticated`, et son etape (1) ne demande QUE « es-tu authentifie ? ».
--   Aucune garde de role, aucune garde de perimetre.
--   -> n importe quel negociateur connecte peut ecrire une date de cloture sur
--      n importe lequel des 24 564 mandats, y compris ceux d un collegue.
--
-- ⚠⚠ LE PROJET AVAIT DEJA TRANCHE L INVERSE, ET IL FAUT LE DIRE :
--   patch_chantier3_3c_piece4_droits_2026-10-13.sql, l. 22 :
--     « NE PAS TOUCHER A app_set_mandat_cloture_optimistic : pour celle-la,
--       authenticated est VOULU -- c est l ecran qui l appelle pour saisir. »
--   La demande du 16/10 REMPLACE cette decision. Ce patch n est pas la
--   correction d une negligence : c est un changement d avis, assume et date.
--
-- CE QU ON NE FAIT PAS, ET POURQUOI :
--   ⚠ ON NE RETIRE PAS LE GRANT `authenticated`. Un `revoke` ferait lever une
--     erreur de permission -- et le seul appelant du front AVALE l erreur
--     (App.tsx:16951, console.warn). Le negociateur verrait « statut change » et
--     rien d autre. Une garde A L INTERIEUR rend un refus LISIBLE, en francais,
--     que la piece 4 pourra afficher. Meme doctrine que (7)-1 : « bouton
--     toujours visible avec un refus explique ».
--   ⭐ `anon` n a toujours AUCUN droit sur cette fonction (chantier (1)).
--   ⭐ `service_role` passe : le worker et la re-pose de nuit n ont pas de
--     auth.uid(), et is_app_manager_or_admin() rendrait faux pour eux.
--
-- CE QUE CA NE CHANGE PAS -- mesure du 16/10, appelant par appelant :
--   · LE WORKER n appelle PAS cette fonction : il ecrit en direct dans le carnet
--     et le registre (console_job_worker.js:13700-13733), et un commentaire dit
--     pourquoi (elle refuse un couple absent du registre).
--     ⭐ ET CE N EST PAS GRAVE, parce que LE GESTE EST DEJA RESERVE AILLEURS.
--       Mesure du 16/10, en empruntant les identites, en lecture seule :
--         legrand   (commercial) -> can_request_job(change_hektor_annonce_status) = FALSE
--         codex.test(admin)      -> TRUE
--       app_console_can_request_job reserve change_hektor_annonce_status ET
--       archive_hektor_annonce a admin/manager -- c est sa PREMIERE regle, posee
--       au chantier (2) -- et app_change_annonce_status_optimistic l appelle bien.
--       Les DEUX chemins de cloture (« Mandat clos » et « Vendu ») passent par ce
--       meme type de travail : un negociateur ne peut donc PAS clore un mandat.
--     ➡ CE QUE CETTE GARDE FERME EST DONC LA PORTE DE DERRIERE : l appel DIRECT
--       a la RPC avec la cle publique, sans passer par l ecran. Famille du
--       chantier (1). Reel, mais ce n est pas la porte d entree.
--   · app_reposer_cloture_mandat_app : service_role seulement, n appelle pas
--     cette fonction. Intacte.
--   · le run, phase2, le backend Render : zero appel dans tout le depot.
--   · les regles RLS : la fonction est SECURITY DEFINER, rien ne change.
--
-- CE PATCH NE RECOPIE PAS LA FONCTION : il la LIT dans la base, verifie son
-- empreinte et que son ancre est unique, insere AVANT l ancre et reexecute.
--   empreinte attendue (sans retours chariot) : 09280b46e6832db15dce53ca5e30e9db
--   ancre : une seule ligne, ASCII pur, vue 1 fois (mesure du 16/10)
--   ANCRES MULTI-LIGNES : ZERO  (lecon du 15/10, la 3e fois)
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('  IF v_annonce is null OR v_numero is null THEN', chr(13), '');
  v_ajout text;
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_set_mandat_cloture_optimistic';

  if v_src is null then
    raise exception 'STOP : app_set_mandat_cloture_optimistic introuvable';
  end if;

  if position('GARDE MANAGER ADMIN' in v_src) > 0 then
    raise notice 'DEJA FAIT : la garde manager/admin est en place';
    return;
  end if;

  -- La garde que l on va appeler doit exister, sinon la fonction ne compilerait
  -- qu a l execution et le refus deviendrait une panne.
  if not exists (
    select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'is_app_manager_or_admin'
  ) then
    raise exception 'STOP : is_app_manager_or_admin() est introuvable';
  end if;

  if md5(v_src) <> '09280b46e6832db15dce53ca5e30e9db' then
    raise notice 'ATTENTION : empreinte % (attendue 09280b46...) -- un autre patch est passe. On continue : l ancre unique et l absence du texte sont les vrais garde-fous.', md5(v_src);
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then
    raise exception 'STOP : l ancre apparait % fois (attendu 1)', v_vu;
  end if;

  v_ajout := replace(
'  -- GARDE MANAGER ADMIN -- DEBUT
  -- (7)-3a piece 2 (16/10/2026) : SEUL UN MANAGER OU UN ADMIN FIXE LA DATE.
  -- Demande de Frederic du 16/10. Elle REMPLACE la decision du 13/10 qui disait
  -- que `authenticated` etait VOULU ici (patch_chantier3_3c_piece4_droits, l.22).
  -- On garde le GRANT a authenticated et on refuse PROPREMENT : le front avale
  -- les erreurs de cette fonction (console.warn), donc une erreur de permission
  -- serait un silence. `anon` n a aucun droit (chantier (1)).
  -- `service_role` passe : le worker et la re-pose n ont pas de auth.uid().
  IF coalesce(v_role, '''') <> ''service_role''
     AND NOT public.is_app_manager_or_admin() THEN
    RETURN jsonb_build_object(
      ''ok'', false,
      ''erreur'', ''droits_insuffisants'',
      ''message'', ''Seul un manager ou un administrateur peut fixer la date de cloture du mandat. Un negociateur passe par une demande d annulation de mandat.'');
  END IF;
  -- GARDE MANAGER ADMIN -- FIN
' || v_ancre, chr(13), '');

  v_new := replace(v_src, v_ancre, v_ajout);
  execute v_new;
  raise notice 'POSE : la date de cloture est desormais reservee au manager / admin (et au service_role)';
end
$do$;

commit;
