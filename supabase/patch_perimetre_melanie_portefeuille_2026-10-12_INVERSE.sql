-- ============================================================================
-- RETOUR ARRIERE : Melanie LEGRAND repasse en « reseau »
-- Inverse de patch_perimetre_melanie_portefeuille_2026-10-12.sql
--
-- A COLLER SANS HESITER si ses ecrans sont lents ou si l'ecran Rapprochement
-- affiche n'importe quoi. C'est immediat et sans effet de bord : elle retrouve
-- exactement la vue qu'elle avait avant.
-- ============================================================================

begin;

do $retour$
declare
    v_email  text := 'legrand@gti-immobilier.fr';
    v_avant  text;
    v_lignes int;
begin
    select perimetre into v_avant
      from public.app_user_profile
     where lower(trim(email)) = v_email;

    if v_avant is null then
        raise exception 'Aucun compte pour %. Rien a faire.', v_email;
    end if;
    if v_avant = 'reseau' then
        raise notice 'RIEN A FAIRE : % est deja en « reseau ».', v_email;
        return;
    end if;

    raise notice 'AVANT : % est en « % ».', v_email, v_avant;

    update public.app_user_profile
       set perimetre = 'reseau',
           updated_at = now()
     where lower(trim(email)) = v_email;

    get diagnostics v_lignes = row_count;
    if v_lignes <> 1 then
        raise exception 'GARDE-FOU : % ligne(s) modifiee(s), 1 attendue.', v_lignes;
    end if;

    if (select count(*) from public.app_user_profile where perimetre <> 'reseau') <> 0 then
        raise exception 'CONTROLE : il reste % compte(s) hors « reseau », 0 attendu.',
            (select count(*) from public.app_user_profile where perimetre <> 'reseau');
    end if;

    raise notice 'APRES : % est revenu en « reseau ». TOUS les comptes y sont.', v_email;
end
$retour$;

commit;
