-- ============================================================================
-- CHANTIER 2 -- REGLER LE PERIMETRE D'UN COMPTE
-- Melanie LEGRAND passe de « reseau » a « portefeuille » (ses biens seulement).
-- Patch du 12/10/2026. Essai demande par Frederic.
--
-- POURQUOI UN PATCH ET PAS UNE CASE DANS L'APP : la case n'existe pas encore
--   (trou trouve par Frederic le 12/10 -- voir L2.12 de la note du chantier).
--   La colonne est posee et les regles s'en servent, mais ni le formulaire ni la
--   fonction serveur ne savent l'ecrire. Ce patch fait le travail en attendant.
--
-- ⚠ PAS DE REPETITION SEPAREE ICI, ET C'EST ASSUME : il s'agit d'UNE SEULE
--   VALEUR sur UNE SEULE LIGNE. Le patch affiche l'etat AVANT, change, affiche
--   l'etat APRES, et refuse si quoi que ce soit ne colle pas. L'inverse est une
--   ligne. Une repetition complete n'apporterait rien de plus ici.
--
-- ⚠⚠ CE QUE CA VA CHANGER POUR ELLE -- mesure du 12/10
--     annonces visibles        13 475  ->    142
--     archives visibles        35 318  ->    774
--     vendus / clos visibles    8 940  ->    130
--     contacts                 62 189  ->  ses contacts seulement
--     ses affaires et commissions      ->  inchange (deja « ses biens »)
--
-- ⚠⚠⚠ ET L'EFFET DE BORD A SURVEILLER : les RAPPROCHEMENTS acquereur n'ont
--      AUCUNE limite de lecture (regle « true »). Elle continuera donc de voir
--      des rapprochements qui pointent vers des biens qu'elle ne peut PLUS
--      ouvrir. L'ecran Rapprochement peut afficher des lignes incompletes.
--      C'est exactement la tension signalee le 12/10 : « voir et modifier n'ont
--      pas besoin de la meme portee », et le rapprochement a besoin du reseau.
--
-- ⚠ ET LA VITESSE : ce reglage fait tourner les branches « portefeuille » des
--   regles, qui N'ONT JAMAIS TOURNE. Le court-circuit qui protegeait tout le
--   monde ne jouera plus pour elle. A CHRONOMETRER DES LE COLLAGE.
--
-- RETOUR ARRIERE : patch_perimetre_melanie_portefeuille_2026-10-12_INVERSE.sql
--   (une ligne, immediat)
-- ============================================================================

begin;

do $reglage$
declare
    v_email   text := 'legrand@gti-immobilier.fr';
    v_cible   text := 'portefeuille';
    v_avant   text;
    v_apres   text;
    v_role    text;
    v_actif   boolean;
    v_lignes  int;
begin
    -- 1. l'etat AVANT
    select perimetre, role::text, is_active
      into v_avant, v_role, v_actif
      from public.app_user_profile
     where lower(trim(email)) = v_email;

    if v_avant is null then
        raise exception 'GARDE-FOU : aucun compte actif pour %. Patch arrete.', v_email;
    end if;
    if v_role <> 'commercial' then
        raise exception 'GARDE-FOU : % a le role « % », pas « commercial ». Le perimetre ne sert qu''aux negociateurs : patch arrete.',
            v_email, v_role;
    end if;
    if not v_actif then
        raise exception 'GARDE-FOU : le compte % est desactive. Patch arrete.', v_email;
    end if;
    if v_avant = v_cible then
        raise exception 'DEJA FAIT : % est deja en « % ». Patch arrete.', v_email, v_cible;
    end if;

    raise notice 'AVANT : % est en « % » (role %, actif).', v_email, v_avant, v_role;

    -- 2. le changement, sur UNE ligne et une seule
    update public.app_user_profile
       set perimetre = v_cible,
           updated_at = now()
     where lower(trim(email)) = v_email;

    get diagnostics v_lignes = row_count;
    if v_lignes <> 1 then
        raise exception 'GARDE-FOU : % ligne(s) modifiee(s), 1 attendue. Patch arrete.', v_lignes;
    end if;

    -- 3. l'etat APRES
    select perimetre into v_apres
      from public.app_user_profile
     where lower(trim(email)) = v_email;

    if v_apres <> v_cible then
        raise exception 'CONTROLE : le perimetre vaut « % », pas « % ». Patch arrete.', v_apres, v_cible;
    end if;

    -- 4. et personne d'autre n'a bouge
    if (select count(*) from public.app_user_profile where perimetre <> 'reseau') <> 1 then
        raise exception 'CONTROLE : % compte(s) hors « reseau », 1 attendu. Patch arrete.',
            (select count(*) from public.app_user_profile where perimetre <> 'reseau');
    end if;

    raise notice 'APRES : % est en « % ». UN SEUL compte est hors « reseau ».', v_email, v_apres;
    raise notice 'A FAIRE MAINTENANT : chronometrer ses ecrans (les branches « portefeuille » n''avaient jamais tourne).';
end
$reglage$;

commit;
