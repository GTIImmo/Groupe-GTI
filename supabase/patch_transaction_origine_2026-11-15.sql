-- ════════════════════════════════════════════════════════════════════════════
-- C.19-d PIECES 1 ET 2 -- LA MARQUE D'ORIGINE D'UNE TRANSACTION      15/11/2026
-- ════════════════════════════════════════════════════════════════════════════
-- Prepare le rapatriement des 241 transactions du classeur (chantier classeur,
-- lot B). Deux blocs, dans cet ordre : la colonne, puis la sentinelle qui la lit.
--
-- ─── POURQUOI CETTE COLONNE ───
-- Le registre distingue mal DEUX situations qui n'ont rien a voir :
--     « elle ATTEND son numero Hektor »  -> anormal si ca dure. C'est la securite
--                                            posee par Frederic : un geste de l'app
--                                            doit partir chez Hektor et revenir avec
--                                            son numero, sinon il n'est pas modifiable.
--     « elle n'en aura JAMAIS »          -> assume. Une reprise de l'historique
--                                            (le classeur) n'ira pas chez Hektor.
--
-- Aujourd'hui les deux se ressemblent exactement : `hektor_affaire_id is null`
-- + `present_in_hektor = false`, soit mot pour mot ce que l'app ecrit a chaque
-- clic (app_change_annonce_status_optimistic, « Hektor ne la connait pas encore :
-- la case reste VIDE » / « delete-never : le run de nuit la conservera »).
--
-- ─── CE QU'ON NE FAIT PAS, ET POURQUOI ───
-- ⚠⚠ ON N'ELARGIT PAS LA SENTINELLE A LA PLAGE APP. C'etait ma premiere
--   proposition du 15/11, et Frederic l'a arretee : elle aurait eteint la garde
--   pour TOUS les gestes vivants, donc aussi pour celui qui aurait ECHOUE a
--   partir chez Hektor. On distingue l'INTENTION, pas la plage de numeros.
-- ⚠⚠ ON NE TOUCHE PAS A `present_in_hektor` : colonne lue 575 fois dans
--   150 fichiers (mesure du 15/11), et le couple « pas de numero + false » est
--   DEJA le langage du projet pour dire « nee chez nous » (App.tsx:24444,
--   ModaleStatutV2.tsx:941 : « nee dans l'app, sans numero Hektor »).
-- ⚠ LA VUE GARDE SES 7 COLONNES, memes noms, meme ordre : `create or replace`
--   preserve alors les droits, et la doublure locale ne change pas de forme
--   (la vue est descendue en local -- pull_from_supabase.py:156).
--
-- ─── CE QUE CA TOUCHE AILLEURS ───
--   la regle du moniteur   data.affaire_sans_numero_hektor (check_gti_health.py:494)
--                          rule absolute, max 0 -- INCHANGEE, elle garde son seuil
--   le filet du worker     poserNumerosManquants (console_job_worker.js:24109)
--                          NON TOUCHE par ce patch : c'est la piece 3, a part
--   la doublure locale     app_affaire_ledger__sb, refaite depuis la spec OpenAPI
--                          -> elle prendra la colonne toute seule
--   le push du run         il fait SELECT * sur la table LOCALE et envoie tout
--                          (ledger_rows_for_push, affaire_ledger.py:2932)
--                          ⚠⚠ TANT QUE LA COLONNE N'EXISTE PAS EN LOCAL, le push ne
--                          peut pas l'ecraser. Le jour ou on l'ajoutera en local,
--                          elle DOIT entrer dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS
--                          AVANT tout remplissage -- meme patron que l'etiquette
--                          de dossier (09/11) et l'annulation (10/11), et meme
--                          raison : le 07/09, un `--push` a EFFACE une annulation
--                          faite une heure plus tot.
--
-- ─── RETOUR ARRIERE ───
-- `patch_transaction_origine_2026-11-15_INVERSE.sql` : il remet la vue d'origine et
-- ne retire la colonne QUE si personne ne l'a remplie (il le verifie et le dit).
-- ════════════════════════════════════════════════════════════════════════════

-- ─── BLOC 1 : LA COLONNE ───
-- Additive, nullable, sans valeur par defaut : aucune ligne existante ne change.

alter table public.app_affaire_ledger
  add column if not exists transaction_origine text;

comment on column public.app_affaire_ledger.transaction_origine is
  'D''ou vient la transaction, et ce que ca implique (C.19-d, 15/11/2026) : '
  'classeur (reprise de l''historique depuis le Google Sheet -- elle n''est '
  'JAMAIS allee chez Hektor et n''y sera pas creee, donc pas de numero Hektor, '
  'pas de modification possible dans l''app, et elle sort de la sentinelle '
  'app_affaires_sans_numero_hektor) . NULL = le cas normal, nee dans l''app ou '
  'chez Hektor : elle DOIT avoir son numero Hektor, et la sentinelle veille.';

-- ─── BLOC 2 : LA SENTINELLE ───
-- ⚠⚠ GARDE-FOU D'EMPREINTE : si quelqu'un est passe avant moi sur cette vue,
--   le bloc S'ARRETE au lieu d'ecraser son travail.

do $$
declare
  d text;
begin
  select pg_get_viewdef('public.app_affaires_sans_numero_hektor'::regclass, true) into d;
  if position('transaction_origine' in d) > 0 then
    raise notice 'BLOC 2 DEJA POSE : la vue filtre deja sur transaction_origine. Rien a faire.';
  elsif position('hektor_affaire_id IS NULL' in d) = 0 then
    raise exception 'ARRET : la vue app_affaires_sans_numero_hektor n''a pas la forme attendue. Quelqu''un est passe avant. Definition lue : %', d;
  else
    create or replace view public.app_affaires_sans_numero_hektor as
      select app_affaire_id, app_dossier_id, kind, state, montant, date, first_seen_at
        from public.app_affaire_ledger
       where hektor_affaire_id is null
         and transaction_origine is null;
    raise notice 'BLOC 2 POSE : la sentinelle ignore desormais les transactions marquees.';
  end if;
end $$;

comment on view public.app_affaires_sans_numero_hektor is
  'Sentinelle (seuil 0, check_gti_health.py) : une transaction SANS numero '
  'Hektor est une anomalie -- un geste de l''app qui n''est pas parti, ou qui '
  'n''est pas revenu. Depuis le 15/11/2026 elle ignore les lignes dont '
  'transaction_origine est renseigne : celles-la n''auront jamais de numero, '
  'et c''est DECLARE. ⚠ Le seuil reste 0 pour tout le reste, PLAGE APP '
  'COMPRISE : un geste vivant sans numero leve TOUJOURS la main.';
