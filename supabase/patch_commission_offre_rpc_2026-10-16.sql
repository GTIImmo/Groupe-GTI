-- ═══════════════════════════════════════════════════════════════════════════════
-- LOT 1b — LA RPC QUI ECRIT LA COMMISSION ET SA CHARGE            16/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase, APRES le 1a.
-- Aucun redemarrage, aucun deploiement. Idempotent (CREATE OR REPLACE).
--
-- ─── CE QU'ELLE FAIT, EN UNE PHRASE ───────────────────────────────────────────
-- Elle pose les trois valeurs du 1a sur UNE SEULE LIGNE du registre : celle de
-- l'etape qu'on vient de traiter. Elle ne touche JAMAIS une autre ligne.
--
-- ⭐ C'EST CA QUI REPOND A LA DEMANDE DE FREDERIC (16/10) : « il ne faut pas que
--   les colonnes ajoutees dans l'offre bougent si on bouge le compromis ». Ce
--   n'est pas une regle a ecrire ni un garde-fou a afficher : c'est IMPOSSIBLE
--   PAR CONSTRUCTION, parce que le UPDATE porte un WHERE sur une seule affaire.
--   L'offre et le compromis sont deux LIGNES differentes du registre (mesure du
--   16/10 : 9 826 chaines a plusieurs etapes, une ligne par etape).
--
-- ─── ET LA REPRISE D'UNE ETAPE A L'AUTRE ──────────────────────────────────────
-- Decision de Frederic, 16/10 : « il faut que la donnee soit recuperee, et s'il
-- ne change rien cela la valide ». La reprise se fait donc DANS L'ECRAN (1c) :
-- la modale prerenseigne le champ depuis l'etape precedente de la chaine, et
-- l'enregistrement ecrit ce qui est affiche -- touche ou non. Cote base, il n'y
-- a donc rien a faire : chaque ligne porte sa valeur, lisible seule, et aucune
-- lecture n'a besoin de remonter la chaine.
--
-- ─── POURQUOI UNE RPC A PART, ET PAS `app_edit_affaire_optimistic` ────────────
-- Celle-la existe et corrige deja une transaction chez nous. Je ne la reutilise
-- PAS, et voici les trois raisons, verifiees dans son code le 16/10 :
--   ① SA SEMANTIQUE NE CONVIENT PAS. Chez elle, « vider un champ = RENDRE LA
--      MAIN A HEKTOR » : elle retire la ligne du carnet et le prochain
--      rafraichissement remet la valeur de Hektor. Pour nos trois champs, Hektor
--      n'a RIEN a rendre -- il ne les connait pas. Vider doit vouloir dire
--      « vide », pas « que Hektor decide ».
--   ② ELLE ECRIT DANS LE CARNET `app_affaire_champ_app`, qui compare `valeur_app`
--      a `valeur_miroir` pour verifier que Hektor a garde ce qu'on lui a envoye.
--      Nos valeurs ne partent jamais chez lui : leur `valeur_miroir` serait vide
--      a vie, et le carnet ne dirait rien.
--   ③ SES CHAMPS SONT UNE LISTE BLANCHE liee au mecanisme du contrat (le run de
--      nuit repose le carnet sur le ledger). Nos colonnes n'en ont pas besoin :
--      elles sont de CLASSE A -- le push ne les envoie pas, donc rien ne les
--      ecrase, et le run les redescend. Eprouve le 16/10.
--
-- ─── LE DROIT, ET UNE INCOHERENCE SIGNALEE SANS Y TOUCHER ─────────────────────
-- On exige `is_app_manager_or_admin()`, c'est-a-dire EXACTEMENT qui peut ouvrir
-- la modale de statut aujourd'hui (App.tsx, openStatusChangeModal : `if
-- (!isManagerOrAdmin) return`), plus le controle d'acces au dossier.
-- ⚠ SIGNALE, PAS CORRIGE : `app_edit_affaire_optimistic` exige encore
--   `is_app_admin()` alors que la modale s'ouvre aux managers depuis. Un manager
--   peut donc ouvrir et se faire refuser sa correction. Ce n'est pas le
--   perimetre de ce lot -- c'est une decision a prendre, pas un defaut a
--   corriger au passage.
--
-- ─── ⚠⚠ CE QUI PART CHEZ HEKTOR, ET CE QUI N'Y PART PAS -- CORRIGE LE 16/10 ───
-- Frederic m'a arrete : « UNIQUEMENT LES REPARTITIONS ne sont pas envoyees a
-- Hektor ». J'avais ecrit l'inverse. La mesure lui donne raison, et elle dit
-- PRECISEMENT ou :
--
--     etape       lignes   honoraires chez Hektor
--     offre       11 187           0 %     <- il ne garde RIEN a l'offre
--     compromis   10 628          99 %     <- il les garde
--     vente        9 259         100 %     <- il les garde
--
-- D'OU LE PARTAGE DU TRAVAIL, QUI N'EST PAS CELUI QUE J'AVAIS ECRIT :
--   · A L'OFFRE : Hektor n'a aucune destination. Les honoraires VENDEUR et
--     ACQUEREUR vont donc dans NOS colonnes, par cette RPC. C'est le trou que
--     le lot 1 vient combler (0 sur 11 187, et 22 sur 22 dans le classeur).
--   · AU COMPROMIS ET A LA VENTE : les honoraires partent chez Hektor par le
--     CHEMIN QUI EXISTE DEJA (`sellerFees` / `buyerFees` dans la charge du
--     geste), et il les rend a 99-100 %. Cette RPC n'a pas a les dupliquer.
--   · LA CHARGE DE LA COMMISSION, elle, reste a nous PARTOUT : Hektor n'a pas
--     cette notion. Mesure du 14/10 : sur 25 lignes ou le classeur dit
--     « Acquereur », 13 sont rangees cote vendeur chez lui.
--
-- ⭐ ET LA CONSEQUENCE POUR LE 1c, qui est la demande exacte de Frederic :
--   « si l'admin ne change pas les champs preremplis par l'offre d'achat dans la
--    modale, cela vaut pour saisi et est sauvegarde dans le compromis qui reste
--    modifiable ET A HEKTOR ».
--   Donc au compromis, un champ PREREMPLI ET NON TOUCHE doit quand meme partir
--   dans la charge du geste.
--   ⭐ ET LA SOLUTION EST DE FREDERIC, PAS DE MOI (16/10). J'avais propose
--     d'elargir la condition de `sellerFees` de « touche » a « non vide » --
--     c'est-a-dire de MODIFIER le code qui decide ce qui part chez Hektor.
--     Il a demande : « pourquoi ne pas saisir auto ». C'est mieux, et mesure :
--     le drapeau `statusChangeHonorairesEntreeTouche` a CINQ points d'usage et
--     UN SEUL LECTEUR -- la charge du geste (App.tsx:17064). Rien d'autre n'en
--     depend. Le LEVER au prerenseignement dit donc exactement « cela vaut pour
--     saisi », et LE GESTE N'EST PAS TOUCHE D'UNE LIGNE.
--   LA REGLE : on prerenseigne SEULEMENT si on a une valeur. Sans valeur, pas de
--     drapeau, donc rien n'est envoye -- on ne peut pas envoyer du vide qui
--     effacerait Hektor. Et le prerenseignement ne s'applique que si le champ est
--     encore vide ET le drapeau encore baisse : il ne peut pas ecraser une saisie.
--   ⚠ SIGNALE SANS LE CHANGER : si l'admin VIDE un champ prerenseigne, le drapeau
--     reste leve et du vide partirait. Ce cas existe DEJA aujourd'hui (taper puis
--     effacer fait la meme chose) : le corriger serait changer un comportement en
--     place, hors perimetre de ce lot.
--
-- ─── CE QUE CETTE RPC NE FAIT PAS ─────────────────────────────────────────────
-- ⛔ ELLE, elle n'envoie rien a Hektor : elle ecrit trois colonnes, un point.
-- ⛔ ELLE N'EST PAS DANS LA CHARGE DU GESTE. Le front l'appelle APRES, en appel
--    separe : si elle echoue, le changement de statut reste acquis. Meme patron
--    que la cloture de mandat et la repartition.
-- ⛔ ELLE NE TOUCHE AUCUNE AUTRE COLONNE que les trois du 1a.
--
-- ─── RETOUR ARRIERE ────────────────────────────────────────────────────────────
--   DROP FUNCTION IF EXISTS public.app_affaire_commission_ecrire(bigint, jsonb);
--   Les valeurs deja posees restent : elles sont dans les colonnes, pas ici.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU D'ENTREE
-- ---------------------------------------------------------------------
do $garde$
declare n integer;
begin
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaire_ledger'
     and column_name in ('honoraires_entree_app', 'honoraires_sortie_app',
                         'charge_commission_app');
  if n <> 3 then
    raise exception 'ARRET : les 3 colonnes du lot 1a manquent (vu %) -- '
                    'coller patch_commission_offre_classe_a_2026-10-16.sql d''abord', n;
  end if;

  select count(*) into n from pg_proc p join pg_namespace s on s.oid = p.pronamespace
   where s.nspname = 'public'
     and p.proname in ('is_app_manager_or_admin', 'app_console_can_access_dossier');
  if n < 2 then
    raise exception 'ARRET : is_app_manager_or_admin() et/ou '
                    'app_console_can_access_dossier() sont introuvables (vu %)', n;
  end if;
end $garde$;

-- ---------------------------------------------------------------------
-- LA FONCTION
-- ---------------------------------------------------------------------
create or replace function public.app_affaire_commission_ecrire(
    target_affaire_id bigint,
    edit_fields       jsonb
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  a           app_affaire_ledger%rowtype;
  -- ⚠ LISTE BLANCHE. Un nom inconnu est IGNORE en silence plutot que refuse :
  --   un champ qu'on ajoutera demain ne doit pas casser l'ecran d'aujourd'hui.
  --   (Meme choix que app_edit_affaire_optimistic, et pour la meme raison.)
  champs_ok   text[] := array['honoraires_entree_app', 'honoraires_sortie_app',
                              'charge_commission_app'];
  k           text;
  v           text;
  retenus     int := 0;
  ignores     int := 0;
  touchees    int := 0;
begin
  select * into a from app_affaire_ledger where app_affaire_id = target_affaire_id;
  if not found then
    raise exception 'affaire_not_found' using errcode = '22023';
  end if;

  -- Le droit : exactement qui peut ouvrir la modale de statut.
  if not public.is_app_manager_or_admin() then
    raise exception 'not_allowed' using errcode = '42501';
  end if;

  if not public.app_console_can_access_dossier(a.app_dossier_id,
                                               a.hektor_annonce_id::text) then
    raise exception 'dossier_not_allowed' using errcode = '42501';
  end if;

  for k in select jsonb_object_keys(edit_fields) loop
    if not (k = any (champs_ok)) then
      ignores := ignores + 1;
      continue;
    end if;

    -- Une clef PRESENTE et vide veut dire « vide », pas « que Hektor decide » :
    -- Hektor ne connait pas ces champs. Une clef ABSENTE, elle, ne touche a rien.
    v := nullif(btrim(coalesce(edit_fields ->> k, '')), '');

    if k = 'charge_commission_app' and v is not null then
      -- On NORMALISE ici plutot que de refuser : l'ecran peut envoyer
      -- « Vendeur », « VENDEUR » ou « vendeur ». La contrainte du 1a, elle,
      -- n'accepte que les minuscules -- sans cette etape elle rejetterait une
      -- saisie parfaitement legitime.
      v := lower(btrim(v));
      v := translate(v, 'éèêëàâäïîôöùûü', 'eeeeaaaiioouuu');
      if v not in ('vendeur', 'acquereur') then
        raise exception 'charge_invalide: %', v using errcode = '22023';
      end if;
    end if;

    -- ⭐⭐ LE WHERE PORTE SUR UNE SEULE AFFAIRE, ET C'EST TOUT LE SUJET.
    --   L'offre, le compromis et la vente sont trois LIGNES. Ecrire ici ne peut
    --   pas bouger les autres etapes de la chaine -- la demande de Frederic du
    --   16/10 est tenue par la forme de la requete, pas par une regle.
    if k = 'honoraires_entree_app' then
      update app_affaire_ledger set honoraires_entree_app = v
       where app_affaire_id = target_affaire_id;
    elsif k = 'honoraires_sortie_app' then
      update app_affaire_ledger set honoraires_sortie_app = v
       where app_affaire_id = target_affaire_id;
    else
      update app_affaire_ledger set charge_commission_app = v
       where app_affaire_id = target_affaire_id;
    end if;
    get diagnostics touchees = row_count;
    if touchees <> 1 then
      -- Ne peut pas arriver (la ligne a ete lue juste avant), et si ca arrivait
      -- on prefere crier que poser la valeur ailleurs.
      raise exception 'ecriture_inattendue: % ligne(s) touchee(s) pour %',
            touchees, target_affaire_id using errcode = '22023';
    end if;

    retenus := retenus + 1;
  end loop;

  return jsonb_build_object(
    'ok', true,
    'app_affaire_id', target_affaire_id,
    'kind', a.kind,
    'app_chaine_id', a.app_chaine_id,
    'champs_retenus', retenus,
    'champs_ignores', ignores,
    -- Dit explicitement ce que personne ne doit supposer.
    'hektor_informe', false,
    'autres_etapes_touchees', 0
  );
end
$function$;

revoke all on function public.app_affaire_commission_ecrire(bigint, jsonb) from public;
revoke all on function public.app_affaire_commission_ecrire(bigint, jsonb) from anon;
grant execute on function public.app_affaire_commission_ecrire(bigint, jsonb)
      to authenticated;

comment on function public.app_affaire_commission_ecrire(bigint, jsonb) is
    'Lot 1b (16/10/2026) : pose honoraires_entree_app / honoraires_sortie_app / '
    'charge_commission_app sur UNE SEULE ligne du registre. Ne touche jamais une '
    'autre etape de la chaine -- demande de Frederic du 16/10. Rien ne part chez '
    'Hektor par CETTE voie -- au compromis et a la vente, les honoraires y vont '
    'par le chemin du geste, qui existe deja. Appelee APRES le geste, en appel '
    'separe : un echec ici ne doit pas '
    'annuler un changement de statut reussi.';

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU DE SORTIE
-- ---------------------------------------------------------------------
do $garde$
declare n integer;
begin
  select count(*) into n from pg_proc p join pg_namespace s on s.oid = p.pronamespace
   where s.nspname = 'public' and p.proname = 'app_affaire_commission_ecrire';
  if n <> 1 then
    raise exception 'La fonction n''a pas ete creee (vu %)', n;
  end if;

  if not exists (
    select 1 from information_schema.role_routine_grants
     where routine_schema = 'public'
       and routine_name = 'app_affaire_commission_ecrire'
       and grantee = 'authenticated' and privilege_type = 'EXECUTE'
  ) then
    raise exception 'authenticated ne peut pas l''executer : l''ecran ne pourrait rien ecrire';
  end if;

  raise notice 'OK : app_affaire_commission_ecrire creee, executable par '
               'authenticated, et refusee a anon. ATTENDU ENSUITE : 0 valeur en '
               'base -- rien ne l''appelle avant le 1c (l''ecran).';
end $garde$;

-- ─── CONTROLE APRES APPLICATION ────────────────────────────────────────────────
-- ⚠ NE PAS L'ESSAYER SUR UNE VRAIE AFFAIRE : elle ECRIT. L'essai se fera au 1c,
--   sur une offre d'essai, et la seule preuve qui compte est le LENDEMAIN --
--   la valeur a-t-elle survecu au run de nuit ?
--   Pour verifier seulement qu'elle existe et qu'elle refuse l'inconnu :
--     select public.app_affaire_commission_ecrire(-1, '{}'::jsonb);
--     ATTENDU : erreur « affaire_not_found ». Aucune ligne ne porte l'id -1.
