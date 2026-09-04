-- ═══════════════════════════════════════════════════════════════════════════════
-- LA REGLE DE CHAINAGE PAR LA SEQUENCE -- cote Supabase          05/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Deploye le 05/09/2026 (migrations app_chaine_pour_regle_sequence,
-- app_chaine_pour_exclut_sa_propre_ligne, status_optimistic_utilise_regle_sequence).
-- Ce fichier est la COPIE VERSIONNEE de ce qui tourne : sans lui, la regle
-- n'existerait que dans la base.
--
-- ─── POURQUOI CETTE FONCTION EXISTE ALORS QUE LE LOCAL CALCULE DEJA TOUT ───
-- Le serveur local recalcule les 29 321 chaines a chaque run (recalculer_les_chaines,
-- phase2/sync/affaire_ledger.py). Celle-ci sert ENTRE DEUX RUNS : quand l'app cree
-- une transaction, l'ecran doit montrer le bon dossier tout de suite.
-- ⚠ LES DEUX DOIVENT DIRE LA MEME CHOSE. « Deux copies d'une formule divergent tot
--   ou tard » : toute correction ici doit etre reportee la-bas, et l'inverse.
--
-- ─── CE QU'ON N'A PAS FAIT, ET C'EST VOULU ───
-- app_chaine_pour(bigint, text) -- l'ANCIENNE regle, par (annonce, acquereur) --
-- reste en place, INTOUCHEE. Arite differente, donc aucun appel existant ne bascule
-- par surprise. Le projet sait ce que coute un RPC change sous les pieds de ses
-- appelants : Postgres refuse le renommage, PostgREST appelle par NOM, et un DROP
-- efface les GRANT.
--
-- ─── VERIFICATION FAITE AVANT DE BRANCHER (05/09, sur un tiers du parc) ───
--     compromis   97,8 %  (3 408 / 3 486)
--     vente       99,8 %  (2 493 / 2 498)
--     offre       99,7 %  (678 / 680) dans le seul cas qui peut arriver en vrai
-- ⚠ Les offres tombent a 18 % si on rejoue TOUT le passe -- artefact du rejeu, pas
--   de la regle : la chaine d'une vieille offre a parfois pour tete un compromis
--   enregistre plus tard mais numerote plus bas. Une fonction appelee en direct ne
--   peut pas le savoir, et n'en a pas besoin : la transaction qui arrive est
--   toujours la plus recente.

create or replace function public.app_chaine_pour(
  p_annonce        bigint,
  p_acquereur      text,
  p_kind           text,
  p_app_affaire_id bigint
) returns bigint
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_acq   text   := nullif(btrim(coalesce(p_acquereur, '')), '');
  v_kind  text   := lower(btrim(coalesce(p_kind, '')));
  -- ⚠ LA FONCTION NE DOIT PAS SE VOIR ELLE-MEME. En production la ligne n'existe
  -- pas encore, donc cela ne change rien ; mais sans cette exclusion la regle
  -- serait INVERIFIABLE sur les lignes deja en base -- une vente relue fermerait
  -- sa propre chaine et s'en excluerait (26 concordances sur 1 696, un chiffre qui
  -- ne mesurait que le defaut du test).
  v_moi   bigint := coalesce(p_app_affaire_id, -1);
  v_cible bigint;
  v_n     integer;
begin
  if p_annonce is null or v_kind = '' then
    return coalesce(p_app_affaire_id, nextval('app_chaine_id_seq'));
  end if;

  if v_kind = 'offre' then
    -- une chaine par acquereur ; plusieurs offres coexistent, c'est NORMAL
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
                        and btrim(coalesce(l.hektor_acquereur_id,'')) = v_acq);
    end if;

  elsif v_kind = 'compromis' then
    -- L'UNIQUE offre acceptee encore ouverte. Zero ou plusieurs : ON NE DEVINE PAS,
    -- le compromis ouvre sa propre chaine (87,0 % de rattachement mesure).
    with etat as (
      select app_chaine_id as ch,
             bool_or(kind = 'vente')     as a_vente,
             bool_or(kind = 'compromis') as a_compromis,
             bool_or(kind = 'offre')     as a_offre,
             bool_or(kind = 'offre'
                     and lower(coalesce(state,'')) not in ('refused','refusee'))  as offre_vivante,
             bool_or(kind = 'offre'
                     and lower(coalesce(state,'')) in ('accepted','acceptee'))    as offre_acceptee
        from app_affaire_ledger
       where hektor_annonce_id = p_annonce and app_chaine_id is not null
         and app_affaire_id <> v_moi
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
    -- L'UNIQUE compromis encore ouvert (98,6 % de rattachement mesure).
    with etat as (
      select app_chaine_id as ch,
             bool_or(kind = 'vente')     as a_vente,
             bool_or(kind = 'compromis') as a_compromis,
             bool_or(kind = 'compromis'
                     and lower(coalesce(state,'')) not in ('cancelled','annule')) as compromis_vivant
        from app_affaire_ledger
       where hektor_annonce_id = p_annonce and app_chaine_id is not null
         and app_affaire_id <> v_moi
       group by app_chaine_id
    )
    select count(*), min(e.ch) into v_n, v_cible
      from etat e
     where not e.a_vente and e.a_compromis and e.compromis_vivant;
    if v_n <> 1 then v_cible := null; end if;
  end if;

  -- ⚠ LE NUMERO D'UNE NOUVELLE CHAINE = l'app_affaire_id de la transaction qui
  -- l'ouvre. C'est ce qui evite la divergence avec le local, qui numerote par
  -- min(app_affaire_id) des membres. L'ancienne version tirait un nextval : un
  -- numero que le run de nuit ECRASAIT, donc un dossier qui changeait de numero
  -- sous les yeux de l'utilisateur.
  return coalesce(v_cible, p_app_affaire_id, nextval('app_chaine_id_seq'));
end;
$function$;

comment on function public.app_chaine_pour(bigint, text, text, bigint) is
  'Regle de chainage par la SEQUENCE (1.7, 05/09/2026). Doit rester identique a '
  'recalculer_les_chaines() dans phase2/sync/affaire_ledger.py.';

comment on function public.app_chaine_pour(bigint, text) is
  'ANCIENNE regle (annonce + acquereur), remplacee le 05/09/2026 par la version a '
  '4 arguments. Conservee telle quelle : ne plus l''utiliser pour de nouveaux appels.';

grant execute on function public.app_chaine_pour(bigint, text, text, bigint)
  to anon, authenticated, service_role;

-- ─── L'APPELANT ───
-- app_change_annonce_status_optimistic a ete redeployee A L'IDENTIQUE a une ligne
-- pres (meme signature, donc GRANT conserves) :
--     AVANT  public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur)
--     APRES  public.app_chaine_pour(d.hektor_annonce_id::bigint, v_acquereur,
--                                   v_kind, v_affaire_id)
-- Sa definition complete reste celle de la base ; on ne la recopie pas ici pour ne
-- pas entretenir deux versions d'une fonction de 130 lignes.

-- ─── LA COLONNE DES ACQUEREURS (1.8) ───
alter table public.app_affaire_ledger
  add column if not exists acquereurs_json jsonb;
comment on column public.app_affaire_ledger.acquereurs_json is
  'Liste COMPLETE des acquereurs de la transaction (1.8, 05/09/2026). '
  'acquereur_json ne portait que le premier : 4 536 personnes presentes chez '
  'Hektor etaient invisibles dans le registre.';
