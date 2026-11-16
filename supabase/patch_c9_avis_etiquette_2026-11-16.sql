-- ═══════════════════════════════════════════════════════════════════════════
-- C9 -- L ETIQUETTE DE DOSSIER SUR LA TABLE DES AVIS            16/11/2026
--
-- DEMANDE PAR FREDERIC : « Je veux ces colonnes dans le registre des transactions
-- dans l'apps et le serveur mais pas visibles tout de suite dans le front », puis,
-- apres que je lui ai propose de tout mettre en colonnes du registre :
-- « Table avec etiquettes ».
--
-- ⭐⭐⭐ POURQUOI L ETIQUETTE ET NON LE NUMERO DE CHAINE, et c'est une regle du
--   projet, pas un choix de ce patch :
--
--     « un numero de chaine ne doit JAMAIS servir de point d'accrochage,
--       il bouge »              -- regle du 28/10/2026
--
--   `app_chaine_id` est RECALCULE par le run : 6 chaines ont effectivement bouge
--   depuis le 12/11 (journal des etiquettes, 11 455 lignes / 11 449 chaines).
--   `app_dossier_uuid`, elle, NE BOUGE JAMAIS une fois posee -- c'est tout son
--   dessein, et c'est elle qui ira dans la colonne `affair_uuid` du Sheet a
--   l'etape 5.2. Un avis accroche par l'etiquette survit a une FUSION de
--   dossiers ; accroche par la chaine, il se perdrait en silence.
--
-- ⚠ ET CETTE TABLE EST LA PREMIERE A S ACCROCHER PAR L ETIQUETTE : mesure du
--   16/11, PERSONNE d'autre que `app_affaire_ledger` ne portait
--   `app_dossier_uuid`. L'etiquette etait posee partout et utilisee par rien.
--
-- CE QUE LE PATCH FAIT :
--   1. deux colonnes neuves, l'UUID (pour joindre) et le numero court (pour lire)
--   2. un index sur l'UUID -- c'est le point de jointure avec le registre
--   3. le remplissage, SEULEMENT quand il n'y a AUCUNE ambiguite
--
-- CE QU IL NE FAIT PAS :
--   . il ne touche a AUCUNE des trois colonnes d'avis deja posees ;
--   . il ne met pas `app_chaine_id` (voir ci-dessus) ;
--   . il n'ouvre AUCUN droit : la table reste fermee a `authenticated` depuis le
--     verrou du 16/11, donc le front ne la voit toujours pas -- ce qui est
--     exactement ce que Frederic a demande ;
--   . il ne remplit pas les 28 lignes ambigues, et il les COMPTE.
--
-- Retour arriere : patch_c9_avis_etiquette_2026-11-16_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare avis integer; deja integer;
begin
  select count(*) into avis from public.app_classeur_avis;
  if avis <> 2588 then
    raise exception '⛔ ARRET : % avis au lieu des 2 588 poses le 16/11.', avis;
  end if;
  select count(*) into deja from information_schema.columns
   where table_schema='public' and table_name='app_classeur_avis'
     and column_name = 'app_dossier_uuid';
  if deja <> 0 then
    raise exception '⛔ ARRET : la colonne app_dossier_uuid existe deja. '
      'Quelqu''un est passe avant -- relire.';
  end if;
  raise notice '✅ etat d''avant : 2 588 avis, aucune colonne d''etiquette.';
end $$;

-- ─── 2. LES DEUX COLONNES ──────────────────────────────────────────────────
-- ⓘ `uuid` et non `text` : le MEME type que dans le registre, sinon la jointure
--   se ferait par conversion et perdrait l'index (lecon RLS + ::text).
alter table public.app_classeur_avis
  add column app_dossier_uuid   uuid,
  add column app_dossier_numero text;

comment on column public.app_classeur_avis.app_dossier_uuid is
  'ETIQUETTE DE DOSSIER -- le point d''accrochage au registre des transactions. '
  '⛔ JAMAIS app_chaine_id : « un numero de chaine ne doit jamais servir de point '
  'd''accrochage, il bouge » (28/10/2026). Posee par C9 le 16/11, depuis le gel, '
  'uniquement quand une ligne du classeur designe UN SEUL dossier. 28 lignes '
  'restent vides : 20 a cheval sur plusieurs dossiers, 8 sans aucun lien.';
comment on column public.app_classeur_avis.app_dossier_numero is
  'L''etiquette COURTE (D2026-0431), pour l''ecran et pour parler. ⚠ Son annee est '
  'une ETIQUETTE, PAS une donnee.';

-- ─── 3. L'INDEX, parce que c'est le point de jointure ──────────────────────
create index if not exists app_classeur_avis_dossier_uuid_idx
    on public.app_classeur_avis (app_dossier_uuid)
 where app_dossier_uuid is not null;

-- ─── 4. LE REMPLISSAGE, SANS AUCUNE AMBIGUITE ──────────────────────────────
-- ⭐ `having count(distinct ...) = 1` : une ligne du classeur qui designe DEUX
--   dossiers n'est pas remplie. On ne choisit pas a sa place.
-- ⛔ PAS `min(app_dossier_uuid)` : PostgreSQL N'A PAS d'agregat min sur `uuid`
--   (« function min(uuid) does not exist » -- premiere tentative du 16/11, rejetee
--   AVANT le commit, donc sans aucun effet). On prend le premier element du
--   tableau des valeurs distinctes : comme le `having` ci-dessous en exige UNE
--   SEULE, c'est la bonne et c'est la seule.
with etiq as (
  select a.id_unique,
         (array_agg(distinct r.app_dossier_uuid))[1]   as uuid,
         (array_agg(distinct r.app_dossier_numero))[1] as numero
    from public.app_classeur_avis a
    join public.app_classeur_lien l on l.id_unique = a.id_unique
    join public.app_affaire_ledger r on r.app_affaire_id = l.app_affaire_id
   group by a.id_unique
  having count(distinct r.app_dossier_uuid) = 1
)
update public.app_classeur_avis a
   set app_dossier_uuid   = e.uuid,
       app_dossier_numero = e.numero
  from etiq e
 where e.id_unique = a.id_unique;

-- ─── 5. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  remplies integer;
  vides    integer;
  sans_num integer;
  faux     integer;
  avis     integer;
begin
  select count(*) into avis from public.app_classeur_avis;
  if avis <> 2588 then
    raise exception '⛔ le nombre d''avis a change : %.', avis;
  end if;

  select count(app_dossier_uuid) into remplies from public.app_classeur_avis;
  if remplies <> 2560 then
    raise exception '⛔ 2 560 attendues, % remplies.', remplies;
  end if;

  select count(*) into vides from public.app_classeur_avis
   where app_dossier_uuid is null;
  if vides <> 28 then
    raise exception '⛔ 28 vides attendues (20 a cheval + 8 sans lien), %.', vides;
  end if;

  -- ⭐ L'UUID et le numero vont PAR PAIRE : l'un sans l'autre serait un defaut.
  select count(*) into sans_num from public.app_classeur_avis
   where app_dossier_uuid is not null and app_dossier_numero is null;
  if sans_num <> 0 then
    raise exception '⛔ % ligne(s) ont l''UUID sans le numero court.', sans_num;
  end if;

  -- ⭐⭐ LE TEMOIN QUI COMPTE VRAIMENT : chaque etiquette posee doit EXISTER
  --   dans le registre. Une etiquette inventee serait un lien mort.
  select count(*) into faux from public.app_classeur_avis a
   where a.app_dossier_uuid is not null
     and not exists (select 1 from public.app_affaire_ledger r
                      where r.app_dossier_uuid = a.app_dossier_uuid);
  if faux <> 0 then
    raise exception '⛔ % etiquette(s) ne correspondent a AUCUN dossier.', faux;
  end if;

  raise notice '✅ 2 560 etiquettes posees . 28 laissees vides et comptees . '
    '0 UUID sans numero . 0 etiquette orpheline.';
end $$;

commit;
