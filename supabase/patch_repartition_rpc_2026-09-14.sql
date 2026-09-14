-- =====================================================================
-- ECRIRE LA REPARTITION DEPUIS L'ECRAN                       14/09/2026
-- Chantier C.19-d, tache 3.2e, lot 5 -- suite du patch du meme jour.
-- =====================================================================
--
-- POURQUOI UNE RPC ET PAS UNE POLICY D'ECRITURE
-- ---------------------------------------------
-- `app_affaire_repartition` a la RLS active et AUCUNE policy d'ecriture : hors
-- service_role, personne n'y touche. C'est deliberé et c'est la meme demarche
-- que tous les gestes optimistes du projet -- l'ecran ne pose pas une ligne, il
-- DEMANDE un geste, et le geste verifie.
--
-- ⚠ C'EST DE L'ARGENT. Une policy d'ecriture laisserait n'importe quel compte
--   connecte reecrire la part de n'importe qui, sans que rien ne l'enregistre.
--   Ici le controle est le MEME que celui de la modale qui porte la saisie :
--   `app_console_can_request_job('change_hektor_annonce_status', ...)`, qui
--   exige le role administrateur. Qui peut changer le statut d'une annonce peut
--   dire qui touche sa commission ; les autres, non.
--
-- CE QU'ELLE FAIT, ET CE QU'ELLE REFUSE
-- -------------------------------------
-- Elle REMPLACE la repartition d'un dossier, en une fois. Pas de mise a jour
-- ligne a ligne : l'ecran connait les quatre emplacements, il les envoie tous,
-- et ce qu'il n'envoie pas disparait. Deux gestes partiels qui se croisent
-- laisseraient un total faux.
--
-- ⚠ ELLE REFUSE UN TOTAL SUPERIEUR A 100, et RIEN D'AUTRE sur le total. En
--   dessous de 100, le reste n'est simplement attribue a personne -- c'est
--   exactement ce que Hektor appelle « Part Reseau », et cela existe. L'ECRAN
--   PREVIENT quand la somme ne fait pas le compte ; la base, elle, ne refuse que
--   l'impossible. C'est la regle que Frederic a posee pour la modale : verifier,
--   c'est aider ; decider a la place de l'utilisateur, non.
--
-- ⚠ ELLE EXIGE UN DOSSIER QUI EXISTE. Une repartition sur une chaine inconnue
--   serait une ligne que personne ne retrouverait jamais.
--
-- ⚠ ELLE NE VERIFIE PAS QUE LA PERSONNE EST ACTIVE, et c'est voulu. L'ecran
--   propose les 30 actifs ; mais une repartition posee hier reste valable quand
--   quelqu'un part, et une correction doit pouvoir la rejouer telle quelle.
--   Interdire ici, ce serait rendre l'historique non modifiable.
--
-- RETOUR ARRIERE : DROP FUNCTION. La table, elle, reste.
-- =====================================================================

CREATE OR REPLACE FUNCTION public.app_repartition_commission_set(
    target_chaine_id  bigint,
    target_dossier_id bigint,
    lignes            jsonb
)
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
        if coalesce(v_ligne->>'rang', '') not in ('1', '2') then
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
        -- L'ecran affiche ce reste : en dessous de 100, une part n'est attribuee
        -- a personne, et il vaut mieux le dire que le laisser deviner.
        'non_attribue', 100 - v_total);
end;
$function$;

COMMENT ON FUNCTION public.app_repartition_commission_set(bigint, bigint, jsonb) IS
    'REMPLACE la repartition de commission d''un dossier d''affaire, en une fois. '
    'Meme controle d''acces que la modale qui porte la saisie (role administrateur). '
    'Refuse un total superieur a 100 et rien d''autre : en dessous, le reste n''est '
    'attribue a personne -- ce que Hektor appelle « Part Reseau ». L''ecran previent, '
    'la base ne refuse que l''impossible.';

REVOKE ALL ON FUNCTION public.app_repartition_commission_set(bigint, bigint, jsonb) FROM public;
GRANT EXECUTE ON FUNCTION public.app_repartition_commission_set(bigint, bigint, jsonb) TO authenticated;
