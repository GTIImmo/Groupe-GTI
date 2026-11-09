-- ═══════════════════════════════════════════════════════════════════════════════
-- LE SUIVI DE L'AFFAIRE — les champs À NOUS que Hektor ne porte pas   09/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Décidé par Frédéric le 09/11/2026, après la revue des 38 colonnes du classeur :
-- huit d'entre elles n'ont AUCUNE case en face chez nous. Sa consigne, le 09/11 :
-- « Cinq cases » pour les cinq colonnes de texte, et chacune des trois autres la
-- sienne.
--
-- ⛔⛔ CE PATCH A ÉTÉ ÉCRIT UNE PREMIÈRE FOIS AVEC `app_chaine_id` EN CLÉ PRIMAIRE,
--   ET C'ÉTAIT INTERDIT PAR UNE RÈGLE DÉJÀ ÉCRITE DANS CE PROJET. Frédéric, 09/11 :
--   « as-tu audité mon projet et retrouvé nos notes au sujet des id du registre des
--   affaires en conservant le principe de chaînage ? ce n'était pas si simple. »
--   Il avait raison. notice/AUDIT_CHAINAGE_ARCHITECTURE_2026-10-28.md § 5 :
--
--      « Un numéro de chaîne ne doit JAMAIS servir de point d'accrochage à quoi que
--        ce soit d'extérieur. Ce n'est pas un défaut du chaînage : c'est sa nature,
--        et elle est assumée. C'est à CE QUI S'ACCROCHE de pointer les transactions. »
--
--   ⚠ ET J'AVAIS MAL BORNÉ LE RISQUE. J'avais mesuré que le numéro de chaîne ne
--   bouge que si sa PREMIÈRE transaction DISPARAÎT (13 chaînes sur 4 688). Faux : il
--   bouge aussi quand une transaction ARRIVE avec un numéro plus petit, et le projet
--   l'a mesuré — 34 dossiers dont la tête est arrivée après les autres (exemple 29046 :
--   une vente de 2009 remontée le 15/09 a pris la tête d'une offre et d'un compromis
--   déjà là). Plus une FUSION en production le 25/10 : 12 160 dossiers -> 12 159.
--   ⛔ Et notice/AUDIT_CHAINAGE_ARCHITECTURE § 6 dit qu'AUCUN JOURNAL ne compte les
--   chaînes qui changent de numéro chaque nuit. Le risque n'est donc pas borné du tout.
--
-- ─── LA CLÉ RETENUE : `id_unique`, LA LIGNE DU CLASSEUR ───
-- notice/ANALYSE_LIEN_PAR_DOSSIER_OU_PAR_TRANSACTION_2026-10-29.md § 3 décrit déjà
-- cette table : c'est sa « TABLE 1 », UNE ligne par ligne de classeur, la FORME du
-- classeur. Sa clé « ID Unique » est gelée et immuable (décision du projet : « AL ID
-- Unique, LA CLÉ DU PONT — ne jamais y toucher »).
-- ⭐ Et les transactions se retrouvent par `app_classeur_lien`, qui est la « TABLE 2 »
--   de cette même note : la PREUVE et la PRÉCISION, gelée sur `app_affaire_id`, qui
--   lui NE bouge jamais. Les deux tables ont chacune leur rôle, comme prévu.
-- ⚠ CE QUE CETTE CLÉ NE COUVRE PAS, et c'est VOULU : une affaire née dans l'app n'a
--   pas de ligne au classeur, donc pas de place ici. C'est le bon périmètre pour la
--   PHASE A, qui est un rattrapage UNE SEULE FOIS. La suite a déjà un nom et un rang
--   dans le projet — voir ci-dessous.
--
-- ─── ⭐ LA CONFORMITÉ AU SYSTÈME DE CHAÎNAGE — vérifiée le 09/11 sur sa demande ───
-- Frédéric, 09/11 : « est-ce que ton patch est conforme au système de chaînage ? »
-- TROIS points vérifiés, et un défaut trouvé (corrigé, contrôles ⑩ et ⑪ ci-dessous) :
--
-- ① ✅ LA TABLE NE S'ACCROCHE PLUS À UN NUMÉRO DE CHAÎNE. Plus aucune colonne
--    `*chaine*`, et le contrôle ③ le vérifie. La règle du 28/10 est respectée.
--
-- ② ✅ LE CHAÎNAGE POURRA REMONTER JUSQU'ICI. Le recalcul tourne EN LOCAL
--    (`recalculer_les_chaines(con: sqlite3.Connection)`, base `phase2/phase2.sqlite`,
--    6,7 Go), et j'ai vérifié que `app_classeur_lien` Y EXISTE DÉJÀ — donc le chemin
--    chaîne -> transactions -> ligne du classeur -> ici est possible sans plomberie
--    nouvelle.
--    ⚠ MAIS `app_affaire_suivi` doit DESCENDRE en local. Elle descendra seule : la
--    descente (scheduled/run_descente.ps1, 07:30) découvre les tables du schéma.
--    ⛔ ET ELLE DESCEND APRÈS LE RUN (05:00). Le run lira donc la table telle qu'elle
--    était la veille — SANS CONSÉQUENCE pour une date d'annulation venue du classeur,
--    qui ne change jamais. ⚠ À reprendre en PHASE B, où l'app écrirait la date : elle
--    mettrait alors 24 h à agir sur le chaînage.
--
-- ③ ⚠ LES DEUX COPIES DE LA FORMULE N'AURONT PAS LE MÊME ACCÈS AUX DONNÉES.
--    `recalculer_les_chaines()` lit le LOCAL (table descendue, un jour de retard) ;
--    `app_chaine_pour()` tourne dans Supabase et lirait la table EN DIRECT. Elles
--    peuvent donc diverger sur une date saisie dans la journée. Nul en phase A (la
--    date vient du classeur, une fois), réel en phase B.
--    ⛔ C'est exactement l'avertissement du patch du 05/09 : « Deux copies d'une
--    formule divergent tôt ou tard : toute correction ici doit être reportée là-bas. »
--
-- ─── ⬜ CE QUI VIENDRA APRÈS, ET QUI N'EST PAS CE PATCH ───
-- L'identifiant d'affaire propre à notre registre s'appelle `app_dossier_affaire_id`
-- dans la note du 29/10 : « l'étiquette STABLE ». Elle y est déclarée NÉCESSAIRE —
-- plus optionnelle — parce que la PHASE B en dépend : après une fusion, le worker
-- verrait UN dossier lié à DEUX lignes du classeur et ne saurait pas laquelle écrire.
-- ⭐ MAIS SON RANG EST FIXÉ, ET IL EST APRÈS CE PATCH. L'ordre de la note, § 4 :
--      1. corriger les 8 liens très suspects
--      2. geler sur les TRANSACTIONS                        ✅ FAIT (12 422 liens)
--      3. le rapport des écarts + la mise en conformité      <- LA PHASE A EST FINIE
--      4. PUIS l'étiquette de dossier, construite À PARTIR des liens déjà gelés
--      5. la table 1 complète, et seulement alors la PHASE B
--   « et c'est plus facile dans cet ordre : les liens de l'étape 2 DONNENT les groupes
--     à étiqueter, déjà vérifiés par toi. »
-- ⬜ NON MESURÉ, et la note le signale comme à faire AVANT la phase B, pas avant la A :
--   à quelle fréquence une fusion toucherait réellement DEUX lignes du classeur.
--
-- ─── POURQUOI PAS LE CARNET (app_affaire_champ_app) ───
-- Le carnet était le candidat naturel : il est à nous, il fonctionne par NOM DE CHAMP
-- (donc sans migration), et il porte déjà sept champs que Hektor ignore.
-- ⛔ MESURÉ LE 09/11, ET IL NE CONVIENT PAS : son ménage de nuit
-- (phase2/identite/nettoyer_carnet_affaire.py:175) retire toute ligne dont l'affaire
-- est `cancelled` ou `refused` — ETATS_MORTS. Sur les 833 lignes « Annulée » :
--     522 lignes (62,7 %)  seraient PERDUES EN ENTIER
--     208 lignes (25,0 %)  seraient AMPUTÉES
--     103 lignes (12,4 %)  tiendraient
-- ⭐ TÉMOIN INVERSE : sur les lignes NON annulées, 99,9 % tiendraient. Le carnet
--   convient pour une vente réglée, pas pour une annulation — et l'annulation est
--   précisément ce qu'on vient chercher. Sa logique n'est pas absurde : le carnet sert
--   à ATTENDRE que Hektor confirme une saisie, et une affaire morte n'attendra plus
--   rien. Nos huit colonnes, elles, ne sont pas en attente : Hektor ne les connaîtra
--   JAMAIS. Deuxième raison, de taille : le carnet porte 48 lignes aujourd'hui, et ces
--   colonnes en représentent ~20 600.
--
-- ─── CE QUI N'EST PAS DANS CE PATCH, ET C'EST VOULU ───
-- ⛔ AUCUN CHAMP D'ÉTAT. Frédéric, 09/11 : « c'est la date d'annulation qui fait
--   l'état actuel annulé ». Deux champs pourraient se contredire, un seul ne peut pas.
-- ⛔ AUCUNE ÉCRITURE DE DONNÉE. Ce patch pose la table VIDE. Le rattrapage est un
--   geste à part (P1.4), famille par famille, avec la liste sous les yeux.
-- ⛔ AUCUN CHANGEMENT D'ÉTAT des transactions. Sa consigne du 09/11 — « on clôture le
--   dossier, on passe compromis en annulé et offre d'achat en refusé en même temps » —
--   est un GESTE, pas un champ. Il touche le registre (relu chaque nuit) et peut-être
--   Hektor : il a sa propre étude. Mesure du 09/11 : il ne concerne que 311 des 833
--   lignes, les 522 autres étant DÉJÀ dans le bon état.
-- ⛔ AUCUN AFFICHAGE. On écrit d'abord, on montre ensuite.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_affaire_suivi_2026-11-09_INVERSE.sql — la table est neuve et vide,
-- donc le retour est un simple DROP, sans perte possible.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;

-- ─────────────────────────────────────────────────────── ① LA TABLE
create table if not exists public.app_affaire_suivi (
  -- ⭐ LA CLÉ : la ligne du classeur, gelée et immuable. PAS app_chaine_id, qui est
  --   une déduction refaite chaque nuit (voir l'en-tête).
  id_unique          text    primary key,

  -- ─── LES DEUX DATES ET NUMÉROS
  -- ⛔⛔ `date_annulation` A ÉTÉ RETIRÉE DE CETTE TABLE LE 09/11, et c'est une
  --   DÉCISION DE FRÉDÉRIC : « il faut aussi ajouter dans le registre des colonnes
  --   date d'annulation, qui permet d'annuler le dossier dans le registre des
  --   transactions et de faire une modification de l'état des transactions dans la
  --   chaîne. »
  --   ⭐ SA PLACE EST DANS app_affaire_ledger, PAS ICI, pour trois raisons mesurées :
  --     ① la règle de chaînage la lirait dans la table qu'elle lit DÉJÀ — quatre
  --        sauts en moins (chaîne -> transactions -> gel -> cette table) ;
  --     ② le registre est DÉJÀ en local, donc pas d'attente de la descente de 07:30
  --        alors que le run tourne à 05:00 ;
  --     ③ elle est alors PAR TRANSACTION, ce qui est exactement ce que la cascade
  --        demande : marquer l'offre, le compromis et la vente du même dossier.
  --   Elle sera protégée du run par OMISSION (absente du ON CONFLICT), le patron que
  --   le projet nomme ainsi et qui protège déjà six colonnes.
  --   Spécification : notice/SPEC_ANNULATION_AFFAIRE_2026-11-09.md
  date_vente_reglee  date,       -- ⚠ ce n'est PAS notre date d'acte : +3 j de médiane
  numero_facture     text,       -- ⚠ du numéro ET du texte dans la même case

  -- ─── LES CINQ COLONNES DE TEXTE — « cinq cases », sa décision du 09/11
  -- ⛔ REPRISES EN BLOC, SANS INTERPRÉTER : c'est sa consigne, et elle évite de leur
  --   inventer une sémantique. Ce sont des notes humaines, pas des codes.
  en_attente_de      text,       -- « V » = Vendu (1 537 lignes sur 1 537)
  commentaires       text,       -- la seule trace du POURQUOI, jusqu'à 1 450 car.
  avis_a_envoyer     text,       -- 120 valeurs distinctes, pas un oui/non
  avis_commentaire   text,
  avis_envoye        text,       -- contient des PRÉNOMS (Marion 190, Nico 59)

  -- ─── LA TRAÇABILITÉ — on doit toujours savoir D'OÙ vient une valeur
  origine            text    not null default 'classeur',
  ecrit_le           timestamptz not null default now(),
  ecrit_par          text,

  -- ⭐ une ligne qui ne porte RIEN n'a pas de raison d'exister
  constraint app_affaire_suivi_pas_vide check (
    date_vente_reglee is not null
    or numero_facture is not null or en_attente_de is not null
    or commentaires is not null or avis_a_envoyer is not null
    or avis_commentaire is not null or avis_envoye is not null
  ),
  constraint app_affaire_suivi_origine check (
    origine in ('classeur', 'app', 'rattrapage', 'essai')
  ),
  constraint app_affaire_suivi_id_unique_non_vide check (btrim(id_unique) <> '')
);

comment on table public.app_affaire_suivi is
  'Les champs de suivi d''une AFFAIRE qui sont À NOUS : Hektor ne les porte pas, donc '
  'rien ne les rafraîchit et rien ne les efface. Source : le classeur de suivi des '
  'ventes (8 colonnes sur 38). Posée le 09/11/2026. '
  '⛔ Clé = « ID Unique » du classeur, JAMAIS app_chaine_id (règle du 28/10 : un numéro '
  'de chaîne ne sert jamais de point d''accrochage). Les transactions se retrouvent par '
  'app_classeur_lien. ⬜ L''étiquette app_dossier_affaire_id viendra à l''étape 4 du '
  'plan du 29/10, APRÈS la phase A. ⛔ Pas de champ d''état : la date d''annulation '
  'FAIT l''état annulé.';

comment on column public.app_affaire_suivi.id_unique is
  'La clé « ID Unique » de la ligne du classeur. Même clé que app_classeur_lien, donc '
  'les transactions de l''affaire se lisent là-bas, avec leur rôle.';

-- ─────────────────────────────────────────────────────── ② L'INDEX
-- ⭐ retrouver une ligne depuis le classeur reste utile ; l'index sur les
--   annulations n'a plus lieu d'etre ici (la date vit au registre).
create index if not exists app_affaire_suivi_id_unique_idx
  on public.app_affaire_suivi (id_unique);

-- ─────────────────────────────────────────────────────── ③ LES DROITS
-- ⛔ `revoke all from public` NE FERME PAS `authenticated` : chaque rôle se nomme.
alter table public.app_affaire_suivi enable row level security;
revoke all on table public.app_affaire_suivi from public;
revoke all on table public.app_affaire_suivi from anon;
revoke all on table public.app_affaire_suivi from authenticated;

-- ⭐ AUCUNE POLITIQUE N'EST POSÉE, et c'est voulu : RLS activée sans politique =
--   personne ne lit, personne n'écrit, sauf le service_role (qui l'ignore). La lecture
--   par l'écran se décidera avec l'affichage, dans un second temps. Tant qu'on
--   n'affiche rien, personne n'a besoin d'y accéder.

commit;

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être vert.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① la table existe'                                  as controle,
       count(*)                                              as trouve,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end   as verdict
  from information_schema.tables
 where table_schema = 'public' and table_name = 'app_affaire_suivi'
union all
select '② elle a 11 colonnes', count(*),
       case when count(*) = 11 then 'VERT' else 'ROUGE' end
  from information_schema.columns
 where table_schema = 'public' and table_name = 'app_affaire_suivi'
union all
-- ⛔⛔ LE CONTRÔLE QUI DIT QUE LA FAUTE EST RÉPARÉE : aucune colonne de cette table
--    ne doit s'accrocher à un numéro de chaîne (règle du 28/10).
select '③ ni colonne de chaîne, ni date d''annulation (elle vit au registre)', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.columns
 where table_schema = 'public' and table_name = 'app_affaire_suivi'
   and (column_name like '%chaine%' or column_name like '%annulation%')
union all
select '④ la clé primaire est bien id_unique', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from information_schema.key_column_usage k
  join information_schema.table_constraints t
       on t.constraint_name = k.constraint_name and t.table_schema = k.table_schema
 where k.table_schema = 'public' and k.table_name = 'app_affaire_suivi'
   and t.constraint_type = 'PRIMARY KEY' and k.column_name = 'id_unique'
union all
select '⑤ elle est VIDE (ce patch n''écrit aucune donnée)', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from public.app_affaire_suivi
union all
select '⑥ RLS est activée', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname = 'app_affaire_suivi' and c.relrowsecurity
union all
select '⑦ aucune politique (donc personne n''accède)', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from pg_policies
 where schemaname = 'public' and tablename = 'app_affaire_suivi'
union all
select '⑧ ni anon ni authenticated n''ont de droit', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants
 where table_schema = 'public' and table_name = 'app_affaire_suivi'
   and grantee in ('anon', 'authenticated', 'PUBLIC')
union all
-- ⭐⭐ LE TÉMOIN QUI COMPTE : la clé que cette table attend existe-t-elle vraiment
--    dans le gel, et combien de lignes pourra-t-elle recevoir ?
select '⑨ TÉMOIN : le gel porte bien des « ID Unique » distincts',
       count(distinct id_unique),
       case when count(distinct id_unique) > 4000 then 'VERT' else 'ROUGE' end
  from public.app_classeur_lien
union all
-- ⛔⛔ LES DEUX TÉMOINS DE CONFORMITÉ AU CHAÎNAGE. Frédéric, 09/11 : « est-ce que
--    ton patch est conforme au système de chaînage ? » — et ils manquaient.
--    ⭐ POURQUOI ILS SONT INDISPENSABLES : la fermeture d'une chaîne par
--    `date_annulation` devra remonter chaîne -> transactions -> app_classeur_lien
--    -> id_unique -> ici. Si une chaîne portait DEUX lignes du classeur, elle
--    aurait DEUX dates d'annulation candidates et la règle ne saurait pas laquelle
--    prendre. Aujourd'hui la correspondance est 1 ↔ 1 (mesuré le 09/11 : 4 688
--    lignes ↔ 4 688 chaînes, zéro exception sur 12 422 transactions), mais c'est
--    exactement ce qu'une FUSION casserait — le cas dangereux nommé par
--    notice/ANALYSE_LIEN_PAR_DOSSIER_OU_PAR_TRANSACTION_2026-10-29.md § 1 ③.
--    ⛔ Ces deux contrôles doivent donc être REJOUÉS avant d'allumer la fermeture,
--    pas seulement aujourd'hui.
select '⑩ CONFORMITÉ : 1 ligne du classeur = 1 chaîne, sans exception',
       count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from (select l.id_unique
          from public.app_classeur_lien l
          join public.app_affaire_ledger g on g.app_affaire_id = l.app_affaire_id
         group by l.id_unique
        having count(distinct g.app_chaine_id) <> 1
            or count(*) filter (where g.app_chaine_id is null) > 0) as mauvaises
union all
select '⑪ CONFORMITÉ, le TÉMOIN INVERSE : 1 chaîne = 1 ligne du classeur',
       count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from (select g.app_chaine_id
          from public.app_classeur_lien l
          join public.app_affaire_ledger g on g.app_affaire_id = l.app_affaire_id
         where g.app_chaine_id is not null
         group by g.app_chaine_id
        having count(distinct l.id_unique) <> 1) as partagees
 order by 1;
