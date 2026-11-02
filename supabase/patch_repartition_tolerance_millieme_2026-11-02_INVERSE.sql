-- ════════════════════════════════════════════════════════════════════════════
--  RETOUR ARRIERE de la tolerance du millieme                      02/11/2026
-- ════════════════════════════════════════════════════════════════════════════
--  Remet le seuil STRICT (> 100) dans app_repartition_commission_set.
--
--  ⚠ CE QU'IL FAUT SAVOIR AVANT DE LE JOUER : en revenant en arriere, les 12
--    dossiers a 100,001 % redeviennent IMPOSSIBLES A REENREGISTRER depuis
--    l'ecran (annonces 9371, 11840, 11841, 14355, 14464, 32615, 41427, 54768,
--    55085, 58905, 59183, 61412). Et l'importeur, lui, continuera de les
--    accepter : l'incohherence des deux portes revient avec.
--
--  ⚠ CE PATCH NE JUGE QUE SA PART (lecon 31) : il ne touche NI l'ecran
--    (l'avertissement et la traduction des refus vivent dans App.tsx) NI les
--    donnees -- aucune ligne de repartition n'a ete modifiee a la pose.
--
--  EMPREINTE APRES LA POSE : f8374e828c830cbfc86d57a156461c5c
--  EMPREINTE ATTENDUE APRES CE RETOUR : ac980aab69f08bfca742081c65000739
-- ════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_repartition_commission_set(target_chaine_id bigint, target_dossier_id bigint, lignes jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
    v_annonce text;
    v_total   numeric := 0;
    v_ligne   jsonb;
    v_ecrites integer := 0;
begin
    -- ── LE DOSSIER EXISTE-T-IL ? ──
    select max(hektor_annonce_id::text) into v_annonce
      from app_affaire_ledger
     where app_chaine_id = target_chaine_id;
    if v_annonce is null then
        raise exception 'chaine_inconnue' using errcode = '22023';
    end if;

    -- ── LE MEME CONTROLE QUE LA MODALE QUI PORTE LA SAISIE ──
    if not public.app_console_can_request_job(
            'change_hektor_annonce_status', target_dossier_id, v_annonce) then
        raise exception 'forbidden_repartition' using errcode = '42501';
    end if;

    -- ── CE QUI ARRIVE EST-IL SENSE ? On valide AVANT d'effacer quoi que ce soit :
    --    un refus a mi-chemin laisserait le dossier sans repartition du tout.
    if lignes is null or jsonb_typeof(lignes) <> 'array' then
        raise exception 'lignes_attendues' using errcode = '22023';
    end if;
    for v_ligne in select * from jsonb_array_elements(lignes) loop
        if coalesce(v_ligne->>'cote', '') not in ('entree', 'sortie') then
            raise exception 'cote_invalide' using errcode = '22023';
        end if;
        if coalesce(v_ligne->>'rang', '') not in ('1', '2', '3') then
            raise exception 'rang_invalide' using errcode = '22023';
        end if;
        if coalesce(trim(v_ligne->>'hektor_user_id'), '') = '' then
            raise exception 'personne_manquante' using errcode = '22023';
        end if;
        v_total := v_total + coalesce((v_ligne->>'pourcentage')::numeric, 0);
    end loop;
    if v_total > 100 then
        raise exception 'total_superieur_a_cent' using errcode = '22023';
    end if;

    -- ── ON REMPLACE, EN UNE FOIS ──
    delete from app_affaire_repartition where app_chaine_id = target_chaine_id;

    insert into app_affaire_repartition (
        app_chaine_id, app_dossier_id, cote, rang, hektor_user_id,
        nom_au_moment, pourcentage, origine, ecrit_par)
    select target_chaine_id,
           target_dossier_id,
           x->>'cote',
           (x->>'rang')::smallint,
           trim(x->>'hektor_user_id'),
           nullif(trim(coalesce(x->>'nom_au_moment', '')), ''),
           coalesce((x->>'pourcentage')::numeric, 0),
           nullif(trim(coalesce(x->>'origine', '')), ''),
           coalesce(auth.uid()::text, 'app')
      from jsonb_array_elements(lignes) as x;
    get diagnostics v_ecrites = row_count;

    return jsonb_build_object(
        'app_chaine_id', target_chaine_id,
        'lignes', v_ecrites,
        'total', v_total,
        'non_attribue', 100 - v_total);
end;
$function$;
