-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE E — L'INTERRUPTEUR « MODIFIER LE CONJOINT »          02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER avec l'accord de Frédéric, APRÈS : le push du front, le redémarrage des 4 services worker
-- (file vide : le correctif du groupe contactCoupleAll, 748383f) et la pose de
-- patch_couple_phase3e_conjoint_optimiste_2026-11-02.sql. Note : synthèse couples §28.
--
-- `contacts_couples_modif` (app_setting) : 'admin' = les admins seuls, 'on' = tout le monde, absent = la
-- fenêtre « Modifier la fiche » d'avant (sans la partie Conjoint). Lu une fois par chargement de page.
-- RETOUR ARRIÈRE : delete from app_setting where key = 'contacts_couples_modif';
-- ═══════════════════════════════════════════════════════════════════════════

insert into public.app_setting (key, value, description, updated_at)
values ('contacts_couples_modif', 'admin',
        'Couples, piece E (02/11/2026) : modifier le conjoint depuis la fiche principale. admin = admins seuls, on = tout le monde, absent = comme avant.',
        now())
on conflict (key) do update set value = excluded.value, description = excluded.description, updated_at = now();

select key, value, updated_at from public.app_setting where key = 'contacts_couples_modif';
