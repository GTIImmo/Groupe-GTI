-- ═══════════════════════════════════════════════════════════════════════════════
-- RETIRER UN MANDANT D'UN BIEN -- la porte cote cloud        02/10/2026 · ④a + ④b
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
--
-- ⚠ LES DEUX ETAPES SONT DANS LA MEME TRANSACTION, ET C'EST VOULU : la RPC ne peut
--   pas vivre sans le type de travail, et un type de travail sans RPC ne sert a
--   rien. Les separer laisserait une fenetre ou l'un existe sans l'autre.
--
-- ─── CE QUE CE PATCH OUVRE ──────────────────────────────────────────────────────
-- Le geste « retirer un mandant », demande par Frederic le 02/10. Audit complet :
-- notice/AUDIT_RETIRER_UN_MANDANT_2026-10-02.md
--
-- ⭐ HEKTOR ACCEPTE LE GESTE, et son appel a ete RELEVE A L'ECRAN le 02/10, sur le
--   bien 63112 : le menu a trois points de la ligne du mandant porte « Detacher le
--   contact », qui appelle
--       degroupproprioForAnnonce(id, idann)
--       -> $j.ajax({ url:'xmlrpc.php', data:{ mode:'degroupproprio', id:<contact>,
--                                             idann:<annonce> } })
--   MEMES PARAMETRES que le rattachement que le worker fait deja
--   (mode=selectnouveauproprio_sup&id=&idann=). Rien n'a ete execute chez Hektor.
--
-- ⚠⚠ ET HEKTOR NE DEMANDE AUCUNE CONFIRMATION : `confirm()` est ABSENT de sa
--    fonction. Un clic, le contact est detache. L'avertissement cote app n'est donc
--    pas un confort, il comble un manque reel.
--
-- ─── LA REGLE DE FREDERIC ───────────────────────────────────────────────────────
-- « SI UN NUMERO DE MANDAT A ETE GENERE, IMPOSSIBLE DE RETIRER DES MANDANTS. »
--
-- ⭐ Elle est MEILLEURE que celle que j'avais proposee (« si le mandat est signe ») :
--    · elle est MESURABLE aujourd'hui -- l'etat « signe » n'existe nulle part dans
--      la base (0 colonne sur app_mandat, 0 sur app_console_document ; il vit chez
--      ImmoSign, cote Hektor)
--    · elle se trompe DU BON COTE -- un mandat peut avoir un numero sans etre
--      signe, donc elle bloque PLUS de cas. Une regle de surete refuse par defaut.
--    · elle ne demande AUCUN rapprochement par le nom. app_mandat.mandants_texte est
--      une phrase d'affichage (« Guy BOURGIN gerant SARL RESIDENCE AMPERE16 avenue
--      Jean FAURE » -- nom et numero colles) : s'y fier serait DEVINER.
--
-- CE QU'ELLE LAISSE OUVERT, mesure sur deux sources independantes :
--      biens vivants                         13 462
--      avec un numero -> BLOQUES                715   ( 5,3 %)
--      sans numero -> RETRAIT POSSIBLE       12 747   (94,7 %)
--
-- ⚠ ON INTERROGE LES DEUX SOURCES (le registre app_mandat ET le champ de l'annonce)
--   et on refuse des que l'UNE des deux porte un numero. Elles sont d'accord
--   aujourd'hui (715 = 715) ; le jour ou elles divergeront, c'est la plus prudente
--   qui doit gagner.
--
-- ─── CE QUE LA RPC FAIT, ET DANS QUEL ORDRE ─────────────────────────────────────
--   1. la permission (app_console_can_request_job) -- le garde-fou que le front
--      n'a pas a refaire
--   2. LA REGLE : refus si un numero de mandat existe
--   3. la traduction : le front passe le numero HEKTOR du contact (c'est celui que
--      degroupproprio exige) ; la RPC retrouve NOTRE numero pour viser app_relation
--   4. LE TRAVAIL, pose AVANT tout le reste -- patron du 30/09 : « le travail
--      d'abord, parce que c'est LUI qui porte les garde-fous »
--   5. le retrait optimiste : retire_le / retire_par
--      -> la vue app_contact_relations_current filtre sur `retire_le IS NULL`,
--         donc LA LIGNE DISPARAIT DE L'ECRAN A LA SECONDE
--
-- ⛔ CE QU'ELLE NE FAIT PAS : elle ne touche NI a Hektor, NI a app_mandat, NI au
--    registre des mandats. Elle pose un travail et une trace, rien d'autre.
--
-- ⚠⚠ LE CHEMIN DE RETOUR EST DANS LE WORKER, PAS ICI. Si Hektor refuse, il faut
--    EFFACER retire_le -- sinon le lien resterait cache a tort, pour toujours.
--    C'est la piece la plus delicate du geste, et elle est volontairement cote
--    worker : lui seul sait si Hektor a dit oui.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
--   DROP FUNCTION IF EXISTS public.app_unlink_mandant_optimistic(bigint,text,text,integer);
--   (la contrainte peut rester : un type autorise que personne n'emet ne coute rien)
--
-- ─── EPROUVE AVANT ENVOI, le 02/10 ──────────────────────────────────────────────
--   contrainte, en BEGIN/ROLLBACK sur la base reelle :
--      type neuf accepte .......... oui
--      type invente refuse ........ oui   (la garantie tient toujours)
--      residus apres ROLLBACK ..... 0, 73 160 travaux inchanges
--   73 160 lignes / 50 Mo / 0 travail en cours -> revalidation instantanee.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ╔═══ ④a  LE TYPE DE TRAVAIL ═══════════════════════════════════════════════════╗
-- La contrainte liste 41 types ; `unlink_hektor_mandant` n'y est pas, donc
-- l'insertion du travail echouerait. On la remplace par la MEME liste + un type.
-- ⚠ app_console_can_request_job ne code AUCUN type en dur (verifie) : elle
--   fonctionnera telle quelle, rien a y changer.
ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check;
ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check
  CHECK (job_type = ANY (ARRAY[
    'sync_console_documents','prepare_document_cloud','generate_estimation_pdf',
    'generate_mandat_document','generate_cadastre_document','relance_signature',
    'cancel_signature_procedure','upload_document_to_hektor','delete_document_from_hektor',
    'sync_hektor_photos','upload_hektor_photo','prepare_archived_annonce_detail',
    'prepare_historical_annonce_detail','link_hektor_mandant','create_hektor_contact',
    'update_hektor_contact','add_hektor_contact_search','update_hektor_contact_search',
    'delete_hektor_contact_search','delete_hektor_contact','create_hektor_mandant_contact',
    'update_hektor_mandant_contact','update_hektor_annonce_fields',
    'create_hektor_mandat_auto_number','delete_hektor_annonce','archive_hektor_annonce',
    'restore_hektor_annonce','change_hektor_annonce_status','assign_hektor_annonce_negotiator',
    'create_hektor_draft_annonce','matterport_online','matterport_offline','matterport_archive',
    'matterport_reactivate','refresh_console_data','refresh_console_contact_data',
    'archive_cloud_documents','change_hektor_offre_status','cancel_hektor_compromis',
    'delete_hektor_compromis','delete_hektor_vente',
    -- ④a 02/10/2026 : retirer un mandant d'un bien
    'unlink_hektor_mandant'
  ]::text[]));

-- ╔═══ ④b  LA RPC ═══════════════════════════════════════════════════════════════╗
CREATE OR REPLACE FUNCTION public.app_unlink_mandant_optimistic(
    target_app_dossier_id bigint,
    target_hektor_annonce_id text,
    target_contact_id text,
    job_priority integer DEFAULT 18)
 RETURNS public.app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
declare
  created_job   public.app_console_job;
  clean_id      text;
  clean_ann     text;
  v_notre_id    bigint;
  v_numero      text;
  v_touchees    integer;
begin
  clean_id  := nullif(trim(coalesce(target_contact_id, '')), '');
  clean_ann := nullif(trim(coalesce(target_hektor_annonce_id, '')), '');

  if clean_ann is null then
    raise exception 'missing_hektor_annonce_id' using errcode = '22023';
  end if;
  if clean_id is null or clean_id !~ '^[0-9]+$' then
    raise exception 'invalid_contact_id' using errcode = '22023';
  end if;

  -- ── 1. LA PERMISSION ──
  if not public.app_console_can_request_job('unlink_hektor_mandant',
                                            target_app_dossier_id, clean_ann) then
    raise exception 'forbidden_unlink_mandant' using errcode = '42501';
  end if;

  -- ── 2. LA REGLE DE FREDERIC ──
  --    Les DEUX sources, et la plus prudente gagne.
  select coalesce(
           (select m.numero_mandat from public.app_mandat m
             where m.hektor_annonce_id::text = clean_ann
               and nullif(trim(coalesce(m.numero_mandat,'')),'') is not null
             limit 1),
           (select d.numero_mandat::text from public.app_dossiers_current d
             where d.hektor_annonce_id::text = clean_ann
               and nullif(trim(coalesce(d.numero_mandat::text,'')),'') is not null
             limit 1))
    into v_numero;

  if v_numero is not null then
    -- ⛔ Le message porte le numero : l'ecran doit pouvoir le MONTRER, pas juste
    --    dire « non ». Un refus qu'on ne peut pas expliquer sera conteste.
    raise exception 'mandat_numerote_%', v_numero using errcode = '42501';
  end if;

  -- ── 3. LA TRADUCTION ──
  --    Le front passe le numero HEKTOR (celui que degroupproprio exige, releve a
  --    l'ecran : degroupproprioForAnnonce('414472','63112')). app_relation, lui,
  --    est sur NOS numeros. Sans cette traduction on viserait la mauvaise ligne --
  --    ou aucune, EN SILENCE.
  select c.hektor_contact_id::bigint into v_notre_id
    from public.app_contact_current c
   where c.hektor_target_id = clean_id
   limit 1;

  if v_notre_id is null then
    -- Repli : le front a peut-etre deja passe NOTRE numero.
    select c.hektor_contact_id::bigint into v_notre_id
      from public.app_contact_current c
     where c.hektor_contact_id = clean_id
     limit 1;
  end if;
  if v_notre_id is null then
    raise exception 'contact_introuvable_%', clean_id using errcode = '22023';
  end if;

  -- ── 4. LE TRAVAIL D'ABORD ──
  --    Patron du 30/09 (« creer un contact et le rattacher ») : le travail porte les
  --    garde-fous ; s'il ne peut pas etre pose, RIEN ne s'ecrit -- l'exception
  --    annule toute la transaction.
  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json,
     status, priority, requested_by, requested_at)
  values
    ('unlink_hektor_mandant', target_app_dossier_id, clean_ann,
     jsonb_build_object(
       'contact_id',        clean_id,        -- le numero HEKTOR, pour degroupproprio
       'app_contact_id',    v_notre_id,      -- le notre, pour defaire si Hektor refuse
       'hektor_annonce_id', clean_ann),
     'pending', coalesce(job_priority, 18), auth.uid(), now())
  returning * into created_job;

  -- ── 5. LE RETRAIT OPTIMISTE ──
  --    La vue app_contact_relations_current filtre sur `retire_le IS NULL` :
  --    la ligne disparait de l'ecran A LA SECONDE.
  --    ⚠ `retire_le IS NULL` dans le WHERE : un lien deja retire n'est pas redate.
  update public.app_relation
     set retire_le  = now()::text,
         retire_par = coalesce(auth.uid()::text, 'app')
   where app_contact_id = v_notre_id
     and hektor_annonce_id = clean_ann
     and retire_le is null;
  get diagnostics v_touchees = row_count;

  if v_touchees = 0 then
    -- ⛔ ON NE LAISSE PAS PASSER UN TRAVAIL QUI NE CORRESPOND A RIEN. Si aucune
    --   ligne n'a bouge, c'est que le lien n'existe pas (ou est deja retire) :
    --   poser le travail quand meme ferait agir le worker chez Hektor sur une
    --   base fausse. L'exception annule AUSSI l'insertion du travail.
    raise exception 'lien_introuvable_ou_deja_retire' using errcode = '22023';
  end if;

  return created_job;
end
$function$;

REVOKE ALL ON FUNCTION public.app_unlink_mandant_optimistic(bigint,text,text,integer) FROM public;
GRANT EXECUTE ON FUNCTION public.app_unlink_mandant_optimistic(bigint,text,text,integer) TO authenticated;

COMMENT ON FUNCTION public.app_unlink_mandant_optimistic(bigint,text,text,integer) IS
  'Retirer un mandant d''un bien (④, 02/10/2026). Pose le travail unlink_hektor_mandant '
  'ET le retrait optimiste (retire_le/retire_par) -- la vue filtre dessus, donc la ligne '
  'disparait de l''ecran a la seconde. REFUSE si le bien porte un numero de mandat '
  '(regle de Frederic). Le chemin de RETOUR -- effacer retire_le si Hektor refuse -- '
  'est dans le worker : lui seul sait si Hektor a dit oui.';

-- ⛔ GARDE-FOU : la fonction existe, elle est SECURITY DEFINER, et le type de
--   travail est accepte. Une migration qui ne verifie pas son propre resultat n'est
--   qu'un espoir.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.proname='app_unlink_mandant_optimistic' AND p.prosecdef;
  IF n <> 1 THEN
    RAISE EXCEPTION 'ARRET : la RPC n''existe pas, ou pas en SECURITY DEFINER (% trouvee(s))', n;
  END IF;
  IF NOT (SELECT pg_get_constraintdef(c.oid) ~ 'unlink_hektor_mandant'
            FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
           WHERE t.relname='app_console_job' AND c.conname='app_console_job_job_type_check') THEN
    RAISE EXCEPTION 'ARRET : le type de travail n''est pas autorise par la contrainte.';
  END IF;
  RAISE NOTICE 'OK : RPC posee, type de travail autorise.';
END $$;

COMMIT;

-- ─── A LIRE APRES LE COMMIT ─────────────────────────────────────────────────────
-- SELECT proname, prosecdef FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
--  WHERE n.nspname='public' AND proname='app_unlink_mandant_optimistic';
--
-- ⛔ RIEN NE S'EN SERT ENCORE : ni le worker (④c), ni le front (④d). La RPC est
--   posee et dormante. Le premier appel reel devra se faire SUR UN BIEN D'ESSAI,
--   avec accord explicite -- c'est une ecriture chez Hektor.
