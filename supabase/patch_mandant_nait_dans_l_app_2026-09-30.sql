-- ═══════════════════════════════════════════════════════════════════════════════
-- F -- CREER UN CONTACT ET LE RATTACHER : IL NAIT DANS L'APP    30/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC. Demande AUSSI le redemarrage des 4 services.
--
-- ─── LE GESTE ───────────────────────────────────────────────────────────────────
-- Sur une fiche bien, « ajouter un mandant » avec une personne QUI N'EXISTE PAS
-- ENCORE. Deux choses a creer d'un coup : la personne, et le lien.
--
-- AUJOURD'HUI   une etiquette provisoire, purgee sous 24 h
--               le worker cree la personne chez Hektor
--               ... la nuit ... le run recopie
--               -> si le run rate, LE GESTE EST PERDU
--               -> a la coupure, plus rien n'arrive
--
-- DESORMAIS     la personne NAIT dans l'app, avec NOTRE numero
--               le lien durable est pose dans le meme geste
--               le worker fait exactement ce qu'il faisait
--
-- ─── POURQUOI ON NE POUVAIT PAS SIMPLEMENT ENCHAINER DEUX FONCTIONS ─────────────
-- `app_create_contact_optimistic` fait naitre un contact depuis le 21/09 -- mais
-- elle pose AUSSI un travail « cree ce contact chez Hektor ». Enchainee au geste
-- mandant, qui pose « cree ce contact ET rattache-le », HEKTOR LE CREERAIT DEUX
-- FOIS. Il ne doit y avoir QU'UN SEUL TRAVAIL : celui du mandant.
-- On reprend donc ici la naissance du contact, sans son travail.
--
-- ─── CE QUI MANQUAIT COTE WORKER : UNE ADRESSE, PAS UN MECANISME ────────────────
-- ⚠ JE M'ETAIS TROMPE EN DISANT « il faut apprendre au worker a rapporter le
--   numero ». IL LE RAPPORTE DEJA : il le pose sur l'etiquette provisoire
--   (lierRelationProvisoire). Ce qu'il ne faisait pas, c'est le poser dans LA
--   CASE DU CONTACT -- parce qu'il n'y avait pas de contact.
--   Frederic avait raison de me pousser : « il y a deja un worker qui fait cela,
--   audite mon projet, il faut donc l'adapter ». Le bloc ajoute est COPIE du
--   geste voisin (creation de contact globale), qui le fait depuis le 21/09,
--   avec son piege deja paye : n'envoyer QUE la case cible (un PATCH qui
--   ajoutait une colonne inexistante a ete rejete en 400, et la case est restee
--   vide).
--
-- ─── L'ORDRE, ET IL EST VOULU ───────────────────────────────────────────────────
--   1. on tire NOTRE numero (app_contact_identite_seq, plage >= 20 000 000)
--   2. ON POSE LE TRAVAIL D'ABORD -- c'est lui qui porte les GARDE-FOUS (nom,
--      email, permission). S'il refuse, RIEN n'est ecrit : tout est annule.
--   3. puis le contact durable, puis le lien durable
--   4. puis l'etiquette provisoire, INCHANGEE -- c'est elle qui assure
--      l'affichage immediat, et elle n'a pas bouge
--
-- ─── CE QUE L'ECRAN MONTRERA ────────────────────────────────────────────────────
-- Le lien durable porte present_in_hektor = false : Hektor ne le connait pas
-- encore. LA VUE NE LE MONTRE DONC PAS TOUT DE SUITE (filtre du patch A).
-- L'affichage immediat reste assure par l'etiquette provisoire, comme avant.
-- Le lien apparait durablement quand Hektor l'a confirme.
-- ⭐ MAIS LE CONTACT, LUI, EXISTE IMMEDIATEMENT dans l'annuaire, avec son numero.
--
-- EPROUVE en BEGIN/ROLLBACK :
--     contact 20000002 « Jean ESSAI » -- case cible encore vide, c'est normal
--     lien n° 1 000 007, role mandant, present_in_hektor = false
--     visible a l'ecran : 0 -- voulu
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- Rejouer la version d'origine, gardee dans
-- supabase/fonctions_gestes_mandant_ETAT_2026-09-30.sql (1/4).
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_create_mandant_contact_optimistic(
    target_app_dossier_id bigint, target_hektor_annonce_id text,
    contact_payload jsonb, job_priority integer DEFAULT 18)
 RETURNS app_console_job
 LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
declare
  created_job public.app_console_job;
  v_token     uuid := gen_random_uuid();
  v_label     text;
  v_identite  text;
begin
  -- 1. NOTRE numero, tire avant tout : le travail doit l'emporter.
  v_identite := nextval('public.app_contact_identite_seq')::text;

  -- 2. LE TRAVAIL D'ABORD -- il porte les garde-fous. S'il refuse, rien ne
  --    s'ecrit : l'exception annule toute la fonction.
  --    Le jeton ET l'identite voyagent dans la charge :
  --    app_console_create_mandant_contact_job fait « contact_payload || ... »
  --    et n'ecrase pas ces cles.
  created_job := public.app_console_create_mandant_contact_job(
      target_app_dossier_id, target_hektor_annonce_id,
      coalesce(contact_payload, '{}'::jsonb)
        || jsonb_build_object('creation_token', v_token, 'app_identite', v_identite),
      job_priority);

  -- 3. LE CONTACT DURABLE + LE LIEN DURABLE, best effort.
  begin
    insert into public.app_contact_current(
      hektor_contact_id, app_contact_id, nom, prenom, display_name, email,
      phone_primary, negociateur_email, agence_nom, archive,
      date_enregistrement, date_maj, typologies_json, source_hash, refreshed_at)
    values (
      v_identite, v_identite::bigint,
      nullif(trim(coalesce(contact_payload->>'last_name', contact_payload->>'nom', '')), ''),
      nullif(trim(coalesce(contact_payload->>'first_name', contact_payload->>'prenom', '')), ''),
      nullif(trim(coalesce(contact_payload->>'first_name', contact_payload->>'prenom', '') || ' ' ||
             coalesce(contact_payload->>'last_name', contact_payload->>'nom', '')), ''),
      nullif(trim(coalesce(contact_payload->>'email', '')), ''),
      nullif(trim(coalesce(contact_payload->>'phone', contact_payload->>'telephone', '')), ''),
      nullif(trim(coalesce(contact_payload->>'hektor_user_email',
                           contact_payload->>'negociateur_email', '')), ''),
      nullif(trim(coalesce(contact_payload->>'target_agency_label',
                           contact_payload->>'agence_nom', '')), ''),
      false, now()::date::text, now()::text, '[]'::jsonb,
      'app_mandant_' || v_identite, now());

    insert into public.app_relation
      (app_relation_id, app_contact_id, app_dossier_id, hektor_annonce_id,
       hektor_contact_id, fait, role_hektor, source, relation_key,
       first_seen_at, last_seen_at, present_in_hektor, absent_depuis)
    values (nextval('public.app_relation_id_app_seq'), v_identite::bigint,
       target_app_dossier_id, trim(target_hektor_annonce_id),
       null,          -- Hektor ne connait pas encore cette personne
       'proprietaire_du_bien', 'mandant', 'app', 'app:' || v_token::text,
       now()::text, now()::text,
       false,         -- le worker n'a pas tourne : la vue attend sa confirmation
       null)
    on conflict (app_contact_id, hektor_annonce_id) do nothing;
  exception when others then
    null;
  end;

  -- 4. L'ETIQUETTE PROVISOIRE, INCHANGEE : elle assure l'affichage immediat.
  begin
    v_label := nullif(trim(
      coalesce(contact_payload->>'civilite', '') || ' ' ||
      coalesce(contact_payload->>'first_name', '') || ' ' ||
      coalesce(contact_payload->>'last_name', '')), '');

    insert into public.app_relation_provisional
      (creation_token, hektor_annonce_id, app_dossier_id,
       contact_creation_token, contact_label, role_contact, status, created_by)
    values
      (v_token, trim(target_hektor_annonce_id), target_app_dossier_id,
       v_token, v_label, 'mandant', 'pending', auth.uid()::text);
  exception when others then
    null;
  end;

  return created_job;
end;
$function$;
