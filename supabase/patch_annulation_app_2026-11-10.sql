-- ═══════════════════════════════════════════════════════════════════════════
-- LES DEUX COLONNES DE L'ANNULATION, AU REGISTRE          10/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Demande de Frederic (10/11) : « on avait commence a prevoir une colonne dans
-- le registre pour l'annulation ». Elle etait prevue depuis le 09/11 (liste B de
-- notice/A18_LA_LISTE_DES_CASES_A_CREER_2026-11-09.md) et JAMAIS POSEE -- mesure
-- du 10/11 : le registre ne porte que charge_commission_app,
-- honoraires_entree_app et honoraires_sortie_app.
--
-- CE QUE CHACUNE PORTE
--   date_annulation_app    la colonne Z du classeur (« Annulee »), 896 dates,
--                          100 % lisibles. Le classeur fait foi dessus.
--   motif_annulation_app   LA RAISON, qui n'existe nulle part aujourd'hui --
--                          ni au classeur, ni chez Hektor. Decision de Frederic
--                          du 09/11 : « on demande la raison et la date ».
--
-- ⭐ POURQUOI « text » ET NON « date » -- ce n'est pas de la paresse.
--   La colonne voisine `date` du registre est en text, et Hektor y met
--   `0000-00-00`. Une colonne `date` REFUSERAIT cette valeur et ferait tomber le
--   run. Le projet a deja paye cette lecon (memoire
--   date-vide-hektor-0000-refusee-par-timestamptz).
--
-- ⛔⛔ CE QUI PROTEGE CES COLONNES DE HEKTOR -- QUATRE PIECES, PAS UNE
--   1  la colonne chez SUPABASE                     <- CE PATCH
--   2  la colonne EN LOCAL                          <- phase2/sync/affaire_ledger.py
--   3  son nom dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS   (meme fichier)
--   4  absente du ON CONFLICT DO UPDATE SET         <- consequence de 3
--   ⚠ ET L'ORDRE COMPTE : Supabase D'ABORD, le local ensuite. L'inverse est
--     l'etat actuel de app_dossier_uuid -- posee en local, absente ici, et la
--     redescente la reclame pour rien.
--
-- ⚠⚠ LA LECON QUI JUSTIFIE LA PIECE 3, ecrite dans affaire_ledger.py l. 2559 :
--     06:38  un compromis est ANNULE depuis l'app -> « cancelled » chez Supabase
--     07:52  `--push` lance a la main -> il pousse le MIROIR LOCAL de 04:18
--            -> L'ANNULATION EST EFFACEE
--   Une date d'annulation que le push renvoie subirait exactement le meme sort.
--
-- ⛔ CE PATCH NE REMPLIT RIEN. Deux colonnes vides, protegees, pretes.
--   Le remplissage (les 896 dates du classeur) et la regle de cascade sont des
--   decisions a part, non prises a ce jour.
--
-- Retour arriere : patch_annulation_app_2026-11-10_INVERSE.sql
-- Controle       : patch_annulation_app_2026-11-10_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── LE TEMOIN D'AVANT, pour que la repetition ait un point de depart ───────
do $$
declare
  deja int;
begin
  select count(*) into deja
    from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaire_ledger'
     and column_name in ('date_annulation_app', 'motif_annulation_app');
  if deja > 0 then
    raise notice 'ⓘ % colonne(s) sur 2 existent deja -- le patch est idempotent, il ne fera que completer.', deja;
  else
    raise notice 'ⓘ aucune des deux colonnes n''existe : pose complete.';
  end if;
end $$;

-- ─── LA POSE. `if not exists` : rejouable sans dommage ──────────────────────
alter table public.app_affaire_ledger
  add column if not exists date_annulation_app  text,
  add column if not exists motif_annulation_app text;

comment on column public.app_affaire_ledger.date_annulation_app is
  'A NOUS. La date d''annulation de la transaction (colonne Z du classeur de suivi). '
  'text et non date : Hektor met 0000-00-00 dans la colonne `date` voisine, et une '
  'colonne date ferait tomber le run. ⛔ Doit figurer dans '
  'COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (phase2/sync/affaire_ledger.py), sinon un '
  '--push la remplace par le vide du miroir local -- lecon du 07/09/2026.';

comment on column public.app_affaire_ledger.motif_annulation_app is
  'A NOUS. La raison de l''annulation, saisie dans l''app. Elle n''existe NI au '
  'classeur NI chez Hektor : nous sommes la seule source. Decision de Frederic du '
  '09/11/2026. ⛔ Meme protection que date_annulation_app.';

-- ─── LE TEMOIN D'APRES ─────────────────────────────────────────────────────
-- Attendu : les 2 colonnes posees, toutes deux en `text`, toutes deux nullables,
-- et le registre inchange par ailleurs (temoin positif : il garde ses 3 autres
-- colonnes _app).
select 'pose des colonnes d''annulation' as controle,
       count(*) filter (where column_name = 'date_annulation_app'
                          and data_type = 'text' and is_nullable = 'YES')  as date_annulation_attendu_1,
       count(*) filter (where column_name = 'motif_annulation_app'
                          and data_type = 'text' and is_nullable = 'YES')  as motif_annulation_attendu_1,
       count(*) filter (where column_name in ('charge_commission_app',
                                              'honoraires_entree_app',
                                              'honoraires_sortie_app'))    as temoin_positif_attendu_3
from information_schema.columns
where table_schema = 'public' and table_name = 'app_affaire_ledger';

-- ⬜ CE QUI RESTE A FAIRE APRES CE PATCH, ET QUI N'EST PAS ICI :
--   . les deux noms dans phase2/sync/affaire_ledger.py -- la boucle de creation
--     de colonnes ET COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (pieces 2 et 3) ;
--   . le remplissage depuis le classeur (896 dates) -- decision a part ;
--   . la regle de cascade « une transaction annulee entraine ses maillons »
--     -- elle n'est ECRITE NULLE PART a ce jour, et la RPC
--     app_geste_affaire_optimistic n'en fait AUCUNE (mesure du 10/11).
