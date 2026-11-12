-- ═══════════════════════════════════════════════════════════════════════════
-- LA REPOSE DES ÉTIQUETTES, AVEC LA BONNE ANNÉE                 12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⛔⛔ CE FICHIER ÉCRIT, ET IL EFFACE AVANT D'ÉCRIRE. Il ne se colle qu'avec
--     l'accord de Frédéric, et SEULEMENT APRÈS
--     patch_etiquette_annee_2026-11-12_LECTEURS.sql (il refuse sinon).
--     Retour arrière : patch_etiquette_annee_2026-11-12_INVERSE.sql
--
-- ⭐⭐ POURQUOI REPOSER DE ZÉRO, ET POURQUOI C'EST AUJOURD'HUI OU JAMAIS.
--   Mesuré le 12/11 : RIEN ne lit l'étiquette.
--       grep -rn "app_dossier_uuid|app_dossier_numero" apps/ backend/ Console/ scheduled/
--         -> AUCUN résultat
--       clés étrangères vers app_affaire_ledger        -> AUCUNE
--       vues qui la lisent                             -> AUCUNE
--       fonctions qui la lisent  -> app_dossier_numero_format et la pose, rien d'autre
--   Elle n'existe donc que dans le registre et dans son journal. Reposer est
--   GRATUIT tant que les UUID ne sont pas partis dans la colonne `affair_uuid`
--   du classeur (étape 5.2 du plan). APRÈS, le numéro est public et la règle
--   « un numéro ne se perd jamais » l'interdira.
--
--   ⭐ Et reposer vaut mieux que rattraper les 708 : la série repart
--     chronologique, sans trous dans l'année 2026, et la PREMIÈRE ligne du
--     journal dit la vérité. Un rattrapage aurait laissé 653 trous dans 2026 et
--     653 rangs posés hors de leur ordre, à expliquer pour toujours.
--
-- CE QUE LA REPOSE CHANGE, mesuré le 12/11 AVANT de la lancer :
--       dossiers qui changent d'année                         708
--       dont « 2026 » -> une année de 2006 à 2025             653
--       dossiers inchangés                                 10 733
--       transactions touchées (toutes réétiquetées)        31 151
--       les UUID changent TOUS : ils ne sont lus par personne.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ═══════════════════════════════════════════════════════════════════════════
-- ⓿ LE GARDE-FOU : les lecteurs doivent être réparés, sinon on reposerait les
--    mêmes numéros faux. ⛔ Un patch qui ne vérifie pas son prédécesseur fait
--    du travail pour rien, en silence.
-- ═══════════════════════════════════════════════════════════════════════════
do $$
begin
  if not exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                  where n.nspname = 'public'
                    and p.proname = 'app_dossier_annee_date_transaction') then
    raise exception 'ARRET : le lecteur unique n''existe pas. '
                    'Coller d''abord patch_etiquette_annee_2026-11-12_LECTEURS.sql.';
  end if;
  if not exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                  where n.nspname = 'public' and p.proname = 'app_poser_etiquettes_dossier'
                    and pg_get_functiondef(p.oid) like '%app_dossier_annee_date_transaction%') then
    raise exception 'ARRET : la fonction de pose ne passe PAS par le lecteur repare. '
                    'Le fichier LECTEURS n''a pas ete colle, ou pas en entier.';
  end if;
  raise notice 'les deux lecteurs sont repares -- on peut reposer';
end $$;


-- ═══════════════════════════════════════════════════════════════════════════
-- ① LA SAUVEGARDE, AVANT TOUT — règle du projet : jamais un geste destructif
--    sans copie datée. C'est elle que l'INVERSE relit, au champ près.
-- ═══════════════════════════════════════════════════════════════════════════
create table if not exists public.app_etiquette_avant_repose_20261112 as
select app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero,
       now() as copie_le
  from public.app_affaire_ledger;

create table if not exists public.app_etiquette_compteur_avant_20261112 as
select * from public.app_dossier_numero_compteur;

create table if not exists public.app_etiquette_journal_avant_20261112 as
select * from public.app_dossier_etiquette_journal;

-- ⛔ ET ON VÉRIFIE LA COPIE AVANT DE DÉTRUIRE. Si elle ne porte pas ce que le
--   registre porte, quelqu'un est passé entre-temps : on s'arrête.
do $$
declare v_registre integer; v_copie integer; v_etiq integer;
begin
  select count(*) into v_registre from public.app_affaire_ledger;
  select count(*), count(app_dossier_uuid) into v_copie, v_etiq
    from public.app_etiquette_avant_repose_20261112;
  if v_copie <> v_registre then
    raise exception 'ARRET : la sauvegarde porte % lignes, le registre %. '
                    'Une sauvegarde d''un autre passage existe deja -- la renommer avant.',
                    v_copie, v_registre;
  end if;
  if v_etiq <> v_registre then
    raise exception 'ARRET : % lignes sauvegardees sur % portent une etiquette. '
                    'L''etat de depart n''est pas celui de la pose du 12/11.',
                    v_etiq, v_registre;
  end if;
  raise notice 'sauvegarde : % lignes, toutes etiquetees', v_copie;
end $$;


-- ═══════════════════════════════════════════════════════════════════════════
-- ② LA REMISE À ZÉRO
-- ═══════════════════════════════════════════════════════════════════════════
update public.app_affaire_ledger
   set app_dossier_uuid = null, app_dossier_numero = null
 where app_dossier_uuid is not null or app_dossier_numero is not null;

delete from public.app_dossier_etiquette_journal;
delete from public.app_dossier_numero_compteur;


-- ═══════════════════════════════════════════════════════════════════════════
-- ③ LA REPOSE — un seul appel (318 ms mesurés le 12/11 sur 11 441 dossiers)
--    ⛔ ET ELLE REFUSE DE PASSER POUR RIEN : un zéro ne se croit pas sans
--      témoin positif.
-- ═══════════════════════════════════════════════════════════════════════════
do $$
declare r record; v_pose integer := 0; v_lignes integer := 0; v_autres integer := 0;
begin
  for r in select * from public.app_poser_etiquettes_dossier() loop
    raise notice 'geste % : % dossiers, % lignes', r.geste, r.dossiers, r.lignes;
    if r.geste = 'pose' then v_pose := r.dossiers; v_lignes := r.lignes;
    else v_autres := v_autres + r.dossiers; end if;
  end loop;

  if v_pose = 0 then
    raise exception 'ARRET : la repose n''a pose AUCUN dossier.';
  end if;
  if v_autres <> 0 then
    raise exception 'ARRET : propagation/fusion/scission ont vu % dossier(s) alors '
                    'que tout etait nu. La remise a zero n''a pas eu lieu.', v_autres;
  end if;
  if v_lignes <> (select count(*) from public.app_affaire_ledger
                   where app_chaine_id is not null) then
    raise exception 'ARRET : % lignes etiquetees pour % transactions chainees.',
                    v_lignes, (select count(*) from public.app_affaire_ledger
                                where app_chaine_id is not null);
  end if;
  raise notice 'REPOSE FAITE : % dossiers, % transactions', v_pose, v_lignes;
end $$;


-- ═══════════════════════════════════════════════════════════════════════════
-- ④ LES INVARIANTS, DANS LA MÊME TRANSACTION — si l'un casse, TOUT est annulé.
--    ⛔ C'est la seule façon de ne jamais laisser le registre à moitié réétiqueté.
-- ═══════════════════════════════════════════════════════════════════════════
do $$
declare v_a integer; v_b integer; v_sans integer; v_bij integer; v_dos integer;
begin
  select count(*) into v_a from (
    select app_chaine_id from public.app_affaire_ledger
     where app_chaine_id is not null and app_dossier_uuid is not null
     group by app_chaine_id having count(distinct app_dossier_uuid) > 1) z;
  select count(*) into v_b from (
    select app_dossier_uuid from public.app_affaire_ledger
     where app_dossier_uuid is not null and app_chaine_id is not null
     group by app_dossier_uuid having count(distinct app_chaine_id) > 1) z;
  select count(*) into v_sans from public.app_affaire_ledger
   where app_chaine_id is not null and app_dossier_uuid is null;
  select count(distinct app_dossier_uuid), count(distinct app_chaine_id)
    into v_bij, v_dos from public.app_affaire_ledger where app_chaine_id is not null;

  if v_a <> 0 then raise exception 'INVARIANT : % groupe(s) a plusieurs etiquettes', v_a; end if;
  if v_b <> 0 then raise exception 'INVARIANT : % etiquette(s) sur plusieurs groupes', v_b; end if;
  if v_sans <> 0 then raise exception 'INVARIANT : % transaction(s) chainee(s) sans etiquette', v_sans; end if;
  if v_bij <> v_dos then
    raise exception 'INVARIANT : % etiquettes pour % dossiers -- pas de bijection', v_bij, v_dos;
  end if;
  raise notice 'INVARIANTS VERTS : % dossiers = % etiquettes, 0 sans etiquette', v_dos, v_bij;
end $$;

commit;

-- ═══════════════════════════════════════════════════════════════════════════
-- APRÈS LE COLLAGE : jouer patch_etiquette_annee_2026-11-12_REPETITION.sql
-- ⚠ Et la sauvegarde ne se supprime QUE sur décision de Frédéric, jamais ici.
-- ═══════════════════════════════════════════════════════════════════════════
