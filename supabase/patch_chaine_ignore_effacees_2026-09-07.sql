-- ═══════════════════════════════════════════════════════════════════════════════
-- CE QUE HEKTOR A EFFACE NE COMPTE PLUS DANS LA CHAINE           07/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de la migration
-- `chaine_ignore_les_transactions_effacees_chez_hektor`.
--
-- DEUXIEME DES DEUX COPIES DE LA REGLE. La premiere est recalculer_les_chaines()
-- dans phase2/sync/affaire_ledger.py, corrigee dans le meme commit. « Deux copies
-- d'une formule divergent tot ou tard » : la clause est ecrite mot pour mot des
-- deux cotes.
--
-- POURQUOI MAINTENANT. Le drapeau present_in_hektor ne s'est JAMAIS leve --
-- mesure du 07/09 : 0 ligne sur 29 327, en local comme chez Supabase. Le miroir
-- ne perdant rien, refresh_ledger revoyait toujours tout, et le defaut dormait.
-- ⚠ L'ALIGNEMENT DU MIROIR LE REVEILLE (normalize_source, meme commit) : des que
--   le miroir cessera de garder ce que Hektor a efface, une vente irait se
--   rattacher a un compromis QUI N'EXISTE PLUS -- `compromis_vivant` le
--   compterait encore. D'ou l'ordre : les chaines d'abord.
--
-- ⚠ LE FILTRE NAIF EST FAUX, et c'est le piege a connaitre. `present_in_hektor
--   is true` exclurait aussi les transactions NEES DANS L'APP : elles portent
--   present_in_hektor = false ET aucun numero Hektor jusqu'a ce que le run les
--   adopte. Une offre creee le matin perdrait son dossier jusqu'au lendemain.
--   La regle est celle de l'ecran (affaireEstVivante, App.tsx) :
--
--       exclure SI  (elle porte un numero Hektor)  ET  (present_in_hektor faux)
--       pas de numero = nee chez nous = VIVANTE
--
--   `is false` et non `= false` : un NULL veut dire « on ne sait pas », on garde.
--
-- VERIFIE AVANT DEPLOIEMENT, des deux cotes -- la correction est INERTE :
--     local     rejouee sur copie  -> 29 327 transactions, 12 648 chaines
--     Supabase  29 327 / 12 648, 0 ligne exclue par la nouvelle clause
--
-- RETOUR ARRIERE : retirer les quatre clauses marquees « 07/09 ».
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_chaine_pour(p_annonce bigint, p_acquereur text)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_acq    text := nullif(btrim(coalesce(p_acquereur, '')), '');
  v_chaine bigint;
begin
  if p_annonce is not null and v_acq is not null then
    select min(app_chaine_id) into v_chaine
      from app_affaire_ledger
     where app_chaine_id is not null
       and hektor_annonce_id = p_annonce
       and btrim(coalesce(hektor_acquereur_id, '')) = v_acq
       -- 07/09 : on ne rejoint pas une chaine par une transaction effacee chez Hektor.
       and not (btrim(coalesce(hektor_affaire_id::text, '')) <> ''
                and present_in_hektor is false);
    if v_chaine is not null then
      return v_chaine;
    end if;
  end if;
  return nextval('app_chaine_id_seq');
end;
$function$;

CREATE OR REPLACE FUNCTION public.app_chaine_pour(p_annonce bigint, p_acquereur text, p_kind text, p_app_affaire_id bigint)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_acq   text   := nullif(btrim(coalesce(p_acquereur, '')), '');
  v_kind  text   := lower(btrim(coalesce(p_kind, '')));
  v_moi   bigint := coalesce(p_app_affaire_id, -1);
  v_cible bigint;
  v_n     integer;
begin
  if p_annonce is null or v_kind = '' then
    return coalesce(p_app_affaire_id, nextval('app_chaine_id_seq'));
  end if;

  if v_kind = 'offre' then
    if v_acq is not null then
      with etat as (
        select app_chaine_id as ch,
               bool_or(kind = 'vente')     as a_vente,
               bool_or(kind = 'compromis') as a_compromis,
               bool_or(kind = 'compromis'
                       and lower(coalesce(state,'')) not in ('cancelled','annule')) as compromis_vivant,
               bool_or(kind = 'offre')     as a_offre,
               bool_or(kind = 'offre'
                       and lower(coalesce(state,'')) not in ('refused','refusee'))  as offre_vivante
          from app_affaire_ledger
         where hektor_annonce_id = p_annonce and app_chaine_id is not null
           and app_affaire_id <> v_moi
           -- 07/09 : ce que Hektor a efface ne pese plus dans l'etat de la chaine.
           and not (btrim(coalesce(hektor_affaire_id::text, '')) <> ''
                    and present_in_hektor is false)
         group by app_chaine_id
      )
      select min(e.ch) into v_cible
        from etat e
       where not e.a_vente
         and not e.a_compromis
         and (not e.a_offre or e.offre_vivante)
         and exists (select 1 from app_affaire_ledger l
                      where l.app_chaine_id = e.ch
                        and l.hektor_annonce_id = p_annonce
                        and l.app_affaire_id <> v_moi
                        and btrim(coalesce(l.hektor_acquereur_id,'')) = v_acq
                        -- 07/09 : idem pour le rattachement par acquereur.
                        and not (btrim(coalesce(l.hektor_affaire_id::text, '')) <> ''
                                 and l.present_in_hektor is false));
    end if;

  elsif v_kind = 'compromis' then
    with etat as (
      select app_chaine_id as ch,
             bool_or(kind = 'vente')     as a_vente,
             bool_or(kind = 'compromis') as a_compromis,
             bool_or(kind = 'compromis'
                     and lower(coalesce(state,'')) not in ('cancelled','annule')) as compromis_vivant,
             bool_or(kind = 'offre')     as a_offre,
             bool_or(kind = 'offre'
                     and lower(coalesce(state,'')) not in ('refused','refusee'))  as offre_vivante,
             bool_or(kind = 'offre'
                     and lower(coalesce(state,'')) in ('accepted','acceptee'))    as offre_acceptee
        from app_affaire_ledger
       where hektor_annonce_id = p_annonce and app_chaine_id is not null
         and app_affaire_id <> v_moi
         -- 07/09 : ce que Hektor a efface ne pese plus dans l'etat de la chaine.
         and not (btrim(coalesce(hektor_affaire_id::text, '')) <> ''
                  and present_in_hektor is false)
       group by app_chaine_id
    )
    select count(*), min(e.ch) into v_n, v_cible
      from etat e
     where not e.a_vente
       and not e.a_compromis
       and e.offre_acceptee
       and (not e.a_offre or e.offre_vivante);
    if v_n <> 1 then v_cible := null; end if;

  elsif v_kind = 'vente' then
    with etat as (
      select app_chaine_id as ch,
             bool_or(kind = 'vente')     as a_vente,
             bool_or(kind = 'compromis') as a_compromis,
             bool_or(kind = 'compromis'
                     and lower(coalesce(state,'')) not in ('cancelled','annule')) as compromis_vivant
        from app_affaire_ledger
       where hektor_annonce_id = p_annonce and app_chaine_id is not null
         and app_affaire_id <> v_moi
         -- 07/09 : LE CAS QUI MOTIVE TOUT CECI. Sans cette clause, une vente se
         -- rattacherait au compromis d'une chaine dont le compromis a ete EFFACE
         -- chez Hektor -- il compterait encore comme `compromis_vivant`.
         and not (btrim(coalesce(hektor_affaire_id::text, '')) <> ''
                  and present_in_hektor is false)
       group by app_chaine_id
    )
    select count(*), min(e.ch) into v_n, v_cible
      from etat e
     where not e.a_vente
       and e.a_compromis
       and e.compromis_vivant;
    if v_n <> 1 then v_cible := null; end if;
  end if;

  return coalesce(v_cible, p_app_affaire_id, nextval('app_chaine_id_seq'));
end;
$function$;
