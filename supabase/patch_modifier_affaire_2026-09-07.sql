-- ═══════════════════════════════════════════════════════════════════════════════
-- 3.2 — MODIFIER UNE TRANSACTION : le geste a sa propre RPC      07/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de la migration `modifier_affaire_optimistic`.
--
-- POURQUOI UNE RPC A PART, ET PAS UN DRAPEAU DANS CELLE DE LA CREATION.
-- Essai reel du 07/09 : le bouton « Modifier chez Hektor » a bien fait voyager
-- l'intention jusqu'au worker (reprendre_transaction = true, verifie dans la
-- charge), MAIS app_change_annonce_status_optimistic frappe un numero NEUF sans
-- condition --
--     v_affaire_id := nextval('app_affaire_id_app_seq');
-- -> l'affaire 1001348 est nee au lieu de reprendre 1001347. Une correction
--    fabriquait un dossier de plus.
--
-- ⚠ ET LA RPC NE PEUT PAS DEVINER LA CIBLE. Sur l'annonce temoin il y a SEPT
--   offres : « l'affaire vivante de ce genre » ne designe rien d'unique. C'est
--   l'ECRAN qui sait laquelle il affiche (affaireCourantePourStatut). Il envoie
--   donc son app_affaire_id. « L'utilisateur designe, le worker execute. »
--
-- CE QU'ON NE TOUCHE PAS : app_change_annonce_status_optimistic reste identique.
-- La creation n'est pas mise en danger par le geste de modification.
--
-- ⚠ LA MODIFICATION N'EST PAS UNE CREATION DEGUISEE : on refuse une affaire sans
--   numero Hektor (rien a modifier chez eux) et une affaire effacee (Hektor ne
--   l'a plus). Mieux vaut une erreur claire qu'une creation muette.
-- ⚠ ON N'INTERDIT AUCUN ETAT -- arbitrage de Frederic du 07/09 : « il faut
--   pouvoir modifier des offres refusees dans le cas ou l'on veut la passer en
--   valide [...] idem un compromis peut etre debloque en cas d'erreur ». Si
--   Hektor refuse (« un compromis cloture ne peut pas etre modifie », mesure du
--   03/09), c'est LUI qui le dira, et on montrera sa reponse.
--
-- RETOUR ARRIERE : DROP FUNCTION public.app_modifier_affaire_optimistic. Le
-- front retombe alors sur l'ancien chemin (et « Modifier » recreerait -- donc
-- retirer aussi le bouton).
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_modifier_affaire_optimistic(
  target_affaire_id bigint, job_payload jsonb, job_priority integer DEFAULT 7)
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
  -- ⚠ « vide ne gagne pas » : un champ laisse blanc dans la modale n'efface pas
  --   ce qui est deja la.
  update public.app_affaire_ledger
     set montant = coalesce(nullif(btrim(coalesce(v_payload->>'amount',
                                                  v_payload->>'sale_price', '')), ''), montant),
         date    = coalesce(nullif(btrim(coalesce(v_payload->>'transaction_date', '')), ''), date)
   where app_affaire_id = a.app_affaire_id;

  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───
  -- Meme liste que la creation. L'origine dit « modification_app » pour qu'on
  -- sache, en relisant, d'ou vient la valeur.
  for v_champ in
    select * from (values
      ('montant',            coalesce(v_payload->>'amount', v_payload->>'sale_price')),
      ('date',               v_payload->>'transaction_date'),
      ('date_acte',          v_payload->>'signature_date'),
      ('sequestre',          v_payload->>'sequestration'),
      ('prix_net_vendeur',   v_payload->>'net_seller_price'),
      ('prix_publique',      v_payload->>'sale_price'),
      ('honoraires',         v_payload->>'buyer_fees'),
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
      values (a.app_affaire_id, v_champ.champ, v_valeur, 'modification_app',
              coalesce(auth.uid()::text, 'app'))
      on conflict (app_affaire_id, champ) do update
        set valeur_app = excluded.valeur_app,
            origine    = excluded.origine,
            ecrit_par  = excluded.ecrit_par,
            ecrit_le   = now();
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
