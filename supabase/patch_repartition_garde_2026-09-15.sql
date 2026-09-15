-- =====================================================================
-- LA BASE REFUSE D'ECRASER CE QUE L'APP A POSE            15/09/2026
-- Chantier C.19-d, tache 3.2e, lot 5 -- etape 4 du plan de sortie.
-- =====================================================================
--
-- LE PRINCIPE DE FREDERIC, 15/09, MOT POUR MOT
-- --------------------------------------------
-- « les repartitions saisies dans mon apps en ajout ou modification ecrasent
--   toute modification de Hektor ».
--
-- ⚠ AUJOURD'HUI CE PRINCIPE TIENT PAR POLITESSE, PAS PAR REGLE. Le convertisseur
--   saute les dossiers que l'app a poses -- parce qu'il est ecrit ainsi. Il tourne
--   avec `service_role`, qui contourne la RLS : s'il avait un defaut, RIEN ne
--   l'arreterait. Et il en a eu un ce matin meme, pendant quelques heures : il ne
--   reconnaissait que `origine = 'saisie'`, alors que la modale inscrit `'defaut'`
--   quand on ACCEPTE les noms proposes. Une repartition VALIDEE par un humain
--   etait donc ecrasable, et personne ne l'aurait vu.
--
-- ➡ CETTE FONCTION DEPLACE L'INTERDIT DU PROGRAMME VERS LA BASE. Le jour ou un
--   autre outil, ou une version suivante, voudra ecrire ici, il se heurtera a la
--   meme regle sans avoir besoin de la connaitre.
--
-- LA REGLE, EN UNE PHRASE
-- -----------------------
-- Un dossier dont UNE SEULE ligne ne vient pas de Hektor appartient a l'app :
-- on n'y touche pas, et on le dit.
--     'hektor', 'hektor_partage_suppose'   -> derive, rafraichissable
--     'saisie', 'defaut', NULL, tout autre -> decide par quelqu'un, intouchable
--
-- ⚠ NULL EST DU COTE DE L'APP, ET C'EST DELIBERE. Une origine qu'on ne sait pas
--   lire se traite comme une decision humaine : le doute profite a la saisie.
--
-- ⚠ ET LA PROTECTION PORTE SUR LE DOSSIER, PAS SUR LA LIGNE. Si quelqu'un n'a
--   rempli que l'entree, on n'ajoute pas la sortie de Hektor -- on laisse le
--   dossier ENTIER intact. C'est « l'app ecrase tout » pris au mot, ce que
--   Frederic a demande. Une saisie partielle reste donc partielle, et c'est une
--   consequence a connaitre, pas un defaut.
--
-- CE QU'ELLE FAIT D'UN DOSSIER QU'ELLE ACCEPTE : elle le REMPLACE en entier.
-- Pas de mise a jour ligne a ligne -- deux gestes partiels qui se croisent
-- laisseraient un total faux. Meme choix que `app_repartition_commission_set`.
--
-- ⚠ POURQUOI LES LIGNES PERIMEES DOIVENT DISPARAITRE, ET CE N'EST PAS THEORIQUE.
--   Mesure du 15/09 : en faisant entrer les ventes d'avant 2010, le rechainage a
--   deplace UN dossier sur 6 655. Le bien 1367875 portait deux cycles ; sa vente
--   de 2011 a rejoint la chaine 18855 au lieu de rester seule sur 18859, ou sa
--   repartition etait posee. Si la conversion ecrit 18855 en laissant 18859, un
--   releve par negociateur compte la commission DEUX FOIS. D'ou la purge
--   ci-dessous, qui ne touche QUE le derive.
--
-- RETOUR ARRIERE : DROP FUNCTION les deux. Les donnees restent.
-- =====================================================================

CREATE OR REPLACE FUNCTION public.app_repartition_absorber(lignes jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
declare
    v_ecrites  integer := 0;
    v_dossiers integer := 0;
    v_protege  integer := 0;
    v_refuse   integer := 0;
    v_chaine   bigint;
    v_total    numeric;
begin
    if lignes is null or jsonb_typeof(lignes) <> 'array' then
        raise exception 'lignes_attendues' using errcode = '22023';
    end if;

    -- On travaille dossier par dossier : c'est l'unite de la regle.
    for v_chaine in
        select distinct (x->>'app_chaine_id')::bigint
          from jsonb_array_elements(lignes) as x
    loop
        -- ── LE DOSSIER APPARTIENT-IL A L'APP ? ──
        if exists (
            select 1 from app_affaire_repartition r
             where r.app_chaine_id = v_chaine
               and coalesce(r.origine, '') not like 'hektor%'
        ) then
            v_protege := v_protege + 1;
            continue;                      -- on n'y touche PAS, et on le compte
        end if;

        -- ── CE QUI ARRIVE EST-IL SENSE ? On valide AVANT d'effacer : un refus a
        --    mi-chemin laisserait le dossier sans repartition du tout.
        select coalesce(sum((x->>'pourcentage')::numeric), 0) into v_total
          from jsonb_array_elements(lignes) as x
         where (x->>'app_chaine_id')::bigint = v_chaine;
        if v_total > 100.001 then
            -- ⚠ 100,001 ET PAS 100 : Hektor ecrit `percent = 200.001` la ou il
            --   veut dire 200 (sa facon de dire « cette personne prend tout, y
            --   compris l'autre cote »). 12 dossiers sur 6 655 depassent ainsi,
            --   d'un millieme. Refuser a 100 pile rejetterait de la donnee juste.
            v_refuse := v_refuse + 1;
            continue;
        end if;

        delete from app_affaire_repartition where app_chaine_id = v_chaine;

        insert into app_affaire_repartition (
            app_chaine_id, app_dossier_id, cote, rang, hektor_user_id,
            nom_au_moment, pourcentage, origine, ecrit_par)
        select v_chaine,
               nullif(x->>'app_dossier_id', '')::bigint,
               x->>'cote',
               (x->>'rang')::smallint,
               trim(x->>'hektor_user_id'),
               nullif(trim(coalesce(x->>'nom_au_moment', '')), ''),
               least(coalesce((x->>'pourcentage')::numeric, 0), 100),
               coalesce(nullif(trim(coalesce(x->>'origine', '')), ''), 'hektor'),
               'conversion'
          from jsonb_array_elements(lignes) as x
         where (x->>'app_chaine_id')::bigint = v_chaine;

        get diagnostics v_total = row_count;
        v_ecrites  := v_ecrites + v_total::integer;
        v_dossiers := v_dossiers + 1;
    end loop;

    return jsonb_build_object(
        'dossiers_ecrits', v_dossiers,
        'lignes_ecrites',  v_ecrites,
        'proteges_app',    v_protege,
        'refuses_total',   v_refuse);
end;
$function$;

COMMENT ON FUNCTION public.app_repartition_absorber(jsonb) IS
    'Absorbe une repartition DERIVEE de Hektor, dossier par dossier. REFUSE de '
    'toucher un dossier dont une seule ligne ne vient pas de Hektor : la saisie de '
    'l''app gagne toujours, et NULL est traite comme une saisie (le doute profite a '
    'l''humain). Remplace le dossier en entier -- jamais ligne a ligne. C''est la '
    'meme regle que le convertisseur appliquait par politesse ; ici elle est tenue '
    'par la BASE, donc inviolable meme en service_role.';

-- =====================================================================
-- LA PURGE DES ORPHELINES -- et elle ne touche QUE le derive
-- =====================================================================
CREATE OR REPLACE FUNCTION public.app_repartition_purger_orphelines()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
declare
    v_supprimees integer := 0;
    v_gardees    integer := 0;
begin
    -- ⚠ CE QUI VIENT DE L'APP N'EST JAMAIS SUPPRIME, MEME ORPHELIN. Une decision
    --   humaine dont la chaine a bouge doit etre RATTACHEE, pas effacee --
    --   « supprimer n'est pas annuler ». On la compte et on la laisse : c'est un
    --   geste humain qui la replacera, avec `app_dossier_id` pour la retrouver.
    select count(*) into v_gardees
      from app_affaire_repartition r
     where coalesce(r.origine, '') not like 'hektor%'
       and not exists (select 1 from app_affaire_ledger l
                        where l.app_chaine_id = r.app_chaine_id);

    delete from app_affaire_repartition r
     where coalesce(r.origine, '') like 'hektor%'
       and not exists (select 1 from app_affaire_ledger l
                        where l.app_chaine_id = r.app_chaine_id);
    get diagnostics v_supprimees = row_count;

    return jsonb_build_object(
        'derivees_supprimees', v_supprimees,
        'saisies_orphelines_gardees', v_gardees);
end;
$function$;

COMMENT ON FUNCTION public.app_repartition_purger_orphelines() IS
    'Supprime les lignes de repartition DERIVEES (origine hektor%) dont le dossier '
    'n''existe plus au registre -- cas d''un rechainage. Sans elle, la conversion '
    'ecrirait la bonne chaine en laissant la perimee, et un releve par negociateur '
    'compterait la commission DEUX FOIS (mesure du 15/09 : 1 dossier sur 6 655). '
    'Une SAISIE orpheline n''est jamais supprimee : elle est comptee et laissee.';

-- Ces deux fonctions sont des gestes de PIPELINE, pas d'ecran : l'app n'a aucune
-- raison de les appeler, et la modale a deja la sienne.
REVOKE ALL ON FUNCTION public.app_repartition_absorber(jsonb) FROM public;
REVOKE ALL ON FUNCTION public.app_repartition_purger_orphelines() FROM public;
GRANT EXECUTE ON FUNCTION public.app_repartition_absorber(jsonb) TO service_role;
GRANT EXECUTE ON FUNCTION public.app_repartition_purger_orphelines() TO service_role;
