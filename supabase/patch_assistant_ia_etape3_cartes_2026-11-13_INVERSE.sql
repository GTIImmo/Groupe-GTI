-- ═══════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ASSISTANT IA, ÉTAPE 3 LOT 1 : LES CARTES DE VALIDATION      13/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Retire app_assistant_action. ⚠ Les cartes déjà proposées ou exécutées disparaissent avec elle :
-- ce sont le journal des actions de l'assistant. Les GESTES exécutés (demandes, relances), eux,
-- restent dans leurs tables métier : ce retour arrière ne défait aucun geste.
-- Avant de le poser, couper l'assistant (assistant_ia = 'off') ou remettre le code d'avant l'étape 3 :
-- sinon le serveur échouerait à ranger une carte (l'assistant le dirait, sans rien exécuter).
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_assistant_action') is null then
    raise exception 'ARRET : app_assistant_action absente -- rien a retirer';
  end if;
  if exists (select 1 from pg_depend d join pg_rewrite r on r.oid = d.objid
              where d.refobjid = 'public.app_assistant_action'::regclass and r.ev_class <> 'public.app_assistant_action'::regclass) then
    raise exception 'ARRET : une vue depend de app_assistant_action -- a regarder avant de retirer';
  end if;
end
$garde$;

drop table public.app_assistant_action;

do $verif$
begin
  if to_regclass('public.app_assistant_action') is not null then
    raise exception 'ARRET : la table est encore la';
  end if;
end
$verif$;

commit;
