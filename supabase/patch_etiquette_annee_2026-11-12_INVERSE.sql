-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — L'ANNÉE DES ÉTIQUETTES                        12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Il défait ..._REPOSE.sql, et lui seul.
--
-- ⛔⛔ CE QU'IL NE FAIT PAS, ET C'EST VOULU : il ne touche PAS aux fonctions de
--   ..._LECTEURS.sql. Celles-ci n'écrivent aucune donnée et sont JUSTES ; les
--   remettre dans leur état fautif n'aurait aucun sens. Si on veut vraiment les
--   défaire, on recolle le corps du 12/11 matin (il est dans
--   supabase/patch_etiquette_dossier_2026-11-09.sql).
--
-- ⭐ « UN RETOUR ARRIÈRE NE JUGE QUE SA PART » — règle du projet, leçon n° 31 :
--   il vérifie d'abord qu'il peut rendre EXACTEMENT ce qu'il doit rendre, et il
--   refuse plutôt que de rendre à moitié.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ① LA SAUVEGARDE EST-ELLE LÀ, ET COMPLÈTE ?
do $$
declare v_copie integer; v_registre integer; v_etiq integer;
begin
  if not exists (select 1 from information_schema.tables
                  where table_schema = 'public'
                    and table_name = 'app_etiquette_avant_repose_20261112') then
    raise exception 'ARRET : aucune sauvegarde app_etiquette_avant_repose_20261112. '
                    'Il n''y a RIEN a restaurer -- la repose n''a jamais eu lieu.';
  end if;
  select count(*), count(app_dossier_uuid) into v_copie, v_etiq
    from public.app_etiquette_avant_repose_20261112;
  select count(*) into v_registre from public.app_affaire_ledger;

  -- ⚠ Le registre a pu GRANDIR depuis (une transaction neuve est arrivee). Ce
  --   n'est pas un obstacle : on rend leur etiquette d'avant aux lignes qu'on
  --   avait copiees, et les lignes neuves restent telles quelles. Mais on le DIT.
  if v_registre <> v_copie then
    raise notice 'le registre porte % lignes, la sauvegarde % : % ligne(s) neuve(s) '
                 'ne seront pas touchees (elles n''existaient pas a la sauvegarde).',
                 v_registre, v_copie, v_registre - v_copie;
  end if;
  if v_etiq <> v_copie then
    raise exception 'ARRET : la sauvegarde est incomplete -- % lignes sur % portent '
                    'une etiquette. Restaurer poserait des trous.', v_etiq, v_copie;
  end if;
  raise notice 'sauvegarde valide : % lignes, toutes etiquetees', v_copie;
end $$;


-- ② LES ÉTIQUETTES REVIENNENT, AU CHAMP PRÈS
update public.app_affaire_ledger l
   set app_dossier_uuid   = s.app_dossier_uuid,
       app_dossier_numero = s.app_dossier_numero
  from public.app_etiquette_avant_repose_20261112 s
 where l.app_affaire_id = s.app_affaire_id
   and (l.app_dossier_uuid   is distinct from s.app_dossier_uuid
     or l.app_dossier_numero is distinct from s.app_dossier_numero);


-- ③ LE COMPTEUR ET LE JOURNAL REVIENNENT AUSSI
--    ⛔ Sans eux, la prochaine pose repartirait d'un compteur reposé et
--      fabriquerait des numéros déjà pris.
delete from public.app_dossier_numero_compteur;
insert into public.app_dossier_numero_compteur
select * from public.app_etiquette_compteur_avant_20261112;

delete from public.app_dossier_etiquette_journal;
insert into public.app_dossier_etiquette_journal
select * from public.app_etiquette_journal_avant_20261112;


-- ④ IL NE DOIT RESTER AUCUNE TRACE DE LA REPOSE — et on le vérifie AVANT de
--    valider. Si un seul point casse, tout est annulé.
do $$
declare v_reste integer; v_sans integer; v_a integer; v_b integer;
begin
  select count(*) into v_reste
    from public.app_etiquette_avant_repose_20261112 s
    join public.app_affaire_ledger l on l.app_affaire_id = s.app_affaire_id
   where l.app_dossier_uuid   is distinct from s.app_dossier_uuid
      or l.app_dossier_numero is distinct from s.app_dossier_numero;
  if v_reste <> 0 then
    raise exception 'ARRET : % ligne(s) ne sont pas revenues a leur etiquette d''avant.', v_reste;
  end if;

  select count(*) into v_sans from public.app_affaire_ledger
   where app_chaine_id is not null and app_dossier_uuid is null
     and app_affaire_id in (select app_affaire_id from public.app_etiquette_avant_repose_20261112);
  if v_sans <> 0 then
    raise exception 'ARRET : % transaction(s) sauvegardee(s) sont restees sans etiquette.', v_sans;
  end if;

  -- ⚠ ET LES INVARIANTS DOIVENT TENIR APRÈS LE RETOUR AUSSI. Un retour arrière
  --   qui laisse le registre incoherent est pire que le mal qu'il defait.
  select count(*) into v_a from (
    select app_chaine_id from public.app_affaire_ledger
     where app_chaine_id is not null and app_dossier_uuid is not null
     group by app_chaine_id having count(distinct app_dossier_uuid) > 1) z;
  select count(*) into v_b from (
    select app_dossier_uuid from public.app_affaire_ledger
     where app_dossier_uuid is not null and app_chaine_id is not null
     group by app_dossier_uuid having count(distinct app_chaine_id) > 1) z;
  if v_a <> 0 or v_b <> 0 then
    raise exception 'ARRET : apres le retour, % groupe(s) a plusieurs etiquettes et '
                    '% etiquette(s) sur plusieurs groupes.', v_a, v_b;
  end if;

  raise notice 'RETOUR ARRIERE FAIT : etiquettes, compteur et journal rendus a leur '
               'etat d''avant la repose. Invariants verts.';
end $$;

commit;

-- ═══════════════════════════════════════════════════════════════════════════
-- ⚠ LES TROIS TABLES DE SAUVEGARDE NE SE SUPPRIMENT PAS ICI, et pas non plus
--   après un collage réussi : elles ne coûtent rien et elles sont la seule copie
--   des numéros du 12/11. Elles ne partent que sur décision de Frédéric.
--
-- ⚠ ET APRÈS CE RETOUR, LES 708 ANNÉES SONT DE NOUVEAU FAUSSES. C'est ce qu'un
--   retour arrière doit faire : rendre l'état d'avant, pas un état meilleur.
--   Rejouer la répétition le dira (contrôle ④ : 708 et 653).
-- ═══════════════════════════════════════════════════════════════════════════
