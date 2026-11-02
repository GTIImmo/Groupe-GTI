-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PHASE 3-C — L'INTERRUPTEUR DE L'ANNUAIRE                   02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER avec l'accord de Frédéric, APRES le push du front (Vercel en ligne).
-- Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §18.
--
-- `contacts_couples_ecran` (app_setting), trois crans, même patron que `registre_transactions_ecran` :
--   'admin' = les admins seuls voient l'annuaire des couples (pour l'éprouver sur les vraies données) ;
--   'on'    = tout le monde ;
--   absent ou autre = l'annuaire d'avant (aucune nouvelle colonne lue).
-- Allumé, l'annuaire SEUL : lit nature_fiche / couple_json, masque les lignes « conjoint » et les
-- cases vides d'un couple (4 483 lignes actives au 02/11), montre « Couple · prénoms ».
-- ⛔ Prérequis : la vue 3-B (posée le 02/11 ~08:55). ⛔ Avant tout retour arrière de 3-B : éteindre ici.
-- RETOUR ARRIÈRE : delete from app_setting where key = 'contacts_couples_ecran';  (effet au prochain chargement)
-- ═══════════════════════════════════════════════════════════════════════════

insert into public.app_setting (key, value, description, updated_at)
values ('contacts_couples_ecran', 'admin',
        'Couples, piece C (02/11/2026) : annuaire un couple = une ligne. admin = admins seuls, on = tout le monde, absent = comme avant.',
        now())
on conflict (key) do update set value = excluded.value, description = excluded.description, updated_at = now();

-- CONTROLE
select key, value, updated_at from public.app_setting where key = 'contacts_couples_ecran';
