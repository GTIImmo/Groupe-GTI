-- G.8 -- L'ANCRE DES SIX MOIS                                          26/09/2026
--
-- POURQUOI. La regle validee par Frederic le 26/09 dit : une annonce EN VENTE garde ses
-- derives ; une annonce ARCHIVEE les garde SIX MOIS, puis on les retire ; le master reste
-- toujours sur le serveur, donc retirer n'est jamais une perte.
--
-- ⛔ MAIS « six mois apres l'archivage » suppose une DATE D'ARCHIVAGE, et il n'en existe
-- AUCUNE dans le projet -- verifie le 26/09 sur les quatre index et sur app_console_photo :
-- « archive » est un DRAPEAU (du texte, « 0 » ou « 1 »), pas une date. Les seules dates
-- disponibles (date_maj, refreshed_at) bougent pour dix autres raisons.
-- -> il faut poser l'ancre soi-meme. C'est ce que fait ce patch.
--
-- CE QU'IL NE FAIT PAS : il ne supprime RIEN. Il pose une date, c'est tout. La purge des
-- six mois viendra apres, et elle lira cette date. Tant qu'aucun derive n'existe (le
-- coffre gti-photo est vide), ce patch n'a aucun effet visible.
--
-- ⚠⚠ LE POINT DE CONCEPTION : ON NE REECRIT PAS LA REGLE « ANNONCE VIVANTE ».
-- Le worker la porte dans shouldKeepCloud (archive = 0 ET statut parmi Actif, Sous offre,
-- Sous compromis, Estimation). La reecrire ici en SQL creerait DEUX verites qui
-- deriveraient un jour -- et la purge effacerait alors les derives d'annonces encore en
-- vente. Or app_dossier_current EST deja l'ensemble des vivantes, par construction
-- (ANNONCES_SCOPE_WHERE applique exactement ces conditions). Donc :
--       vivante  =  le numero de la photo est dans app_dossier_current
-- Une seule verite, aucune derive possible.

-- ── 1. L'ANCRE ────────────────────────────────────────────────────────────────
alter table public.app_console_photo
  add column if not exists hors_vitrine_depuis timestamptz;

comment on column public.app_console_photo.hors_vitrine_depuis is
  'Quand l''annonce de cette photo a cesse d''etre en vente (sortie de '
  'app_dossier_current). NULL = elle y est encore. C''est l''ancre des SIX MOIS : la purge '
  'des derives lira cette date. Remise a NULL si l''annonce redevient vivante.';

-- La purge devra trouver « les photos sorties depuis plus de 6 mois » sans balayer
-- 436 524 lignes.
create index if not exists app_console_photo_hors_vitrine_idx
  on public.app_console_photo (hors_vitrine_depuis)
  where hors_vitrine_depuis is not null;


-- ── 2. LE GESTE NOCTURNE ──────────────────────────────────────────────────────
create or replace function public.app_photo_marquer_sortie_vitrine()
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  vivantes   bigint;
  plancher   constant bigint := 5000;   -- cf garde-fou ci-dessous
  marquees   bigint := 0;
  liberees   bigint := 0;
  maintenant timestamptz := now();
begin
  select count(*) into vivantes from public.app_dossier_current;

  -- ⚠⚠ LE GARDE-FOU, ET IL EST LA RAISON D'ETRE DU PLANCHER.
  -- Si le run de nuit echoue a mi-chemin, app_dossier_current peut etre vide ou tronquee.
  -- Sans ce test, la fonction horodaterait TOUT LE PARC comme sorti de la vitrine, et la
  -- purge effacerait six mois plus tard les derives de toutes les annonces en vente.
  -- Le parc vivant mesure 13 438 annonces le 26/09 ; 5 000 est un plancher large qui
  -- laisse passer une vraie baisse d'activite mais arrete un index casse.
  if vivantes < plancher then
    return jsonb_build_object(
      'statut', 'refus',
      'raison', 'app_dossier_current sous le plancher : le run de nuit a probablement echoue',
      'vivantes', vivantes,
      'plancher', plancher);
  end if;

  -- une annonce qui REDEVIENT vivante libere ses photos : on efface l'ancre AVANT de
  -- marquer, pour qu'un aller-retour dans la meme nuit ne laisse pas de date perimee.
  update public.app_console_photo p
     set hors_vitrine_depuis = null
   where p.hors_vitrine_depuis is not null
     and exists (select 1 from public.app_dossier_current d
                  where d.app_dossier_id = p.app_dossier_id);
  get diagnostics liberees = row_count;

  -- une annonce qui n'est plus vivante prend sa date, UNE SEULE FOIS : on ne re-date
  -- jamais une photo deja marquee, sinon l'horloge des six mois repartirait chaque nuit
  -- et la purge n'arriverait jamais.
  update public.app_console_photo p
     set hors_vitrine_depuis = maintenant
   where p.hors_vitrine_depuis is null
     and not exists (select 1 from public.app_dossier_current d
                      where d.app_dossier_id = p.app_dossier_id);
  get diagnostics marquees = row_count;

  return jsonb_build_object(
    'statut', 'ok',
    'vivantes', vivantes,
    'marquees_sorties', marquees,
    'liberees_revenues', liberees,
    'total_hors_vitrine', (select count(*) from public.app_console_photo
                            where hors_vitrine_depuis is not null));
end;
$$;

comment on function public.app_photo_marquer_sortie_vitrine() is
  'G.8 : pose l''ancre des six mois sur les photos dont l''annonce n''est plus en vente, '
  'et la retire si elle le redevient. NE SUPPRIME RIEN. Refuse d''agir si '
  'app_dossier_current est sous son plancher (run de nuit casse).';

revoke all on function public.app_photo_marquer_sortie_vitrine() from public;
grant execute on function public.app_photo_marquer_sortie_vitrine() to service_role;


-- ── 3. LE TRAVAIL NOCTURNE ────────────────────────────────────────────────────
-- 08 h 30 : apres le run (fini vers 07 h 04) et apres la descente (07 h 30), donc
-- app_dossier_current est a jour. Le moniteur decouvre les travaux pg_cron
-- DYNAMIQUEMENT (check_gti_health.py:1672) -> celui-ci est surveille des le 1er jour,
-- sur « dernier run en echec » et « pas de run depuis N min ».
select cron.schedule('app-photo-sortie-vitrine', '30 8 * * *',
                     'select public.app_photo_marquer_sortie_vitrine();');
