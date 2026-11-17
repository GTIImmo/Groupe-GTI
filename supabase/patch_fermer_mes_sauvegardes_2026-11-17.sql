-- ═══════════════════════════════════════════════════════════════════════════
-- FERMER LES TROIS SAUVEGARDES QUE J'AI CREEES AUJOURD'HUI -- 17/11/2026
--
-- ⛔⛔ C'EST SA QUESTION QUI A TROUVE LA FAUTE : « as-tu fait le necessaire pour
--   les erreurs que tu as generees lors des essais precedents ? ». NON.
--   J'ai cree TROIS sauvegardes aujourd'hui et je les ai laissees OUVERTES a
--   `authenticated` -- lecture, suppression ET TRUNCATE :
--     app_c4_note_avant_20261117              (le 3e patch de C4, 80 notes)
--     app_classeur_lien_avant_regel_20261117  (le re-gel des 195)
--     app_classeur_ligne_id_avant_20261117    (les 21 lignes)
--
--   Or LE PATRON AVAIT CHANGE EXPRES, et c'est ecrit dans le projet depuis le
--   16/11 : « 18 sauvegardes du projet sont reellement ouvertes a authenticated
--   (TRUNCATE comprise) (...) toute NOUVELLE sauvegarde NAIT FERMEE -- C8 est la
--   premiere ». J'ai donc enfreint trois fois une regle posee la veille, et
--   personne ne l'aurait vu : une sauvegarde ne sert que le jour ou on en a
--   besoin, et c'est ce jour-la qu'on decouvrirait qu'elle a ete videe.
--
-- ⚠ CE QUE CE PATCH NE FAIT PAS : il NE TOUCHE PAS aux 18 anciennes sauvegardes.
--   Frederic a tranche le 16/11 (« Non enchaine ») -- ce n'est pas le moment de
--   revenir sur sa decision par un effet de bord.
--
-- ⭐ CE QU'IL FAIT, ET RIEN DE PLUS : revoquer TOUT droit de `authenticated` et
--   d'`anon` sur ces trois tables. `service_role` garde l'acces -- c'est lui qui
--   jouerait un retour arriere.
-- ⛔ `revoke all from public` NE FERME PAS `authenticated` : faute deja payee
--   deux fois dans ce projet. On revoque donc CHAQUE role NOMMEMENT.
--
-- RETOUR ARRIERE : patch_fermer_mes_sauvegardes_2026-11-17_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

revoke all on table public.app_c4_note_avant_20261117
  from public, anon, authenticated;
revoke all on table public.app_classeur_lien_avant_regel_20261117
  from public, anon, authenticated;
revoke all on table public.app_classeur_ligne_id_avant_20261117
  from public, anon, authenticated;

grant select on table public.app_c4_note_avant_20261117 to service_role;
grant select on table public.app_classeur_lien_avant_regel_20261117 to service_role;
grant select on table public.app_classeur_ligne_id_avant_20261117 to service_role;

-- LES CONTROLES, DANS LA MEME TRANSACTION
do $$
declare t text; n integer := 0;
begin
  foreach t in array array['app_c4_note_avant_20261117',
                           'app_classeur_lien_avant_regel_20261117',
                           'app_classeur_ligne_id_avant_20261117']
  loop
    -- ⛔ authenticated ne doit plus RIEN pouvoir : ni lire, ni supprimer, ni vider
    if has_table_privilege('authenticated', 'public.' || t, 'SELECT')
       or has_table_privilege('authenticated', 'public.' || t, 'DELETE')
       or has_table_privilege('authenticated', 'public.' || t, 'TRUNCATE')
       or has_table_privilege('authenticated', 'public.' || t, 'UPDATE') then
      raise exception '⛔ authenticated garde un droit sur %', t;
    end if;
    if has_table_privilege('anon', 'public.' || t, 'SELECT') then
      raise exception '⛔ anon peut encore lire %', t;
    end if;
    -- ⭐ TEMOIN POSITIF : service_role doit POUVOIR lire, sinon un retour
    --   arriere serait impossible et on aurait ferme la porte sur la cle.
    if not has_table_privilege('service_role', 'public.' || t, 'SELECT') then
      raise exception '⛔ service_role NE PEUT PLUS lire % -- le retour arriere '
        'serait impossible', t;
    end if;
    n := n + 1;
  end loop;

  -- ⭐⭐ ET LES DONNEES SONT INTACTES : fermer des droits ne touche pas le contenu
  if (select count(*) from app_c4_note_avant_20261117) <> 80 then
    raise exception '⛔ la sauvegarde des notes ne porte plus 80 lignes';
  end if;
  if (select count(*) from app_classeur_lien_avant_regel_20261117) <> 12595 then
    raise exception '⛔ la sauvegarde du gel ne porte plus 12 595 lignes';
  end if;
  if (select count(*) from app_classeur_ligne_id_avant_20261117) <> 4773 then
    raise exception '⛔ la sauvegarde des lignes ne porte plus 4 773 lignes';
  end if;

  raise notice '✅ % sauvegardes fermees, contenus intacts (80 . 12 595 . 4 773)', n;
end $$;

commit;
