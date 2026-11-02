-- ════════════════════════════════════════════════════════════════════════════
--  LA TOLERANCE DU MILLIEME -- aligner l'ECRAN sur l'IMPORTEUR     02/11/2026
-- ════════════════════════════════════════════════════════════════════════════
--
--  LE DEFAUT, mesure le 02/11 :
--    12 dossiers REELS et VENDUS (annonces 9371, 11840, 11841, 14355, 14464,
--    32615, 41427, 54768, 55085, 58905, 59183, 61412) ont un total de
--    100,001 % -- parce que HEKTOR lui-meme ne tombe pas juste : la conversion
--    du 16/09 a ramene par exemple 50,030 a l'entree et 49,971 a la sortie.
--    On les a recopies fidelement, et c'etait la bonne decision.
--
--  ⛔ MAIS LA MEME BASE A DEUX PORTES AVEC DEUX REGLES :
--    . app_repartition_absorber (l'importeur) refuse au-dela de 100.001
--    . app_repartition_commission_set (l'ecran) refuse au-dela de 100
--    La porte large les a laisses ENTRER, la porte etroite refuse de les
--    laisser RESSORTIR. Ce n'est pas un choix : c'est un oubli.
--
--  ⚠ ET LE REFUS EST MUET : l'ecran ne previent qu'au-dela de 0,01 d'ecart,
--    or l'ecart vaut 0,001 -- dix fois trop petit. L'utilisateur voyait sa
--    vente partir chez Hektor, puis le mot « total_superieur_a_cent ».
--
--  ⭐ CE PATCH NE CHANGE QU'UNE LIGNE : le seuil passe de 100 a 100.001, la
--    valeur DEJA tranchee dans l'importeur. Aucune donnee touchee, aucun
--    calcul modifie, le reste de la fonction est rejoue A L'IDENTIQUE.
--
--  ⚠ CE QUE CA NE CHANGE PAS : 100,002 reste REFUSE (temoin inverse), et la
--    regle « on ne distribue pas plus que la commission » tient toujours.
--
--  EMPREINTE ATTENDUE AVANT : ac980aab69f08bfca742081c65000739
--  RETOUR ARRIERE : patch_repartition_tolerance_millieme_2026-11-02_INVERSE.sql
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
    -- ⭐⭐ LA TOLERANCE DU MILLIEME (02/11/2026) -- LA MEME QUE L'IMPORTEUR.
    --   HEKTOR NE TOMBE PAS JUSTE : 50,030 + 49,971 = 100,001. 12 dossiers
    --   reels et vendus etaient ainsi IMPOSSIBLES A REENREGISTRER, alors que
    --   c'est NOUS qui les avions importes -- par une porte qui, elle, tolere
    --   100.001 (app_repartition_absorber). Deux portes, deux regles : l'oubli
    --   est corrige ici, pas dans les donnees.
    --   ⚠ LE SEUIL RESTE STRICT AU-DELA : 100,002 est toujours refuse, et
    --     personne ne decide un partage au millieme pres.
    if v_total > 100.001 then
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
        -- L'ecran affiche ce reste : en dessous de 100, une part n'est attribuee
        -- a personne, et il vaut mieux le dire que le laisser deviner.
        'non_attribue', 100 - v_total);
end;
$function$;
