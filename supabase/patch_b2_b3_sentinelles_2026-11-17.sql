-- ═══════════════════════════════════════════════════════════════════════════
-- B2 ET B3 -- LES DEUX SENTINELLES DU CHANTIER CLASSEUR -- 17/11/2026
--
-- ⛔ CE PATCH N'ECRIT AUCUNE DONNEE. Il pose DEUX VUES et rien d'autre : pas une
--   valeur, pas une colonne, pas un droit sur une table existante. Le registre
--   ne gagne rien -- c'est un VOYANT qu'on ajoute, pas un rapatriement.
--
-- LE PATRON EST COPIE DE `app_v_repartition_orpheline`, qui est en service :
--   des colonnes qui NOMMENT la ligne (pour agir sans requete) + un `diagnostic`
--   en francais. « Une alerte qui dit 1 sans dire lequel oblige a chercher. »
--
-- ═══════════════════════════════════════════════════════════════════════════
-- B2 -- LES LIGNES DU CLASSEUR QUI NE RECEVRONT JAMAIS RIEN
--   85 lignes sur 4 773 n'ont AUCUN lien vers une transaction. Donc aucune date,
--   aucun motif, aucune note ne les atteindra jamais -- et personne ne le voit.
--
-- ⚠ LE SEUIL EST 85, PAS 0, ET C'EST DELIBERE. Un seuil 0 crierait des le premier
--   passage pour un fait CONNU et DECLARE : c'est le defaut que j'ai reproche ce
--   matin meme a la sentinelle des negociateurs (« un essai qui crie tous les
--   jours n'est plus un essai »). Ce qu'on veut detecter est une HAUSSE : une
--   ligne qui PERD son lien. Le re-gel (D1) doit faire BAISSER ce nombre ; il
--   faudra alors baisser le seuil, et c'est ecrit dans le commentaire du code.
--
-- B3 -- LES NOTES ET LES CONDITIONS ORPHELINES
--   6 notes et 5 conditions pointent une transaction QUI N'EXISTE PLUS.
--
-- ⭐⭐⭐ ET LA MESURE A CORRIGE CE QUE J'ALLAIS ECRIRE : ce ne sont pas des
--   donnees metier perdues, ce sont des RESTES D'ESSAIS du 23/10, tous sur le
--   dossier 1068399, tous `origine = 'saisie'`. Leurs textes le disent eux-memes :
--     « Essai 3 du 23/10 : compromis - note libre (a nettoyer) »
--     « Essai 4 du 23/10 : vente - note libre (A GARDER POUR LA PREUVE) »   <- ⛔
--   ⛔ JE NE LES SUPPRIME DONC PAS : l'une demande expressement d'etre gardee, et
--     le nettoyage d'un essai est une decision de Frederic, pas la mienne.
--   ➡ On les DECLARE une fois pour toutes (liste figee ci-dessous), et la
--     sentinelle ne compte que les orphelines NEUVES -- seuil 0, vrai des le
--     premier jour. « Exclure est une decision, et elle se declare. »
--
-- ⭐ POURQUOI MAINTENANT : a l'etape 4, l'app ecrira elle-meme des notes et des
--   conditions. C'est la qu'une orpheline peut naitre sans que personne ne la
--   voie. Le plan le disait : « A POSER AVANT d'ecrire ».
--
-- RETOUR ARRIERE : patch_b2_b3_sentinelles_2026-11-17_INVERSE.sql
-- CONTROLES      : patch_b2_b3_sentinelles_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① B2 : LES LIGNES DU CLASSEUR SANS AUCUN LIEN
create or replace view public.app_v_classeur_ligne_sans_lien as
select g.id_unique,
       g.ligne_classeur,
       'aucun lien vers une transaction -- cette ligne ne recevra JAMAIS'::text
         as diagnostic
  from public.app_classeur_ligne_id g
 where not exists (select 1 from public.app_classeur_lien l
                    where l.id_unique = g.id_unique);

comment on view public.app_v_classeur_ligne_sans_lien is
  'B2 (17/11/2026) : les lignes du classeur qu''aucun lien ne rattache a une '
  'transaction -- elles ne recevront jamais ni date, ni motif, ni note. '
  '85 au 17/11 sur 4 773. Le re-gel (D1) doit faire BAISSER ce nombre ; une '
  'HAUSSE veut dire qu''une ligne a PERDU son lien.';

-- ② B3 : LES NOTES ET LES CONDITIONS ORPHELINES
--    ⭐ UNE SEULE VUE pour les deux objets : une colonne `objet` les distingue.
--      Deux vues jumelles, c'est deux endroits a corriger le jour ou la regle
--      change.
create or replace view public.app_v_affaire_note_condition_orpheline as
with essais_declares as (
  -- ⛔ LA LISTE FIGEE DES ORPHELINES CONNUES, mesurees le 17/11/2026.
  --   Ce sont les restes des essais du 23/10 sur le dossier 1068399, dont
  --   l'une porte « a garder pour la preuve ». Elles sont DECLAREES, pas
  --   masquees : la vue les montre avec leur propre diagnostic.
  select unnest(array[1001388, 1001389, 1001391, 1001392, 1001394, 1001395]::bigint[]) as id
)
select 'note'::text as objet,
       n.app_affaire_id,
       n.app_chaine_id,
       n.app_dossier_id,
       coalesce(n.origine, '(vide)') as origine,
       n.ecrit_le,
       left(coalesce(n.texte, ''), 120) as apercu,
       case when n.app_affaire_id in (select id from essais_declares)
            then 'essai du 23/10, CONNU et declare -- son nettoyage est une decision'
            else 'ORPHELINE NEUVE -- sa transaction a disparu, un humain doit trancher'
       end as diagnostic,
       (n.app_affaire_id in (select id from essais_declares)) as deja_declaree
  from public.app_affaire_note n
 where not exists (select 1 from public.app_affaire_ledger l
                    where l.app_affaire_id = n.app_affaire_id)
union all
select 'condition'::text,
       c.app_affaire_id,
       c.app_chaine_id,
       c.app_dossier_id,
       coalesce(c.origine, '(vide)'),
       c.ecrit_le,
       left(coalesce(c.libelle, ''), 120),
       case when c.app_affaire_id in (select id from essais_declares)
            then 'essai du 23/10, CONNU et declare -- son nettoyage est une decision'
            else 'ORPHELINE NEUVE -- sa transaction a disparu, un humain doit trancher'
       end,
       (c.app_affaire_id in (select id from essais_declares))
  from public.app_affaire_condition c
 where not exists (select 1 from public.app_affaire_ledger l
                    where l.app_affaire_id = c.app_affaire_id);

comment on view public.app_v_affaire_note_condition_orpheline is
  'B3 (17/11/2026) : les notes et les conditions dont la transaction n''existe '
  'plus. Les 11 connues au 17/11 sont des restes d''essais du 23/10 (dossier '
  '1068399), DECLAREES via deja_declaree -- dont une porte « a garder pour la '
  'preuve ». La sentinelle ne compte que deja_declaree = false, donc seuil 0.';

-- ③ LES DROITS : lecture pour les administrateurs de l'app, rien pour anon
--    ⛔ `revoke from public` ne ferme pas `authenticated` -- faute payee deux
--      fois. On revoque donc public ET anon NOMMEMENT.
revoke all on public.app_v_classeur_ligne_sans_lien from public, anon;
revoke all on public.app_v_affaire_note_condition_orpheline from public, anon;
grant select on public.app_v_classeur_ligne_sans_lien to authenticated, service_role;
grant select on public.app_v_affaire_note_condition_orpheline to authenticated, service_role;

-- ④ LES CONTROLES, DANS LA MEME TRANSACTION
do $$
declare n integer; m integer;
begin
  -- ⭐⭐ LE TEMOIN POSITIF : les deux vues doivent RENDRE QUELQUE CHOSE. Une vue
  --   qui rend 0 pourrait etre cassee sans qu'on le sache.
  select count(*) into n from public.app_v_classeur_ligne_sans_lien;
  if n <> 85 then
    raise exception '⛔ B2 rend % lignes au lieu des 85 mesurees -- la vue est fausse', n;
  end if;

  select count(*) into n from public.app_v_affaire_note_condition_orpheline;
  if n <> 11 then
    raise exception '⛔ B3 rend % orphelines au lieu des 11 mesurees', n;
  end if;

  -- ⭐ et LES 11 SONT TOUTES DECLAREES : la sentinelle doit donc lire 0
  select count(*) into m from public.app_v_affaire_note_condition_orpheline
   where not deja_declaree;
  if m <> 0 then
    raise exception '⛔ % orpheline(s) NON declaree(s) des la pose -- a regarder', m;
  end if;

  -- ⭐ le detail par objet, pour que le compte rendu le dise
  select count(*) into n from public.app_v_affaire_note_condition_orpheline
   where objet = 'note';
  select count(*) into m from public.app_v_affaire_note_condition_orpheline
   where objet = 'condition';
  if n <> 6 or m <> 5 then
    raise exception '⛔ B3 : % notes et % conditions au lieu de 6 et 5', n, m;
  end if;

  -- ⛔ TEMOIN INVERSE : anon ne doit rien pouvoir lire
  if has_table_privilege('anon', 'public.app_v_classeur_ligne_sans_lien', 'SELECT')
     or has_table_privilege('anon', 'public.app_v_affaire_note_condition_orpheline', 'SELECT') then
    raise exception '⛔ anon peut lire une des deux vues -- le revoke n a pas tenu';
  end if;
  if not has_table_privilege('authenticated', 'public.app_v_classeur_ligne_sans_lien', 'SELECT') then
    raise exception '⛔ authenticated ne peut PAS lire B2';
  end if;

  -- ⭐ LA VOISINE EST INTACTE : la sentinelle des repartitions existe toujours
  select count(*) into n from pg_class c join pg_namespace x on x.oid = c.relnamespace
   where x.nspname = 'public' and c.relname = 'app_v_repartition_orpheline';
  if n <> 1 then raise exception '⛔ app_v_repartition_orpheline a disparu'; end if;

  raise notice '✅ B2 : 85 lignes sans lien . B3 : 6 notes + 5 conditions, toutes DECLAREES';
end $$;

commit;
