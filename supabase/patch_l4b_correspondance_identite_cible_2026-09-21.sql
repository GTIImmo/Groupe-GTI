-- ═══════════════════════════════════════════════════════════════════════════
-- L4-b (②) — LA CORRESPONDANCE IDENTITE ↔ CIBLE, LISIBLE PAR LE SERVEUR
--                                                                21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- CE QUE L'ESSAI REEL DU 21/09 A MONTRE. Le premier contact ne dans l'app a
-- fini en DEUX fiches :
--
--      10000001   ESSAI L4B   cible 605450   <- la fiche de l'app
--        605450   ESSAI L4B   cible 605450   <- posee par le retour du worker
--
-- Le retour de synchronisation fait pourtant son travail normal : il lit la
-- fiche 605450 dans le miroir et la pousse. RIEN ne lui dit que 605450 EST
-- 10 000 001. La correspondance existe -- c'est la case cible, posee par le
-- worker juste apres la creation -- mais elle vit dans Supabase, et le serveur
-- ne la lit nulle part : `hektor_target_id` n'apparait dans AUCUN fichier de
-- phase2/ (mesure du 21/09).
--
-- CE QUE CE PATCH FAIT, ET RIEN DE PLUS : il expose cette correspondance dans
-- une vue que le serveur peut redescendre. Il ne cree pas de table, ne modifie
-- aucune ligne, et ne change le comportement de personne tant que l'etape de
-- descente n'est pas branchee dans le run.
--
-- ⚠ POURQUOI UNE VUE ET PAS UN FILTRE DANS LE CLIENT. L'identite est une
--   colonne TEXTE. Un `hektor_contact_id=gte.10000000` compare donc
--   LEXICOGRAPHIQUEMENT -- et '605450' > '10000000' en lexicographie, ce qui
--   ramenerait la moitie du parc. La comparaison doit se faire en nombre, donc
--   dans Postgres.
--
-- AU 21/09 ELLE REMONTE 2 LIGNES : les deux contacts d'essai. Pour les 356 000
-- autres, identite = numero Hektor, il n'y a rien a traduire.
--
-- RETOUR ARRIERE : drop view public.app_v_correspondance_identite_cible;
-- ═══════════════════════════════════════════════════════════════════════════

create or replace view public.app_v_correspondance_identite_cible as
  select hektor_contact_id as app_identite,
         hektor_target_id  as hektor_contact_id,
         nom,
         prenom,
         refreshed_at
    from public.app_contact_current
   where hektor_target_id is not null
     and hektor_target_id <> hektor_contact_id
     and hektor_contact_id ~ '^[0-9]+$'
     and hektor_contact_id::bigint >= 10000000;

comment on view public.app_v_correspondance_identite_cible is
  'L4-b 21/09/2026 : pour chaque contact NE DANS L''APP, son identite (>= 10 000 000) et le numero que Hektor lui a donne. Le serveur la redescend AVANT de construire sa couche contacts, pour ranger la fiche, ses recherches et ses relations sous l''identite au lieu d''en creer une seconde. Vide tant qu''aucun contact ne nait dans l''app.';

grant select on public.app_v_correspondance_identite_cible to service_role, authenticated;

-- ── LA SONDE : UNE PERSONNE, UNE FICHE ─────────────────────────────────────
-- Elle ne surveille pas la correspondance, elle surveille son ECHEC : une fiche
-- rangee sous un numero de Hektor alors qu'une identite d'app vise deja ce
-- numero. C'est EXACTEMENT le defaut du 21/09, et il etait invisible.
create or replace view public.app_v_contacts_en_double_identite as
  select c.hektor_contact_id as fiche_en_trop,
         m.app_identite,
         c.nom,
         c.prenom,
         c.refreshed_at
    from public.app_contact_current c
    join public.app_v_correspondance_identite_cible m
      on m.hektor_contact_id = c.hektor_contact_id;

comment on view public.app_v_contacts_en_double_identite is
  'L4-b 21/09/2026 : fiches rangees sous un numero Hektor alors qu''une identite d''app vise deja ce numero -- donc DEUX fiches pour une personne. Seuil de la sonde data.contacts_double_identite : 0.';

grant select on public.app_v_contacts_en_double_identite to service_role, authenticated;
