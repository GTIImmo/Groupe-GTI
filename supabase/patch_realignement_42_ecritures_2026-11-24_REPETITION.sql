-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- patch_realignement_42_ecritures_2026-11-24 -- LES CONTROLES, REJOUABLES. AUCUNE ECRITURE.
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
select 'lignes au journal (42 gestes + 4 nommees)' as controle, count(*)::text as mesure, '46' as attendu
  from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24'
union all
select 'les 42 portent LEURS DEUX CLES (place + ligne d''origine)', count(*)::text, '42'
  from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24' and geste <> 'NOMMEE (laissee en place)'
   and de_app_chaine_id is not null and ligne_origine is not null and ligne_origine_num is not null
union all
select 'par geste : ' || geste, count(*)::text, case geste when 'DEPLACER' then '37' when 'METTRE DE COTE' then '5' else '4' end
  from public.app_classeur_realignement_journal where lot = 'realignement_42_2026-11-24' group by geste
union all
select 'notes sur leur cible (meme texte)', count(*)::text, '31'
  from public.app_classeur_realignement_journal j join public.app_affaire_note t on t.app_affaire_id = j.vers_app_affaire_id
 where j.lot = 'realignement_42_2026-11-24' and j.famille = 'note' and md5(t.texte) = j.note_md5
union all
select 'notes a un numero negatif', count(*)::text, '0' from public.app_affaire_note where app_affaire_id < 0
union all
select 'cibles du registre posees', count(*)::text, '6'
  from public.app_classeur_realignement_journal v join public.app_affaire_ledger x on x.app_affaire_id = v.vers_app_affaire_id
 where v.lot = 'realignement_42_2026-11-24' and v.famille <> 'note' and v.geste = 'DEPLACER' and case v.famille when 'date_annulation_app' then x.date_annulation_app when 'motif_annulation_app' then x.motif_annulation_app when 'honoraires_entree_app' then x.honoraires_entree_app when 'vente_reglee_app' then x.vente_reglee_app when 'numero_facture_app' then x.numero_facture_app end = v.valeur
union all
select 'sources du registre videes (dont 5 mises de cote)', count(*)::text, '11'
  from public.app_classeur_realignement_journal v join public.app_affaire_ledger x on x.app_affaire_id = v.de_app_affaire_id
 where v.lot = 'realignement_42_2026-11-24' and v.famille <> 'note' and v.geste in ('DEPLACER', 'METTRE DE COTE') and case v.famille when 'date_annulation_app' then x.date_annulation_app when 'motif_annulation_app' then x.motif_annulation_app when 'honoraires_entree_app' then x.honoraires_entree_app when 'vente_reglee_app' then x.vente_reglee_app when 'numero_facture_app' then x.numero_facture_app end is null
union all
select 'les sauvegardes datees existent (registre, notes)',
       ((to_regclass('public.app_affaire_ledger_avant_realignement_20261124') is not null)::int
        + (to_regclass('public.app_affaire_note_avant_realignement_20261124') is not null)::int)::text, '2'
union all
select 'empreinte des lignes touchees', (select md5(coalesce((select string_agg(concat_ws('|', l.app_affaire_id, l.vente_reglee_app, l.numero_facture_app,
         l.date_annulation_app, l.motif_annulation_app, l.honoraires_entree_app), ';' order by l.app_affaire_id)
    from public.app_affaire_ledger l where l.app_affaire_id in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), '') || '#' ||
  coalesce((select string_agg(concat_ws('|', n.app_affaire_id, n.origine, md5(n.texte), n.app_dossier_id, n.app_chaine_id,
         n.ecrit_par), ';' order by n.app_affaire_id)
    from public.app_affaire_note n where abs(n.app_affaire_id) in (177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, 6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, 17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, 26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813)), ''))), '072b3cb3afbf685ca10dfb3c0e590a07'
order by 1;
