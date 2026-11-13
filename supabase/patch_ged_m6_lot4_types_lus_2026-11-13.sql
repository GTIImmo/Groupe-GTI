-- GED morceau 6, lot 4 (13/11/2026) -- l'amiante, le plomb, les termites et le règlement de copropriété deviennent des
-- types LUS (« avec », 13/11, §12.16). Le catalogue les avait rangés « classer » (lus plus tard) ; la colonne n'est
-- qu'une étiquette (seul « jamais_envoye » change un comportement, DepotDocuments.tsx) : on l'aligne pour que la base
-- dise la vérité. Les 10 autres types du lot 4 sont déjà « lue ».
-- Retour arrière : patch_ged_m6_lot4_types_lus_2026-11-13_INVERSE.sql
begin;

do $$
begin
  if (select count(*) from public.app_ged_type
      where code in ('diag.amiante', 'diag.plomb', 'diag.termites', 'copro.reglement') and lecture = 'classer') <> 4 then
    raise exception 'les 4 types ne sont pas tous « classer » : quelqu''un est passé avant, on s''arrête';
  end if;
end $$;

update public.app_ged_type set lecture = 'lue'
 where code in ('diag.amiante', 'diag.plomb', 'diag.termites', 'copro.reglement') and lecture = 'classer';

do $$
begin
  if (select count(*) from public.app_ged_type
      where code in ('diag.amiante', 'diag.plomb', 'diag.termites', 'copro.reglement') and lecture = 'lue') <> 4 then
    raise exception 'contrôle : les 4 types ne sont pas « lue »';
  end if;
  if (select count(*) from public.app_ged_type
      where code in ('mandat.vente', 'mandat.avenant', 'mandat.fin', 'transaction.acte', 'transaction.annulation',
                     'facture.honoraires', 'diag.electricite', 'diag.gaz', 'diag.assainissement', 'diag.surface')
        and lecture = 'lue') <> 10 then
    raise exception 'contrôle : un des 10 autres types du lot 4 n''est pas « lue »';
  end if;
end $$;

commit;
