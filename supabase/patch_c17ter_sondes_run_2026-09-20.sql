-- ═══════════════════════════════════════════════════════════════════════════
-- C.17-ter — LES 13 ETAPES DU RUN QUI ECRIVAIENT DANS LE VIDE     20/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- MESURE DU JOUR : le run de nuit signale son passage avec 28 cles ; le registre
-- n'en connaissait que 15. heartbeat.py fait un PATCH : une cle absente n'ecrit
-- RIEN, et sans erreur. Treize etapes tournaient donc chaque nuit sans qu'aucune
-- surveillance ne puisse dire si elles avaient tourne.
--
-- ET CE NE SONT PAS DES ETAPES MINEURES. On y trouve le CONTRAT D'AUTORITE (ce
-- que l'app garde contre Hektor), le REGISTRE DES AFFAIRES, la PROPAGATION DES
-- NUMEROS DE CONTACT, le REGISTRE D'IDENTITE DES CONTACTS. Le 18/09, « entretien
-- ventes » a echoue a 06:58 : personne ne l'a su.
--
-- LE SEUIL VIENT DE LA FREQUENCE, pas d'un choix :
--    pipeline_step           28 h  -- etape bloquante : si elle saute, le run est mort
--    optional_pipeline_step  50 h  -- etape facultative : deux nuits muettes alertent
--
-- LA CRITICITE DECIDE DE LA SEVERITE de l'alerte : `critical` reveille, `medium`
-- avertit. On la reserve a ce dont la perte se voit le lendemain matin.
--
-- ⚠ status = 'active' PARTOUT, y compris pour les etapes facultatives :
--   check_worker_heartbeat SAUTE les lignes qui ne sont pas 'active'. Une etape
--   declaree 'active_optional' n'est jamais surveillee -- le piege qu'on vient de
--   trouver sur supabase.push_contacts.
--
-- RETOUR ARRIERE :
--   DELETE FROM public.app_worker_registry WHERE worker_key IN (les 13 ci-dessous);
-- ═══════════════════════════════════════════════════════════════════════════

insert into public.app_worker_registry (
    worker_key, worker_name, worker_role, worker_type, criticality, frequency,
    dependencies_json, status, owner, monitoring_domain, source_kind, source_notes,
    script_path, expected_max_runtime_minutes
) values
  ('phase1.backfill_mandats', 'Backfill mandats depuis mandats_json',
   'Reverse les mandats portes par les listings d''annonces dans le miroir.',
   'python_worker', 'medium', 'optional_pipeline_step', '["phase1.normalize_source"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09 : cle utilisee par le run, absente du registre.',
   'phase2/sync/backfill_hektor_mandats.py', 20),

  ('phase2.contrat_autorite', 'Contrat d''autorite',
   'Re-applique chaque nuit les champs dont l''APP est maitresse, apres la reconstruction depuis le miroir. C''est l''interrupteur du chantier d''independance.',
   'python_worker', 'critical', 'pipeline_step', '["phase2.refresh_views"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09. Etape bloquante : sans elle, Hektor gagne sur tout.',
   'phase2/identite/appliquer_contrat.py', 15),

  ('phase2.annonces_app_seule', 'Annonces connues de l''app seule',
   'Tient cote serveur les annonces que le miroir Hektor ignore (26bis).',
   'python_worker', 'medium', 'pipeline_step', '["phase2.refresh_views"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09.', 'phase2/identite/annonces_app_seule.py', 15),

  ('phase2.registre_contacts', 'Registre d''identite des contacts',
   'Maintient app_contact : un numero d''app par contact, jamais perdu (C.2b).',
   'python_worker', 'critical', 'pipeline_step', '["phase2.contacts_layer"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09. Si elle s''arrete, les contacts neufs naissent sans numero d''app.',
   'phase2/identite/registre_contacts.py', 15),

  ('phase2.perimetre_console', 'Perimetre des contacts cites par la console',
   'Fait monter vers l''app les personnes que Hektor nomme dans une transaction.',
   'python_worker', 'medium', 'pipeline_step', '["phase2.contacts_layer"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09.', 'phase2/contacts/elargir_perimetre_console.py', 15),

  ('phase2.redescente_console', 'Redescente des lectures console',
   'Fait redescendre dans le miroir ce que les assistants compromis / vente ont lu.',
   'python_worker', 'medium', 'optional_pipeline_step', '["console.entretien_compromis"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09.', 'phase2/sync/redescente_console.py', 20),

  ('phase2.registre_console', 'Registre depuis la console',
   'Fait entrer le miroir console dans le registre des affaires.',
   'python_worker', 'medium', 'optional_pipeline_step', '["phase2.redescente_console"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09.', 'phase2/sync/registre_depuis_console.py', 20),

  ('phase2.repartition_commission', 'Repartition de commission',
   'Entretient app_affaire_repartition -- une donnee qui n''existe QUE dans l''app depuis le 14/09.',
   'python_worker', 'medium', 'optional_pipeline_step', '["supabase.affaire_ledger"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09.', 'phase2/identite/convertir_repartition_commission.py', 20),

  ('supabase.affaire_ledger', 'Registre des affaires (refresh + push)',
   'Reconstruit et publie app_affaire_ledger : offres, compromis, ventes, et le montant des offres.',
   'python_worker', 'critical', 'pipeline_step', '["phase1.normalize_source"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09. Etape bloquante et centrale : les transactions de l''app en dependent.',
   'phase2/sync/affaire_ledger.py', 30),

  ('supabase.push_contact_ids', 'Pousser les numeros de contact',
   'Pose le numero d''app sur les contacts neufs dans Supabase (C.2b).',
   'python_worker', 'medium', 'pipeline_step', '["supabase.push_contacts"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09.', 'phase2/identite/pousser_numeros_contact.py', 15),

  ('supabase.propagate_contact_ids', 'Propager les numeros de contact',
   'Fait descendre le numero d''app jusqu''aux 18 tables satellites. Repare ~750 lignes par jour.',
   'python_worker', 'medium', 'optional_pipeline_step', '["supabase.push_contact_ids"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09. Sa sonde de resultat existait deja (data.contact_lignes_sans_numero) ; son battement de coeur, non.',
   'phase2/identite/propager_numeros_contact.py', 15),

  ('console.entretien_compromis', 'Entretien des compromis (console)',
   'Relit chez Hektor les compromis neufs ou modifies, par les assistants.',
   'node_worker', 'medium', 'optional_pipeline_step', '["phase1.sync_raw"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09. Parle a Hektor : son echec peut signaler un blocage d''IP.',
   'Console/entretien_compromis_console.js', 45),

  ('console.entretien_ventes', 'Entretien des ventes (console)',
   'Relit chez Hektor les ventes neuves ou modifiees, par les assistants.',
   'node_worker', 'medium', 'optional_pipeline_step', '["phase1.sync_raw"]'::jsonb,
   'active', 'frederic', 'business', 'static_analysis',
   'C.17-ter 20/09. A ECHOUE LE 18/09 A 06:58 SANS QUE PERSONNE LE SACHE -- c''est le cas qui a ouvert cette tache.',
   'Console/entretien_ventes_console.js', 45)

on conflict (worker_key) do update set
    worker_name = excluded.worker_name,
    worker_role = excluded.worker_role,
    criticality = excluded.criticality,
    frequency = excluded.frequency,
    status = excluded.status,
    monitoring_domain = excluded.monitoring_domain,
    source_notes = excluded.source_notes,
    script_path = excluded.script_path,
    expected_max_runtime_minutes = excluded.expected_max_runtime_minutes,
    updated_at = now();
