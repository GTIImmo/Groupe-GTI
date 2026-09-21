-- ═══════════════════════════════════════════════════════════════════════════
-- L3 — LA PROTECTION PASSE DU BIEN AU CHAMP                       21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- L'EXEMPLE DE FREDERIC, ET IL N'AVAIT PAS DE BONNE REPONSE :
--
--    14 h  le negociateur corrige le PRIX dans l'app ; l'envoi vers Hektor echoue
--    15 h  un commercial change la SURFACE dans Hektor
--
--    protection PAR BIEN (aujourd'hui) :
--        soit on gele le bien      -> la nouvelle surface n'arrive jamais
--        soit on le rafraichit     -> le prix saisi disparait de l'ecran
--        LES DEUX SONT FAUX.
--
--    protection PAR CHAMP (ici) :
--        le prix reste celui de l'app, la surface arrive de Hektor.
--        Les deux saisies vivent, chacune la plus recente sur SON champ.
--
-- CE QUI REND CE CORRECTIF PETIT. La carte des champs du 21/09 l'a montre : la
-- ligne d'attente (app_annonce_pending.push_fields) porte DEJA la liste exacte
-- des champs saisis, un par un. Il n'y a donc rien a creer -- ni colonne, ni
-- table, ni journal : il suffit de REAPPLIQUER cette liste apres un
-- rafraichissement, au lieu de sauter le bien entier.
--
-- LES TROIS MEMES CARTES QUE L'EDITION. La fonction reprend mot pour mot les
-- correspondances de app_edit_annonce_optimistic -- colonne, cle du grand bloc,
-- et le calque pour le reste. Deux endroits qui traduisent les memes champs de
-- deux facons differentes finissent toujours par diverger : ici c'est la MEME
-- traduction, recopiee volontairement a l'identique.
--
-- ⚠ CE QU'ELLE NE FAIT PAS : creer un travail, envoyer quoi que ce soit a
--   Hektor, ou toucher a la ligne d'attente. Elle ne fait que reposer par-dessus
--   ce que l'app avait deja affiche. Une saisie soldee (ligne disparue) n'est
--   donc plus reappliquee -- c'est voulu : elle a ete tranchee.
--
-- ⚠ ET ELLE NE REND JAMAIS LA MAIN A UNE VALEUR PLUS ANCIENNE QUE HEKTOR : une
--   ligne d'attente n'existe que tant que l'envoi n'a pas abouti. Des que Hektor
--   confirme, la ligne disparait et c'est lui qui parle. Le cas « Hektor est plus
--   recent » a ete traite le 20/09 : le worker SOLDE la saisie, donc plus de
--   ligne, donc plus de reapplication.
--
-- RETOUR ARRIERE : drop function public.app_annonce_reappliquer_saisies(bigint);
--                  (et retirer ses deux appels)
-- ═══════════════════════════════════════════════════════════════════════════

create or replace function public.app_annonce_reappliquer_saisies(
  target_dossier_id bigint default null
) returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  p record;
  k text;
  v_detail jsonb;
  v_json_set jsonb;
  n_biens int := 0;
  n_champs int := 0;
  -- LES MEMES CARTES QUE app_edit_annonce_optimistic, a l'identique.
  col_map jsonb := '{"price":"prix","city":"ville","postalCode":"code_postal","mandateNumber":"numero_mandat",
                     "prix":"prix","villepublique":"ville","codepublique":"code_postal","ESTIMATION_MONTANT":"prix"}'::jsonb;
  json_map jsonb := '{"surface":"surface","roomCount":"nb_pieces","bedroomCount":"nb_chambres","landSurface":"surface_terrain_detail","latitude":"latitude_detail","longitude":"longitude_detail","garageCount":"garage_box_detail",
                      "surfappart":"surface","nbpieces":"nb_pieces","NB_CHAMBRES":"nb_chambres","surfterrain":"surface_terrain_detail","GARAGE_BOX":"garage_box_detail"}'::jsonb;
begin
  for p in
    select * from public.app_annonce_pending
     where (target_dossier_id is null or app_dossier_id = target_dossier_id)
       and push_fields is not null
       and jsonb_typeof(push_fields) = 'object'
       and push_fields <> '{}'::jsonb
  loop
    -- 1) les champs qui ont une COLONNE
    update public.app_dossier_current d set
      prix          = case when coalesce(nullif(trim(p.push_fields->>'price'),''), nullif(trim(p.push_fields->>'prix'),'')) ~ '^[0-9]+([.,][0-9]+)?$'
                           then replace(replace(coalesce(nullif(trim(p.push_fields->>'price'),''), nullif(trim(p.push_fields->>'prix'),'')),' ',''), ',', '.')::numeric
                           else d.prix end,
      ville         = coalesce(nullif(p.push_fields->>'city',''), nullif(p.push_fields->>'villepublique',''), d.ville),
      code_postal   = coalesce(nullif(p.push_fields->>'postalCode',''), nullif(p.push_fields->>'codepublique',''), d.code_postal),
      numero_mandat = coalesce(nullif(p.push_fields->>'mandateNumber',''), d.numero_mandat)
     where d.app_dossier_id = p.app_dossier_id;

    -- 2) les champs qui ont une CLE dans le grand bloc, + le calque pour le reste
    v_json_set := '{}'::jsonb;
    for k in select jsonb_object_keys(p.push_fields) loop
      if json_map ? k then
        v_json_set := v_json_set || jsonb_build_object(json_map->>k, p.push_fields->>k);
      end if;
      n_champs := n_champs + 1;
    end loop;

    update public.app_dossier_detail_current
       set detail_payload_json = (
             (coalesce(detail_payload_json,'{}')::jsonb || v_json_set)
             || jsonb_build_object(
                  'app_optimistic_overlay',
                  coalesce((coalesce(detail_payload_json,'{}')::jsonb)->'app_optimistic_overlay','{}'::jsonb)
                    || p.push_fields)
           )::text
     where app_dossier_id = p.app_dossier_id;

    n_biens := n_biens + 1;
  end loop;

  return jsonb_build_object('biens', n_biens, 'champs', n_champs);
end
$function$;

grant execute on function public.app_annonce_reappliquer_saisies(bigint) to service_role;

comment on function public.app_annonce_reappliquer_saisies(bigint) is
  'L3 21/09/2026 : repose par-dessus un bien rafraichi les champs que l''app a saisis et que Hektor n''a pas encore confirmes. Sans argument : tous les biens en attente. La protection passe ainsi du BIEN au CHAMP.';
