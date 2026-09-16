-- ═══════════════════════════════════════════════════════════════════════════════
-- 3.1 -- LA PHOTO DE LA SAISIE, POUR LES TRANSACTIONS          16/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de la migration `carnet_affaire_photo_de_la_saisie`.
--
-- ─── CE QUE C'EST, ET POURQUOI ───
-- Le carnet `app_affaire_champ_app` garde ce que l'app a SAISI. Il ne garde pas
-- ce que HEKTOR portait au moment de la saisie. Sans cette photo, une ligne qui
-- traine au carnet ne peut pas etre lue :
--     ma saisie n'est pas encore partie          -> normal, on attend
--     quelqu'un a change la valeur chez eux      -> CONFLIT, geste humain requis
--     Hektor a refuse ou transforme en silence   -> il sait le faire (tache 1.4)
-- Les trois se ressemblent. C'est exactement ce que `base_snapshot` resout pour
-- l'annonce depuis le 20/06 (app_annonce_pending).
--
-- MESURE DU 16/09 : le carnet porte 28 lignes, dont 17 de plus de 48 h, la plus
-- ancienne du 04/09. Certaines y sont legitimement (des champs que Hektor ne rend
-- pas), d'autres sont peut-etre des saisies perdues -- et RIEN ne les departage.
--
-- ─── UNE PHOTO PAR CHAMP, ET PAS UN INSTANTANE GLOBAL ───
-- Le patron de l'annonce photographie tout d'un bloc (`base_snapshot` jsonb),
-- parce que sa table porte UNE ligne par annonce. Le carnet des affaires porte
-- deja UNE LIGNE PAR CHAMP : la photo y est donc plus fine, et gratuite.
--
-- ─── LA PHOTO NE BOUGE PAS TANT QUE LA SAISIE ATTEND ───
-- ⚠ POINT SUBTIL, ET IL COMMANDE LE `coalesce` DE L'ON CONFLICT. La colonne du
--   registre est ecrite DE FACON OPTIMISTE par cette meme RPC : juste apres une
--   modification, elle porte NOTRE valeur, pas celle de Hektor -- jusqu'a ce que
--   le worker relise et la remplace (~40 s). Rephotographier a chaque saisie
--   prendrait donc NOTRE valeur precedente en photo, et la reference serait
--   perdue. On garde la PREMIERE photo tant que la ligne vit.
-- ⚠ ET ELLE SE RENOUVELLE TOUTE SEULE : quand la valeur arrive chez Hektor, le
--   worker RETIRE la ligne du carnet (retirerDuCarnetCeQuiEstArrive). La saisie
--   suivante repart donc d'une photo fraiche. Aucun entretien a prevoir.
--
-- ─── LES CHAMPS SANS PHOTO, ET POURQUOI C'EST ASSUME ───
-- On ne photographie QUE ce que le registre porte VRAIMENT de Hektor. Ailleurs,
-- NULL veut dire « on ne savait pas » -- et c'est plus honnete qu'une devinette :
--     prix_publique        le registre n'a PAS cette colonne (verifie le 12/09,
--                          apres un PATCH refuse en entier pour l'avoir supposee)
--     honoraires           entree ou sortie ? on ne tranche pas a la place du metier
--     jours_retractation   le registre porte une DATE de fin, pas un nombre de jours
--     notaire_id           CLASSE A : c'est NOTRE valeur, pas la leur. La
--     taux_honoraires      photographier reviendrait a se photographier soi-meme.
--
-- ─── CE QUE CETTE MIGRATION NE FAIT PAS ───
-- Elle n'ajoute AUCUN comportement : rien ne lit encore la photo. Le conflit
-- visible et la poussee partielle viennent apres, quand on aura vu ce que la
-- photo raconte. C'est volontairement le plus petit pas possible.
-- ⚠ AUCUN REDEMARRAGE DE WORKER : le worker n'est pas touche.
-- ⚠ LA DESCENTE ABSORBE LA COLONNE SEULE : elle refait la doublure
--   `app_affaire_champ_app__sb` a chaque passage depuis la spec OpenAPI.
--
-- RETOUR ARRIERE : rejouer la RPC sans les photos (la colonne peut rester, elle
-- ne gene personne), ou `ALTER TABLE ... DROP COLUMN valeur_hektor_au_moment`.
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_affaire_champ_app
  ADD COLUMN IF NOT EXISTS valeur_hektor_au_moment text;

COMMENT ON COLUMN public.app_affaire_champ_app.valeur_hektor_au_moment IS
  'La valeur que le registre portait de HEKTOR au moment de la saisie (3.1, '
  '16/09/2026). Sert a distinguer « pas encore parti » de « conflit » et de '
  '« refuse en silence ». NULL = on ne savait pas. Ne bouge pas tant que la '
  'ligne vit ; la ligne disparait quand la valeur arrive.';

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
