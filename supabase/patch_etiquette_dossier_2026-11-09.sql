-- ═══════════════════════════════════════════════════════════════════════════
-- L'ÉTIQUETTE DE DOSSIER -- ÉTAPE B2 DU PLAN DU 29/10              09/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Décision de Frédéric, 09/11 : « Oui » aux DEUX identifiants
--   . un UUID, caché, qui ira dans la colonne « affair_uuid » du classeur
--     (mesurée VIDE le 29/10 : 1 cellule sur 4 778, et son nom dit UUID) ;
--   . un numéro court lisible, pour l'écran et pour parler entre humains.
--
-- ⛔⛔ CE PATCH EST DORMANT. Il crée les colonnes, le journal et la fonction.
--     IL NE POSE AUCUNE ÉTIQUETTE : personne n'appelle la fonction. C'est
--     B2 du plan ; le premier remplissage est B3, et il vient APRÈS.
--
-- ⛔ ET IL NE SE COLLE PAS AVANT que app_dossier_uuid / app_dossier_numero
--    soient entrées dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS côté local
--    (affaire_ledger.py). C'est la condition C1 de l'audit du 29/10, et ce
--    n'est pas une précaution de principe :
--        07/09/2026, 06:38  un compromis est annulé depuis l'app
--                    07:52  « --push » lancé à la main pousse le miroir de 04:18
--                    -> l'annulation est EFFACÉE chez Supabase
--    Une étiquette que le push renvoie se fait écraser par un miroir local
--    qui ne la connaît pas encore. ⭐ Le filet d'ordre d'affaire_ledger.py
--    (l. ~2204) protège l'inverse (SQL avant Python) : il demande à Supabase
--    ce qu'il a. Donc l'ordre sûr est : ce patch, PUIS le code local, PUIS B3.
--
-- ═══════════════════════════════════════════════════════════════════════════
-- POURQUOI L'ÉTIQUETTE VIT SUR LA TRANSACTION, ET PAS DANS UNE TABLE À PART
-- ═══════════════════════════════════════════════════════════════════════════
-- Règle du 28/10, écrite après le premier audit du chaînage :
--   « Un numéro de chaîne ne doit JAMAIS servir de point d'accrochage à quoi
--     que ce soit d'extérieur. C'est à CE QUI S'ACCROCHE de pointer les
--     transactions. »
-- Une table (app_chaine_id -> uuid) violerait cette règle : app_chaine_id est
-- le plus petit app_affaire_id du groupe, et il BOUGE -- mesuré : 35 dossiers
-- sur 12 138 par semaine, quand une transaction plus ancienne arrive ou quand
-- la tête disparaît.
-- ⭐ L'étiquette est donc portée PAR CHAQUE TRANSACTION du dossier, comme
--    app_chaine_id l'est. Un dossier = l'ensemble des transactions qui portent
--    la même étiquette. Quand une transaction arrive dans un groupe déjà
--    étiqueté, elle REÇOIT l'étiquette du groupe : app_chaine_id bouge,
--    l'étiquette ne bouge pas. C'est tout le mécanisme.
--
-- ═══════════════════════════════════════════════════════════════════════════
-- L'ANNÉE DU NUMÉRO -- LA CASCADE, MESURÉE LE 09/11 SUR LES 12 138 DOSSIERS
-- ═══════════════════════════════════════════════════════════════════════════
--   ① l'année de la DATE LA PLUS ANCIENNE des transactions du dossier
--        -> 12 029 dossiers (99,1 %)
--   ② sinon l'année de la DATE DE DÉBUT DU MANDAT de l'annonce
--        -> 98 dossiers (0,8 %)
--      ⚠⚠ RÉSERVE MESURÉE, ET ELLE COMPTE : sur les 9 001 dossiers où l'on
--         peut comparer les deux, le mandat donne la MÊME année que la
--         transaction dans 64,6 % des cas seulement (3 013 fois plus tôt,
--         171 fois plus tard). Donc pour ces 98 dossiers l'année du numéro
--         se trompe environ une fois sur trois.
--      -> CONSÉQUENCE À TENIR : l'année du numéro est une ÉTIQUETTE, pas une
--         donnée. Rien ne doit la lire pour conclure quoi que ce soit. La
--         vraie date d'ouverture reste celle des transactions.
--   ③ sinon 0000 -- 11 dossiers (0,09 %), regardés un par un le 09/11 :
--        9 sont des coquilles vides de Hektor (offre sans date, sans montant,
--        sans état) ; 2 comptent vraiment (offre acceptée 270 000 EUR sur
--        l'annonce 59467, compromis actif 1 500 EUR sur 49831).
--      . date_acte ne sauve personne (témoin positif : 10 447 lignes en ont,
--        donc le zéro est fondé) ; date_enregistrement du mandat non plus
--        (témoin : 645 mandats sur 27 476 en ont).
--      ⛔ first_seen_at a été ÉCARTÉ : les 109 muets l'ont TOUS au 2026-07-31,
--        le jour de la première descente. Il daterait notre lecture, pas le
--        dossier, et il fabriquerait 109 faux D2026.
--
-- ═══════════════════════════════════════════════════════════════════════════
-- POURQUOI L'ANNÉE SUR 4 CHIFFRES, ET NON 2 COMME PROPOSÉ LE 30/10
-- ═══════════════════════════════════════════════════════════════════════════
-- Mesure du 09/11, répartition des 12 138 dossiers par année d'ouverture :
--   . elles vont de 1990 à 2026 -- 7 dossiers en 1990, 1 en 2002, 4 en 2005.
--     Sur 2 chiffres, 1990 s'écrirait D90 et 2026 D26 : l'ordre se casse
--     (D90 > D26) et la lecture devient ambiguë.
--   . le maximum d'une année est 808 (2021), donc 4 chiffres de rang suffisent
--     largement -- la crainte du 30/10 (« max ~800 par an ») est confirmée,
--     et elle ne déborde pas.
-- -> FORMAT RETENU : D2026-0431 (10 caractères). ⭐ Le format tient dans la
--    SEULE fonction app_dossier_numero_format ci-dessous : si Frédéric préfère
--    malgré tout 2 chiffres, c'est une ligne à changer, et rien d'autre.
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- § 1. LES DEUX COLONNES, VIDES
-- ───────────────────────────────────────────────────────────────────────────
alter table public.app_affaire_ledger
  add column if not exists app_dossier_uuid   uuid,
  add column if not exists app_dossier_numero text;

comment on column public.app_affaire_ledger.app_dossier_uuid is
  'ETIQUETTE DE DOSSIER (longue) -- posee par Supabase seulement, jamais par le '
  'push ni par le clic. Toutes les transactions d''un meme dossier la partagent. '
  'C''est elle qui va dans la colonne affair_uuid du classeur. Elle ne bouge '
  'JAMAIS une fois posee : voir le journal pour les fusions et les scissions.';

comment on column public.app_affaire_ledger.app_dossier_numero is
  'ETIQUETTE DE DOSSIER (courte, D2026-0431) -- pour l''ecran et pour parler. '
  'Son annee est une ETIQUETTE, PAS une donnee : pour 98 dossiers elle vient '
  'du mandat, qui se trompe d''un an environ une fois sur trois (mesure 09/11).';

create index if not exists app_affaire_ledger_dossier_uuid_idx
  on public.app_affaire_ledger (app_dossier_uuid)
  where app_dossier_uuid is not null;


-- ───────────────────────────────────────────────────────────────────────────
-- § 2. LE COMPTEUR DES RANGS -- une ligne par annee
-- ───────────────────────────────────────────────────────────────────────────
-- ⭐ POURQUOI UN COMPTEUR ET PAS UN max() RECALCULE. Un max() sur les numeros
--    deja poses obligerait a relire le format pour en extraire le rang : la
--    logique vivrait alors DANS la chaine de caracteres. Le compteur la garde
--    dehors, et le format reste libre de changer.
create table if not exists public.app_dossier_numero_compteur (
  annee   integer primary key,
  dernier integer not null default 0 check (dernier >= 0)
);

comment on table public.app_dossier_numero_compteur is
  'Le dernier rang distribue pour chaque annee d''ouverture. Il ne RECULE '
  'jamais : un numero rendu reste brule, pour qu''aucune etiquette ne soit '
  'reattribuee a un autre dossier.';


-- ───────────────────────────────────────────────────────────────────────────
-- § 3. LE JOURNAL DES POSES, DES FUSIONS ET DES SCISSIONS   (condition C4)
-- ───────────────────────────────────────────────────────────────────────────
-- ⛔ C4 de l'audit du 29/10 : « un JOURNAL des fusions et des scissions, lu
--    par le moniteur -- sinon on aura ajoute un numero sans rien resoudre. »
--    Sans ce journal, le worker de la phase B se retrouverait devant un
--    dossier lie a deux lignes du classeur sans savoir laquelle mettre a jour.
create table if not exists public.app_dossier_etiquette_journal (
  id             bigserial primary key,
  quand          timestamptz not null default now(),
  evenement      text    not null
                 check (evenement in ('pose','propagation','fusion','scission')),
  dossier_uuid   uuid    not null,
  dossier_numero text,
  autre_uuid     uuid,
  app_chaine_id  bigint,
  transactions   bigint[] not null default '{}',
  combien        integer  not null default 0,
  pourquoi       text
);

create index if not exists app_dossier_etiquette_journal_quand_idx
  on public.app_dossier_etiquette_journal (quand desc);
create index if not exists app_dossier_etiquette_journal_uuid_idx
  on public.app_dossier_etiquette_journal (dossier_uuid);

comment on table public.app_dossier_etiquette_journal is
  'Tout ce qui arrive aux etiquettes. Le moniteur lit fusion et scission : ce '
  'sont les deux seuls cas ou une ligne du classeur peut se retrouver devant '
  'deux dossiers, ou l''inverse. autre_uuid = l''etiquette absorbee (fusion) '
  'ou l''etiquette nee (scission).';


-- ───────────────────────────────────────────────────────────────────────────
-- § 4. LE FORMAT -- ⭐ LA SEULE FONCTION A TOUCHER SI LE FORMAT CHANGE
-- ───────────────────────────────────────────────────────────────────────────
create or replace function public.app_dossier_numero_format(
  p_annee integer, p_rang integer
) returns text
language sql immutable
as $fmt$
  -- D2026-0431. Annee sur 4 chiffres : les dossiers vont de 1990 a 2026, et
  -- sur 2 chiffres D90 se classerait apres D26 (mesure du 09/11).
  -- ⭐ POUR PASSER A 2 CHIFFRES : to_char(p_annee % 100, 'FM00') ici, et rien
  --    d'autre dans tout le projet.
  select 'D' || to_char(p_annee, 'FM0000') || '-' || to_char(p_rang, 'FM0000');
$fmt$;


-- ───────────────────────────────────────────────────────────────────────────
-- § 5. L'ANNEE D'OUVERTURE D'UN DOSSIER -- la cascade de l'en-tete
-- ───────────────────────────────────────────────────────────────────────────
-- Pour le DIAGNOSTIC, une chaine a la fois. La pose, elle, calcule les annees
-- par ensembles (§ 6) : une fonction qui lit des tables, appelee par ligne
-- depuis un WHERE, est rejouee pour chaque ligne -- l'essai du 02/11 est parti
-- en boucle sur cette faute exacte.
create or replace function public.app_dossier_annee_ouverture(p_chaine bigint)
returns integer
language sql stable
as $an$
  with t as (
    select min(case when l.date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                     and l.date not like '0000%'
                    then left(l.date, 4) end)  as an_transaction,
           min(l.hektor_annonce_id)            as annonce
    from public.app_affaire_ledger l
    where l.app_chaine_id = p_chaine
  ),
  m as (
    select min(case when a.date_debut ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                     and a.date_debut not like '0000%'
                    then left(a.date_debut, 4) end) as an_mandat
    from public.app_mandat a
    join t on a.hektor_annonce_id = t.annonce::text
  )
  select coalesce((select an_transaction from t),
                  (select an_mandat from m),
                  '0000')::integer;
$an$;


-- ───────────────────────────────────────────────────────────────────────────
-- § 6. LA POSE -- ⛔ DORMANTE : RIEN NE L'APPELLE
-- ───────────────────────────────────────────────────────────────────────────
-- C2 : elle se lance APRES le calcul des groupes, jamais pendant. La lecon du
--      05/09 (9 000 dossiers coupes en deux) vient de l'inverse.
-- C3 : un SEUL emetteur, et c'est Supabase. Ni le clic ni le push ne posent
--      d'etiquette. ⚠ D8 : la regle de chaine existe en DEUX copies, SQL au
--      clic (app_chaine_pour, qui n'a PAS la v2) et Python la nuit
--      (recalculer_les_chaines, qui l'a -- APP_CHAINAGE_V2=1 verifie dans .env
--      le 09/11). Si le clic posait l'etiquette, il la poserait sur des
--      groupes que la nuit refait autrement.
create or replace function public.app_poser_etiquettes_dossier(
  p_limite  integer default null,     -- null = tous ; sinon n groupes, pour un essai
  p_a_blanc boolean default false     -- true = COMPTE et n'ecrit rien
) returns table (
  geste    text,
  dossiers integer,
  lignes   integer
)
language plpgsql
security definer
set search_path = public
as $pose$
declare
  v_pose        integer := 0;  v_pose_l        integer := 0;
  v_propagation integer := 0;  v_propagation_l integer := 0;
  v_fusion      integer := 0;  v_fusion_l      integer := 0;
  v_scission    integer := 0;  v_scission_l    integer := 0;
begin
  -- ─────────────────────────────────────────────────────────────────────
  -- ① LES GROUPES SANS AUCUNE ETIQUETTE  ->  une etiquette neuve
  -- ─────────────────────────────────────────────────────────────────────
  create temporary table _nus on commit drop as
  with groupes as (
    select l.app_chaine_id,
           min(case when l.date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                     and l.date not like '0000%'
                    then left(l.date, 4) end)  as an_transaction,
           min(l.hektor_annonce_id)            as annonce,
           min(case when l.date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                     and l.date not like '0000%'
                    then left(l.date, 10) end) as plus_ancienne
    from public.app_affaire_ledger l
    where l.app_chaine_id is not null
    group by l.app_chaine_id
    having count(l.app_dossier_uuid) = 0
  ),
  mandats as (
    select a.hektor_annonce_id,
           min(case when a.date_debut ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                     and a.date_debut not like '0000%'
                    then left(a.date_debut, 4) end) as an_mandat
    from public.app_mandat a
    group by a.hektor_annonce_id
  )
  select g.app_chaine_id,
         coalesce(g.an_transaction, m.an_mandat, '0000')::integer as annee,
         g.plus_ancienne
  from groupes g
  left join mandats m on m.hektor_annonce_id = g.annonce::text
  order by coalesce(g.an_transaction, m.an_mandat, '0000'),
           g.plus_ancienne nulls last,
           g.app_chaine_id        -- ⭐ departage : l'ordre est REFAISABLE
  limit coalesce(p_limite, 2147483647);

  insert into public.app_dossier_numero_compteur (annee, dernier)
  select distinct annee, 0 from _nus
  on conflict (annee) do nothing;

  create temporary table _neufs on commit drop as
  select n.app_chaine_id,
         n.annee,
         gen_random_uuid() as dossier_uuid,
         (c.dernier + row_number() over (partition by n.annee
                                         order by n.plus_ancienne nulls last,
                                                  n.app_chaine_id))::integer as rang
  from _nus n
  join public.app_dossier_numero_compteur c on c.annee = n.annee;

  select count(*) into v_pose from _neufs;

  if not p_a_blanc and v_pose > 0 then
    update public.app_affaire_ledger l
       set app_dossier_uuid   = f.dossier_uuid,
           app_dossier_numero = public.app_dossier_numero_format(f.annee, f.rang)
      from _neufs f
     where l.app_chaine_id = f.app_chaine_id
       and l.app_dossier_uuid is null;
    get diagnostics v_pose_l = row_count;

    update public.app_dossier_numero_compteur c
       set dernier = s.dernier
      from (select annee, max(rang) as dernier from _neufs group by annee) s
     where c.annee = s.annee;

    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, app_chaine_id,
       transactions, combien, pourquoi)
    select 'pose', f.dossier_uuid,
           public.app_dossier_numero_format(f.annee, f.rang),
           f.app_chaine_id,
           array_agg(l.app_affaire_id order by l.app_affaire_id),
           count(*),
           'premiere pose, annee ' || f.annee
    from _neufs f
    join public.app_affaire_ledger l on l.app_chaine_id = f.app_chaine_id
    group by f.dossier_uuid, f.annee, f.rang, f.app_chaine_id;
  end if;

  -- ─────────────────────────────────────────────────────────────────────
  -- ② UNE TRANSACTION NUE DANS UN GROUPE DEJA ETIQUETE  ->  on propage
  --    C'EST LE CAS NORMAL, et c'est lui qui rend l'etiquette stable :
  --    app_chaine_id peut bouger, l'etiquette du groupe ne bouge pas.
  -- ─────────────────────────────────────────────────────────────────────
  create temporary table _a_propager on commit drop as
  select l.app_affaire_id, l.app_chaine_id, d.dossier_uuid, d.dossier_numero
  from public.app_affaire_ledger l
  join (
    -- l'etiquette du groupe = celle de sa transaction la plus ancienne
    select distinct on (app_chaine_id)
           app_chaine_id,
           app_dossier_uuid   as dossier_uuid,
           app_dossier_numero as dossier_numero
    from public.app_affaire_ledger
    where app_chaine_id is not null and app_dossier_uuid is not null
    order by app_chaine_id, app_affaire_id
  ) d on d.app_chaine_id = l.app_chaine_id
  where l.app_dossier_uuid is null;

  select count(distinct app_chaine_id), count(*)
    into v_propagation, v_propagation_l
  from _a_propager;

  if not p_a_blanc and v_propagation_l > 0 then
    update public.app_affaire_ledger l
       set app_dossier_uuid   = p.dossier_uuid,
           app_dossier_numero = p.dossier_numero
      from _a_propager p
     where l.app_affaire_id = p.app_affaire_id;

    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, app_chaine_id,
       transactions, combien, pourquoi)
    select 'propagation', p.dossier_uuid, p.dossier_numero, p.app_chaine_id,
           array_agg(p.app_affaire_id order by p.app_affaire_id), count(*),
           'transaction(s) arrivee(s) dans un dossier deja etiquete'
    from _a_propager p
    group by p.dossier_uuid, p.dossier_numero, p.app_chaine_id;
  end if;

  -- ─────────────────────────────────────────────────────────────────────
  -- ③ FUSION -- un groupe porte PLUSIEURS etiquettes
  --    Deux dossiers etiquetes se sont retrouves reunis. On garde la plus
  --    ANCIENNE (celle de la plus petite transaction) et on journalise les
  --    autres : c'est la ligne que le worker de la phase B devra lire pour
  --    savoir que deux lignes du classeur ne designent plus qu'un dossier.
  -- ─────────────────────────────────────────────────────────────────────
  create temporary table _fusions on commit drop as
  with multi as (
    select app_chaine_id
    from public.app_affaire_ledger
    where app_chaine_id is not null and app_dossier_uuid is not null
    group by app_chaine_id
    having count(distinct app_dossier_uuid) > 1
  ),
  gagnante as (
    select distinct on (l.app_chaine_id)
           l.app_chaine_id,
           l.app_dossier_uuid   as garde,
           l.app_dossier_numero as garde_num
    from public.app_affaire_ledger l
    join multi using (app_chaine_id)
    where l.app_dossier_uuid is not null
    order by l.app_chaine_id, l.app_affaire_id
  )
  select l.app_affaire_id, l.app_chaine_id,
         g.garde, g.garde_num,
         l.app_dossier_uuid as absorbee
  from public.app_affaire_ledger l
  join gagnante g using (app_chaine_id)
  where l.app_dossier_uuid is not null
    and l.app_dossier_uuid is distinct from g.garde;

  select count(distinct app_chaine_id), count(*)
    into v_fusion, v_fusion_l
  from _fusions;

  if not p_a_blanc and v_fusion_l > 0 then
    -- ⭐ LE JOURNAL D'ABORD : apres l'UPDATE, l'etiquette absorbee a disparu
    --    des lignes, et plus rien ne dirait laquelle elle etait.
    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id,
       transactions, combien, pourquoi)
    select 'fusion', f.garde, f.garde_num, f.absorbee, f.app_chaine_id,
           array_agg(f.app_affaire_id order by f.app_affaire_id), count(*),
           'deux dossiers etiquetes reunis dans un seul groupe'
    from _fusions f
    group by f.garde, f.garde_num, f.absorbee, f.app_chaine_id;

    update public.app_affaire_ledger l
       set app_dossier_uuid   = f.garde,
           app_dossier_numero = f.garde_num
      from _fusions f
     where l.app_affaire_id = f.app_affaire_id;
  end if;

  -- ─────────────────────────────────────────────────────────────────────
  -- ④ SCISSION -- une etiquette etalee sur PLUSIEURS groupes
  --    Un dossier etiquete s'est coupe. Le groupe qui garde la transaction
  --    la plus ancienne garde l'etiquette ; les autres en recoivent une
  --    neuve, journalisee -- sinon une ligne du classeur se retrouverait
  --    devant deux dossiers.
  -- ─────────────────────────────────────────────────────────────────────
  create temporary table _scissions on commit drop as
  with etalees as (
    select app_dossier_uuid
    from public.app_affaire_ledger
    where app_dossier_uuid is not null and app_chaine_id is not null
    group by app_dossier_uuid
    having count(distinct app_chaine_id) > 1
  ),
  tete as (   -- le groupe qui GARDE : celui de la plus petite transaction
    select distinct on (l.app_dossier_uuid)
           l.app_dossier_uuid, l.app_chaine_id as garde_chaine
    from public.app_affaire_ledger l
    join etalees using (app_dossier_uuid)
    order by l.app_dossier_uuid, l.app_affaire_id
  ),
  partants as (
    select distinct
           l.app_dossier_uuid as ancienne,
           l.app_chaine_id,
           public.app_dossier_annee_ouverture(l.app_chaine_id) as annee
    from public.app_affaire_ledger l
    join tete t on t.app_dossier_uuid = l.app_dossier_uuid
    where l.app_chaine_id is distinct from t.garde_chaine
  )
  select p.ancienne, p.app_chaine_id, p.annee, gen_random_uuid() as neuve
  from partants p;

  select count(*) into v_scission from _scissions;

  if not p_a_blanc and v_scission > 0 then
    insert into public.app_dossier_numero_compteur (annee, dernier)
    select distinct annee, 0 from _scissions
    on conflict (annee) do nothing;

    create temporary table _scissions_num on commit drop as
    select s.ancienne, s.app_chaine_id, s.annee, s.neuve,
           (c.dernier + row_number() over (partition by s.annee
                                           order by s.app_chaine_id))::integer as rang
    from _scissions s
    join public.app_dossier_numero_compteur c on c.annee = s.annee;

    -- ⭐ LE JOURNAL D'ABORD, pour la meme raison qu'en ③ : apres l'UPDATE, on
    --    ne saurait plus quelles transactions ont quitte l'ancienne etiquette.
    insert into public.app_dossier_etiquette_journal
      (evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id,
       transactions, combien, pourquoi)
    select 'scission', s.ancienne,
           public.app_dossier_numero_format(s.annee, s.rang),
           s.neuve, s.app_chaine_id,
           array_agg(l.app_affaire_id order by l.app_affaire_id), count(*),
           'le dossier s''est coupe : cette part recoit une etiquette neuve'
    from _scissions_num s
    join public.app_affaire_ledger l on l.app_chaine_id   = s.app_chaine_id
                                    and l.app_dossier_uuid = s.ancienne
    group by s.ancienne, s.neuve, s.annee, s.rang, s.app_chaine_id;

    update public.app_affaire_ledger l
       set app_dossier_uuid   = s.neuve,
           app_dossier_numero = public.app_dossier_numero_format(s.annee, s.rang)
      from _scissions_num s
     where l.app_chaine_id    = s.app_chaine_id
       and l.app_dossier_uuid = s.ancienne;
    get diagnostics v_scission_l = row_count;

    update public.app_dossier_numero_compteur c
       set dernier = x.dernier
      from (select annee, max(rang) as dernier from _scissions_num group by annee) x
     where c.annee = x.annee;
  end if;

  return query
    select 'pose'::text,          v_pose,        v_pose_l
    union all
    select 'propagation'::text,   v_propagation, v_propagation_l
    union all
    select 'fusion'::text,        v_fusion,      v_fusion_l
    union all
    select 'scission'::text,      v_scission,    v_scission_l;
end;
$pose$;


-- ───────────────────────────────────────────────────────────────────────────
-- § 7. LES DROITS
-- ───────────────────────────────────────────────────────────────────────────
-- ⛔ « revoke all from public » NE FERME PAS authenticated : chaque fonction
--    nait avec le droit d'execute pour lui. Les trois lignes sont necessaires.
--    Seul le run (service_role) pose les etiquettes.
revoke all on function public.app_poser_etiquettes_dossier(integer, boolean) from public;
revoke all on function public.app_poser_etiquettes_dossier(integer, boolean) from authenticated;
revoke all on function public.app_poser_etiquettes_dossier(integer, boolean) from anon;

-- Les lectures, elles, restent ouvertes aux comptes connectes.
revoke all on function public.app_dossier_annee_ouverture(bigint) from public;
revoke all on function public.app_dossier_annee_ouverture(bigint) from anon;
grant execute on function public.app_dossier_annee_ouverture(bigint) to authenticated;

revoke all on function public.app_dossier_numero_format(integer, integer) from public;
revoke all on function public.app_dossier_numero_format(integer, integer) from anon;
grant execute on function public.app_dossier_numero_format(integer, integer) to authenticated;

alter table public.app_dossier_etiquette_journal enable row level security;
alter table public.app_dossier_numero_compteur   enable row level security;

-- Le journal : lisible par les admins. Le moniteur le lit en service_role,
-- qui passe outre RLS -- cette regle est pour l'ecran, pas pour lui.
drop policy if exists app_dossier_etiquette_journal_lecture
  on public.app_dossier_etiquette_journal;
create policy app_dossier_etiquette_journal_lecture
  on public.app_dossier_etiquette_journal for select
  to authenticated using (public.is_app_global_reader());


-- ═══════════════════════════════════════════════════════════════════════════
-- § 8. LES CONTROLES -- ILS N'ECRIVENT RIEN. A lire apres le collage.
-- ═══════════════════════════════════════════════════════════════════════════

-- ① LE PATCH EST BIEN DORMANT : aucune etiquette posee.
--    ⛔ Un zero ne se croit pas sans temoin positif -> la colonne EXISTE et le
--    registre a bien ses lignes.
select '① dormant' as controle,
       count(app_dossier_uuid) as etiquettes_posees_attendu_0,
       count(*)                as lignes_du_registre_temoin_positif
from public.app_affaire_ledger;

-- ② LE FORMAT rend bien ce qu'on attend, aux trois bouts de la cascade.
select '② format' as controle,
       public.app_dossier_numero_format(2026, 431) as attendu_D2026_0431,
       public.app_dossier_numero_format(1990, 7)   as attendu_D1990_0007,
       public.app_dossier_numero_format(0, 11)     as attendu_D0000_0011;

-- ③ L'ANNEE D'OUVERTURE, avec son TEMOIN INVERSE : le dossier muet doit
--    rendre 0 et le dossier date NON -- sinon la fonction rend 0 pour tout
--    le monde et le controle ④ ne le verrait pas.
select '③ annee' as controle,
       public.app_dossier_annee_ouverture(
         (select min(app_chaine_id) from public.app_affaire_ledger
           where date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' and date not like '0000%'
             and app_chaine_id is not null)) as date_attendu_non_nul,
       public.app_dossier_annee_ouverture(28724) as muet_attendu_0;

-- ④ LA CASCADE EN ENTIER : les trois marches doivent retrouver
--    12 029 / 98 / 11 sur 12 138 dossiers (mesure du 09/11).
with g as (
  select l.app_chaine_id,
         min(case when l.date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                   and l.date not like '0000%'
                  then left(l.date, 4) end) as an_t,
         min(l.hektor_annonce_id)           as annonce
  from public.app_affaire_ledger l
  where l.app_chaine_id is not null
  group by l.app_chaine_id
),
m as (
  select a.hektor_annonce_id,
         min(case when a.date_debut ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                   and a.date_debut not like '0000%'
                  then left(a.date_debut, 4) end) as an_m
  from public.app_mandat a
  group by a.hektor_annonce_id
)
select '④ cascade' as controle,
       count(*)                                                      as dossiers_attendu_12138,
       count(*) filter (where g.an_t is not null)                     as par_transaction_attendu_12029,
       count(*) filter (where g.an_t is null and m.an_m is not null)   as par_mandat_attendu_98,
       count(*) filter (where g.an_t is null and m.an_m is null)       as muets_attendu_11
from g left join m on m.hektor_annonce_id = g.annonce::text;

-- ⑤ LA POSE A BLANC : ce que B3 ferait, sans rien ecrire. « pose » doit
--    annoncer 12 138 dossiers ; les trois autres gestes, 0.
select '⑤ a blanc' as controle, *
from public.app_poser_etiquettes_dossier(p_a_blanc => true);

-- ⑥ L'INVARIANT, a relire APRES chaque pose : un groupe = UNE etiquette,
--    une etiquette = UN groupe. Les deux doivent rendre 0, et le journal
--    doit porter une ligne pour chaque exception reparee.
select '⑥ invariant' as controle,
       (select count(*) from (
          select app_chaine_id from public.app_affaire_ledger
          where app_chaine_id is not null and app_dossier_uuid is not null
          group by app_chaine_id having count(distinct app_dossier_uuid) > 1) z)
         as groupes_a_plusieurs_etiquettes_attendu_0,
       (select count(*) from (
          select app_dossier_uuid from public.app_affaire_ledger
          where app_dossier_uuid is not null and app_chaine_id is not null
          group by app_dossier_uuid having count(distinct app_chaine_id) > 1) z)
         as etiquettes_sur_plusieurs_groupes_attendu_0;

-- ⑦ C1, LA CONDITION QUI PROTEGE TOUT. Ce controle ne se lit pas en SQL :
--    il se lit dans phase2/sync/affaire_ledger.py, l. ~2300.
--      grep -n "app_dossier_uuid" phase2/sync/affaire_ledger.py
--    Les DEUX colonnes doivent figurer dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS
--    AVANT le premier remplissage (B3). Sinon, lecon du 07/09 : un « --push »
--    pousse le miroir local, qui ne les connait pas, et les efface.
