-- ============================================================================
-- RETOUR ARRIERE DU LOT L2-A
-- Inverse exact de patch_l2a_negociateur_champs_mandants_2026-10-12.sql
--
-- Il fait l'operation CONTRAIRE : il RETIRE le texte insere, en reconstruisant
-- mot pour mot le meme texte que le patch, puis il VERIFIE que les trois corps
-- retombent EXACTEMENT sur leurs empreintes d'origine du 12/10.
--
-- ⭐ C'est ce controle final qui le rend sur : si le texte retire n'etait pas
--    exactement celui insere, le remplacement ne change rien, l'empreinte ne
--    correspond pas, et le script S'ARRETE sans rien laisser a moitie defait.
-- ============================================================================

begin;

-- ----------------------------------------------------------------------------
-- 1. LE VIDEUR : les 5 types quittent la liste du commercial
-- ----------------------------------------------------------------------------
do $fermer$
declare
    v_def text;
    v_ancre text := '''cancel_signature_procedure''';
    v_ajout text;
begin
    v_ajout := v_ancre || ','
        || chr(10) || '            ''update_hektor_annonce_fields'',''link_hektor_mandant'',''unlink_hektor_mandant'','
        || chr(10) || '            ''create_hektor_mandant_contact'',''update_hektor_mandant_contact''';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    if position('update_hektor_annonce_fields' in v_def) = 0 then
        raise notice 'VIDEUR : rien a retirer, les 5 types ne sont pas la.';
    else
        execute replace(v_def, v_ajout, v_ancre);
        raise notice 'VIDEUR : les 5 types sont retires (12 -> 7).';
    end if;
end
$fermer$;


-- ----------------------------------------------------------------------------
-- 2. LE GARDE DU PRIX, chemin de la saisie
-- ----------------------------------------------------------------------------
do $prix1$
declare
    v_def text;
    v_ancre text := 'raise exception ''invalid_price'' using errcode=''22023''; end if;';
    v_ajout text;
begin
    v_ajout := v_ancre
        || chr(10) || '-- L2-A (12/10/2026) : le PRIX reste sous demande pour un negociateur'
        || chr(10) || '-- (decision B1 de Frederic). Il passe par « Demande de baisse de prix ».'
        || chr(10) || 'if v_price is not null and public.app_console_current_role() = ''commercial'' then'
        || chr(10) || 'raise exception ''prix_sur_demande'' using errcode=''42501''; end if;';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_edit_annonce_optimistic';

    if position('prix_sur_demande' in v_def) = 0 then
        raise notice 'SAISIE : rien a retirer.';
    else
        execute replace(v_def, v_ajout, v_ancre);
        raise notice 'SAISIE : le garde du prix est retire.';
    end if;
end
$prix1$;


-- ----------------------------------------------------------------------------
-- 3. LE GARDE DU PRIX, second chemin
-- ----------------------------------------------------------------------------
do $prix2$
declare
    v_def text;
    v_ancre text := 'raise exception ''forbidden_update_annonce'' using errcode = ''42501'';';
    v_ajout text;
begin
    v_ajout := v_ancre
        || chr(10) || '    end if;'
        || chr(10) || ''
        || chr(10) || '    -- L2-A (12/10/2026) : meme garde du prix que dans la saisie optimiste.'
        || chr(10) || '    if public.app_console_current_role() = ''commercial'''
        || chr(10) || '       and coalesce(nullif(trim(update_fields->>''price''), ''''),'
        || chr(10) || '                    nullif(trim(update_fields->>''prix''), ''''),'
        || chr(10) || '                    nullif(trim(update_fields->>''ESTIMATION_MONTANT''), '''')) is not null then'
        || chr(10) || '        raise exception ''prix_sur_demande'' using errcode = ''42501'';';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_create_update_annonce_job';

    if position('prix_sur_demande' in v_def) = 0 then
        raise notice 'SECOND CHEMIN : rien a retirer.';
    else
        execute replace(v_def, v_ajout, v_ancre);
        raise notice 'SECOND CHEMIN : le garde du prix est retire.';
    end if;
end
$prix2$;


-- ----------------------------------------------------------------------------
-- 4. CONTROLE : les 3 corps retombent-ils sur leurs empreintes d'origine ?
-- ----------------------------------------------------------------------------
do $controle$
declare
    v_attendu jsonb := jsonb_build_object(
        'app_console_can_request_job',           '7143dda690cf82c8c4e65210aa40f483',
        'app_edit_annonce_optimistic',           '45110168d91358c7790032b5085e1314',
        'app_console_create_update_annonce_job', 'cc039ade1eca389ecde206ec5df54b21'
    );
    v_nom text;
    v_trouve text;
    v_ecarts int := 0;
begin
    for v_nom in select jsonb_object_keys(v_attendu) loop
        select md5(replace(pg_get_functiondef(p.oid), chr(13), '')) into v_trouve
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = v_nom
         limit 1;
        if v_trouve is distinct from (v_attendu ->> v_nom) then
            v_ecarts := v_ecarts + 1;
            raise notice 'ECART sur % : trouve %, attendu %', v_nom, v_trouve, (v_attendu ->> v_nom);
        end if;
    end loop;

    if v_ecarts > 0 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % fonction(s) ne retombent pas sur leur corps d''origine.', v_ecarts;
    end if;

    raise notice 'RETOUR ARRIERE COMPLET : les 3 fonctions sont revenues a leur corps du 12/10, a l''empreinte.';
end
$controle$;

commit;
