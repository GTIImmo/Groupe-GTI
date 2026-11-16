-- ═══════════════════════════════════════════════════════════════════════════
-- LE VERROU DES TABLES DU CHANTIER -- RETOUR ARRIERE                16/11/2026
--
-- ⭐ « Un retour arriere ne juge que SA part » (lecon 31) : il ne rend QUE les
--   droits que le patch a retires, sur les QUATRE tables nommees, et il verifie
--   ensuite qu'il les a bien rendus.
--
-- ⚠ IL REND LE PASSE ENTIER, et c'est voulu : il remet l'etat EXACT d'avant le
--   16/11 (authenticated avait SELECT, INSERT, UPDATE, DELETE, TRUNCATE,
--   TRIGGER, REFERENCES). Un retour arriere qui rendrait « juste la lecture »
--   ne serait pas un retour arriere : ce serait une troisieme decision.
--
-- ⛔ A NE JOUER QUE si une lecture du front ou du backend s'est mise a echouer
--   -- ce qui serait une surprise, puisque le grep du 16/11 n'a trouve AUCUNE
--   occurrence de ces quatre tables dans apps/ ni backend/. Si ca arrive,
--   c'est que le grep a manque un appel dynamique : le NOTER avant de rejouer.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

grant select, insert, update, delete, truncate, trigger, references
   on public.app_classeur_lien      to authenticated;
grant select, insert, update, delete, truncate, trigger, references
   on public.app_classeur_ligne_id  to authenticated;
grant select, insert, update, delete, truncate, trigger, references
   on public.app_charge_exclusion   to authenticated;
grant select, insert, update, delete, truncate, trigger, references
   on public.app_classeur_avis      to authenticated;

do $$
declare rendus integer;
begin
  select count(*) into rendus
    from information_schema.role_table_grants
   where table_schema = 'public' and grantee = 'authenticated'
     and privilege_type = 'TRUNCATE'
     and table_name in ('app_classeur_lien', 'app_classeur_ligne_id',
                        'app_charge_exclusion', 'app_classeur_avis');
  if rendus <> 4 then
    raise exception '⛔ % table(s) sur 4 ont retrouve le passe.', rendus;
  end if;
  raise notice '✅ les 4 tables ont retrouve leur etat d''avant le 16/11. '
    '⚠ Elles sont donc de nouveau ouvertes : dire POURQUOI dans le plan.';
end $$;

commit;
