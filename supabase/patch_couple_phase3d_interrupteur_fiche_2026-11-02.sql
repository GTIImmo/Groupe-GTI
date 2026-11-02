-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PHASE 3-D — L'INTERRUPTEUR DE LA FICHE                     02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER avec l'accord de Frédéric, APRES le push du front (Vercel en ligne).
-- Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §21.
--
-- `contacts_couples_fiche` (app_setting), trois crans : 'admin' = les admins seuls, 'on' = tout le monde,
-- absent ou autre = la fiche d'avant. Lu UNE fois par chargement de page : recharger après un changement.
-- Allumé, la fiche d'un couple (nature_fiche = 'couple', ou une seconde fiche « conjoint ») montre le foyer :
-- pastille « Couple », deux onglets qui pilotent les coordonnées (le conjoint en LECTURE SEULE), les biens
-- des deux sans doublon ; « Archiver » / « Supprimer » disent « (tout le foyer) ».
-- ⛔ Prérequis : la vue 3-B (posée le 02/11). ⛔ Avant tout retour arrière de 3-B : éteindre ici.
-- RETOUR ARRIÈRE : delete from app_setting where key = 'contacts_couples_fiche';
-- ═══════════════════════════════════════════════════════════════════════════

insert into public.app_setting (key, value, description, updated_at)
values ('contacts_couples_fiche', 'admin',
        'Couples, piece D (02/11/2026) : fiche d''un couple = le foyer, deux onglets. admin = admins seuls, on = tout le monde, absent = comme avant.',
        now())
on conflict (key) do update set value = excluded.value, description = excluded.description, updated_at = now();

-- CONTROLE
select key, value, updated_at from public.app_setting where key = 'contacts_couples_fiche';
