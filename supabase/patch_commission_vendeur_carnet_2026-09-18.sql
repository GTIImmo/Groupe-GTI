-- ═══════════════════════════════════════════════════════════════════════════════
-- LA COMMISSION VENDEUR VA AU CARNET                                   18/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Demande de Frederic : « il faut absolument qu'on puisse modifier le montant de
-- la commission vendeur et acquereur sur la modale d'ajout ou de modification de
-- compromis ». Elle n'est pas forcement celle du mandat : elle se negocie.
--
-- LA MODALE envoie desormais `seller_fees` -- et SEULEMENT si la case a ete
-- touchee. LE WORKER la pose dans montantHonoraireEntree (Hektor la GARDE :
-- campagne du 08/09, 12 345 envoye, 12 345 retenu). CE PATCH l'inscrit au CARNET,
-- que le run ne touche jamais, pour qu'elle ne soit pas remplacee par la valeur
-- de Hektor avant d'y etre arrivee. Le verdict la retire une fois arrivee
-- (CARNET_VERS_REGISTRE, worker).
--
-- UNE LIGNE AJOUTEE DANS CHAQUE FONCTION, RIEN D'AUTRE. Les definitions sont
-- celles EN SERVICE le 18/09 (pg_get_functiondef), pas celles des fichiers.
-- SIGNATURES INCHANGEES -> CREATE OR REPLACE, les droits sont conserves.
-- RETOUR ARRIERE : retirer la ligne 'honoraires_entree' des deux listes.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_change_annonce_status_optimistic(target_dossier_id bigint, target_status text, job_payload jsonb, job_priority integer DEFAULT 7)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  d               app_dossier_current%rowtype;
  v_kind          text;
  v_affaire_id    bigint;
  v_job_id        uuid;
  v_acquereur     text;
  v_acquereur_app bigint;
  v_payload       jsonb;
  v_champ         record;
  v_valeur        text;
  v_au_carnet     int := 0;
  -- 2.6 (06/09/2026) : TOUS les acquereurs, le principal en tete.
  v_acquereurs    text[];
  v_acq_json      jsonb;
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;

  -- Meme controle qu'avant : admin seulement. Regle metier, pas limite technique.
  if not public.app_console_can_request_job('change_hektor_annonce_status',
                                            target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_change_status' using errcode = '42501';
  end if;

  v_kind := case target_status
              when 'offer'      then 'offre'
              when 'compromise' then 'compromis'
              when 'sold'       then 'vente'
              else null end;

  v_payload   := coalesce(job_payload, '{}'::jsonb);
  v_acquereur := nullif(trim(coalesce(v_payload->>'buyer_contact_id', '')), '');

  -- L'ACQUEREUR PAR LE NUMERO DE L'APP, a cote de celui de Hektor. Sans lui, le
  -- lien entre une vente et son acheteur meurt avec la coupure -- 2 802 affaires
  -- l'ont deja perdu. Vide si le contact nous est inconnu : on n'invente pas.
  if v_acquereur is not null then
    select c.app_contact_id into v_acquereur_app
      from app_contact_current c
     where c.hektor_contact_id = v_acquereur
     limit 1;
  end if;

  -- ─── 2.6 : LA LISTE DES ACQUEREURS, ET LEURS NOMS ───
  --
  -- LE TROU QU'ON COMBLE : le RPC ecrivait l'identifiant de l'acheteur mais
  -- AUCUN NOM. Une transaction creee depuis l'app restait donc anonyme a l'ecran
  -- jusqu'au run de nuit -- alors que 1.8 (05/09) venait justement de faire en
  -- sorte que la rubrique Affaires les nomme tous. L'ecran aurait propose de
  -- choisir plusieurs acquereurs, puis n'en aurait affiche aucun.
  --
  -- ⚠ LE PRINCIPAL RESTE EN TETE : c'est buyer_contact_id, celui que le worker
  --   envoie a Hektor. La liste ne le remplace pas, elle l'entoure.
  -- ⚠ ET LE RUN REPRENDRA LA MAIN : ces deux colonnes sont dans son ON CONFLICT
  --   DO UPDATE. Ce qu'on ecrit ici ne vaut que pour la fenetre d'attente.
  select array_agg(x order by ord) into v_acquereurs from (
    select 0 as ord, v_acquereur as x where v_acquereur is not null
    union all
    select 1 as ord, nullif(trim(e), '') as x
      from jsonb_array_elements_text(
             case when jsonb_typeof(v_payload->'buyer_contact_ids') = 'array'
                  then v_payload->'buyer_contact_ids' else '[]'::jsonb end) as e
     where nullif(trim(e), '') is not null
       and nullif(trim(e), '') is distinct from v_acquereur
  ) s;
  if v_acquereurs is not null then
    v_acq_json := public.app_acquereurs_json(v_acquereurs);
  end if;

  if v_kind is not null then
    -- LE NUMERO VIENT DE LA PLAGE RESERVEE A L'APP (>= 1 000 000) : la serie du serveur
    -- local (MAX+1, a 28 981) ne peut pas la rejoindre.
    v_affaire_id := nextval('public.app_affaire_id_app_seq');

    insert into public.app_affaire_ledger
      (app_affaire_id, app_dossier_id, hektor_annonce_id, kind, app_chaine_id,
       hektor_affaire_id, hektor_acquereur_id, app_contact_id, numero_mandat,
       acquereur_json, acquereurs_json,
       state, montant, date, payload_json,
       first_seen_at, last_seen_at, present_in_hektor)
    values
      (v_affaire_id, target_dossier_id, d.hektor_annonce_id::bigint, v_kind,
       -- LE DOSSIER D'AFFAIRE, des maintenant. ⚠ CHANGEMENT DU 05/09/2026 : on ne
       -- regroupe plus par acquereur mais par la SEQUENCE ouverte sur le bien
       -- (offre -> compromis -> vente). L'identite de l'acheteur change d'une etape
       -- a l'autre -- l'offre au nom de Monsieur, le compromis aux deux noms, l'acte
       -- au nom de Madame -- et l'ancienne regle en faisait trois dossiers. Mesure :
       -- 1 034 ventes etaient separees de leur propre compromis.
       -- La regle vit dans app_chaine_pour(annonce, acquereur, genre, numero), et
       -- elle doit rester identique a recalculer_les_chaines() du serveur local.
       public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur, v_kind, v_affaire_id),
       null,                      -- Hektor ne la connait pas encore : la case reste VIDE
       v_acquereur,
       v_acquereur_app,           -- l'acquereur par NOTRE numero
       nullif(trim(coalesce(v_payload->>'numero_mandat','')), ''),
       -- le principal seul, comme le miroir le range pour une offre
       case when v_acq_json is not null and jsonb_array_length(v_acq_json) > 0
            then v_acq_json->0 else null end,
       v_acq_json,                -- TOUS, dans l'ordre, le principal en tete (2.6)
       'en_cours',
       nullif(trim(coalesce(v_payload->>'amount', v_payload->>'sale_price','')), ''),
       nullif(trim(coalesce(v_payload->>'transaction_date','')), ''),
       v_payload,
       now(), now(),
       false);                    -- delete-never : le run de nuit la conservera

    -- ─── LA SAISIE VA AU CARNET, QUE LE RUN NE TOUCHE JAMAIS ───
    -- payload_json sera remplace par la version de Hektor des le prochain run.
    -- Le carnet, lui, garde ce que VOUS avez ecrit. Un champ de plus dans la
    -- modale ? Une ligne de plus dans cette carte, et rien d'autre.
    for v_champ in
      select * from (values
        ('montant',            coalesce(v_payload->>'amount', v_payload->>'sale_price')),
        ('date',               v_payload->>'transaction_date'),
        ('date_acte',          v_payload->>'signature_date'),
        ('sequestre',          v_payload->>'sequestration'),
        ('prix_net_vendeur',   v_payload->>'net_seller_price'),
        ('prix_publique',      v_payload->>'sale_price'),
        ('honoraires',         v_payload->>'buyer_fees'),
        -- 18/09 : la commission VENDEUR, negociee au compromis.
        ('honoraires_entree',  v_payload->>'seller_fees'),
        ('numero_mandat',      coalesce(nullif(trim(coalesce(v_payload->>'selected_mandat','')), ''),
                                        v_payload->>'numero_mandat')),
        ('jours_validite',     v_payload->>'validity_days'),
        ('jours_retractation', v_payload->>'retraction_days'),
        ('notaire_id',         v_payload->>'buyer_notary_id'),
        ('taux_honoraires',    v_payload->>'buyer_fees_rate')
      ) as c(champ, valeur)
    loop
      v_valeur := nullif(btrim(coalesce(v_champ.valeur, '')), '');
      if v_valeur is not null then
        insert into public.app_affaire_champ_app
          (app_affaire_id, champ, valeur_app, origine, ecrit_par)
        values (v_affaire_id, v_champ.champ, v_valeur, 'creation_app',
                coalesce(auth.uid()::text, 'app'))
        on conflict (app_affaire_id, champ) do update
          set valeur_app = excluded.valeur_app,
              origine    = excluded.origine,
              ecrit_par  = excluded.ecrit_par,
              ecrit_le   = now();
        v_au_carnet := v_au_carnet + 1;
      end if;
    end loop;
  end if;

  -- Le travail emporte le numero d'affaire : c'est lui qui permettra de la retrouver.
  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  values
    ('change_hektor_annonce_status', target_dossier_id, d.hektor_annonce_id::text,
     case when v_affaire_id is null then v_payload
          else v_payload || jsonb_build_object('app_affaire_id', v_affaire_id) end,
     coalesce(job_priority, 7), auth.uid())
  returning id into v_job_id;

  return jsonb_build_object('job_id', v_job_id,
                            'app_affaire_id', v_affaire_id,
                            'kind', v_kind,
                            'app_contact_id', v_acquereur_app,
                            'acquereurs', coalesce(jsonb_array_length(v_acq_json), 0),
                            'champs_au_carnet', v_au_carnet);
end
$function$;

CREATE OR REPLACE FUNCTION public.app_modifier_affaire_optimistic(target_affaire_id bigint, job_payload jsonb, job_priority integer DEFAULT 7)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  a           app_affaire_ledger%rowtype;
  d           app_dossier_current%rowtype;
  v_payload   jsonb;
  v_job_id    uuid;
  v_champ     record;
  v_valeur    text;
  v_photo     text;
  v_au_carnet int := 0;
  v_cle       text;
  v_cible     text;
begin
  select * into a from app_affaire_ledger where app_affaire_id = target_affaire_id;
  if not found then raise exception 'affaire_not_found' using errcode = '22023'; end if;

  if not public.is_app_admin() then
    raise exception 'not_allowed' using errcode = '42501';
  end if;
  if not public.app_console_can_access_dossier(a.app_dossier_id, a.hektor_annonce_id::text) then
    raise exception 'dossier_not_allowed' using errcode = '42501';
  end if;

  -- ─── ON NE MODIFIE QUE CE QUE HEKTOR CONNAIT ───
  if coalesce(btrim(a.hektor_affaire_id::text), '') = '' then
    raise exception 'modification_sans_numero_hektor : cette transaction n''existe pas encore chez Hektor'
      using errcode = '22023';
  end if;
  if a.present_in_hektor is false then
    raise exception 'modification_transaction_effacee : Hektor ne la rend plus'
      using errcode = '22023';
  end if;

  select * into d from app_dossier_current where app_dossier_id = a.app_dossier_id;
  v_payload := coalesce(job_payload, '{}'::jsonb);

  -- ─── LA CHARGE PORTE L'INTENTION *ET* LA CIBLE ───
  -- Le worker lit `reprendre_transaction` (le verrou) puis `<genre>_id` (le quoi).
  -- Sans les deux, idTransactionAReprendre() rend "" et le worker CREE.
  v_cle   := case a.kind when 'offre' then 'offre_id'
                         when 'compromis' then 'compromis_id'
                         else 'vente_id' end;
  v_cible := case a.kind when 'offre' then 'offer'
                         when 'compromis' then 'compromise'
                         else 'sold' end;

  v_payload := v_payload || jsonb_build_object(
      'reprendre_transaction', true,
      'app_affaire_id',        a.app_affaire_id,
      v_cle,                   a.hektor_affaire_id::text,
      'target_status',         v_cible,
      'numero_dossier',        d.numero_dossier,
      'titre_bien',            d.titre_bien,
      'negociateur_email',     d.negociateur_email);

  -- ─── L'INSTANTANE : ON CORRIGE LA LIGNE, ON N'EN CREE PAS ───
  -- ⚠ « vide ne gagne pas » : un champ laisse blanc dans la modale ne doit pas
  --   effacer ce qui est deja la.
  -- ⚠ ET C'EST ELLE QUI OBLIGE A PRENDRE LA PHOTO DANS `a` : apres cet UPDATE, la
  --   ligne porte NOTRE valeur. `a` a ete lue AVANT, donc elle garde celle de
  --   Hektor -- c'est la seule reference valable.
  update public.app_affaire_ledger
     set montant = coalesce(nullif(btrim(coalesce(v_payload->>'amount',
                                                  v_payload->>'sale_price', '')), ''), montant),
         date    = coalesce(nullif(btrim(coalesce(v_payload->>'transaction_date', '')), ''), date)
   where app_affaire_id = a.app_affaire_id;

  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───
  -- Meme liste que la creation. L'origine dit « modification_app » pour qu'on
  -- sache, en relisant, d'ou vient la valeur.
  -- 3.1 (16/09) : la troisieme colonne est LA PHOTO -- ce que le registre portait
  -- de Hektor avant la saisie. NULL la ou le registre ne porte pas la valeur de
  -- Hektor : voir l'en-tete de ce fichier, aucun de ces NULL n'est un oubli.
  for v_champ in
    select * from (values
      ('montant',            coalesce(v_payload->>'amount', v_payload->>'sale_price'), a.montant::text),
      ('date',               v_payload->>'transaction_date',                           a.date::text),
      ('date_acte',          v_payload->>'signature_date',                              a.date_acte::text),
      ('sequestre',          v_payload->>'sequestration',                               a.sequestre::text),
      ('prix_net_vendeur',   v_payload->>'net_seller_price',                            a.prix_net_vendeur::text),
      ('prix_publique',      v_payload->>'sale_price',                                  null::text),
      ('honoraires',         v_payload->>'buyer_fees',                                  null::text),
      -- 18/09 : la commission VENDEUR. La photo est celle du registre, qui porte
      -- la valeur de Hektor (colonne relue a chaque run, classe C).
      ('honoraires_entree',  v_payload->>'seller_fees',                                 a.honoraires_entree::text),
      ('numero_mandat',      coalesce(nullif(trim(coalesce(v_payload->>'selected_mandat','')), ''),
                                      v_payload->>'numero_mandat'),                     a.numero_mandat::text),
      ('jours_validite',     v_payload->>'validity_days',                               a.jours_validite::text),
      ('jours_retractation', v_payload->>'retraction_days',                             null::text),
      ('notaire_id',         v_payload->>'buyer_notary_id',                             null::text),
      ('taux_honoraires',    v_payload->>'buyer_fees_rate',                             null::text)
    ) as c(champ, valeur, photo)
  loop
    v_valeur := nullif(btrim(coalesce(v_champ.valeur, '')), '');
    v_photo  := nullif(btrim(coalesce(v_champ.photo, '')), '');
    if v_valeur is not null then
      insert into public.app_affaire_champ_app
        (app_affaire_id, champ, valeur_app, origine, ecrit_par, valeur_hektor_au_moment)
      values (a.app_affaire_id, v_champ.champ, v_valeur, 'modification_app',
              coalesce(auth.uid()::text, 'app'), v_photo)
      on conflict (app_affaire_id, champ) do update
        set valeur_app = excluded.valeur_app,
            origine    = excluded.origine,
            ecrit_par  = excluded.ecrit_par,
            ecrit_le   = now(),
            -- ⚠ LA PREMIERE PHOTO GAGNE, et c'est tout le point : voir l'en-tete.
            --   Re-photographier prendrait NOTRE valeur precedente pour celle de
            --   Hektor, et la reference serait perdue en silence.
            valeur_hektor_au_moment =
              coalesce(app_affaire_champ_app.valeur_hektor_au_moment,
                       excluded.valeur_hektor_au_moment);
      v_au_carnet := v_au_carnet + 1;
    end if;
  end loop;

  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  values
    ('change_hektor_annonce_status', a.app_dossier_id, a.hektor_annonce_id::text,
     v_payload, coalesce(job_priority, 7), auth.uid())
  returning id into v_job_id;

  return jsonb_build_object('ok', true,
                            'job_id', v_job_id,
                            'app_affaire_id', a.app_affaire_id,
                            'kind', a.kind,
                            'hektor_affaire_id', a.hektor_affaire_id,
                            'champs_au_carnet', v_au_carnet);
end
$function$;
