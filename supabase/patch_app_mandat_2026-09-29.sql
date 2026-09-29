-- ═══════════════════════════════════════════════════════════════════════════════
-- A.3-tech phase 1 -- app_mandat DANS SUPABASE
-- ═══════════════════════════════════════════════════════════════════════════════
-- 29/09/2026. A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Je ne l'execute pas : c'est une ecriture en base de production.
--
-- ─── POURQUOI CETTE TABLE ───────────────────────────────────────────────────────
-- `app_mandat_register_current` n'est pas un registre mais une VUE de travail :
-- effacee et refaite a chaque push, et filtree sur le statut de l'annonce. Une
-- annonce vendue ou archivee en sort, et rien ne l'y remet. Mesure du 29/09 :
-- 23 091 de ses 23 840 lignes etaient figees au 31/07, et 635 mandats de vente
-- lui manquaient -- dont 80 qui couraient encore.
--
-- `app_mandat` est le registre : une ligne par mandat, un numero a nous, et
-- RIEN N'EN SORT JAMAIS. La table locale existe depuis le 29/09 (26 822 lignes,
-- remplie par phase2/sync/mandat_ledger.py). Celle-ci en est la copie cote
-- Supabase -- celle que le front lira et que le worker ecrira.
--
-- ─── LA CLE : LE COUPLE (annonce, numero) ───────────────────────────────────────
-- Et surtout PAS hektor_mandat_id : Hektor range le MEME mandat sous plusieurs
-- identifiants internes -- annonce 1972, numero 17925, SIMPLE, memes dates, TROIS
-- ids (32312, 66487, 555). Prendre l'id compterait trois fois le meme mandat.
-- Le couple, lui, est unique : 24 939 sur 24 939 au 28/08, revalide le 29/09.
--
-- ─── LE PIEGE DES DEUX DISTRIBUTEURS, DEJA PAYE UNE FOIS ────────────────────────
-- Deux chemins distribuent des numeros dans la MEME serie :
--     le run local  « je prends le plus grand + 1 »  -- mais UNIQUEMENT sous 1 000 000
--     l'app         « je prends le suivant »         -- app_mandat_id_app_seq
-- C'est exactement le montage de l'affaire. Et c'est son ratage qui a coute cinq
-- jours en aout : le run regardait alors le MAX GLOBAL, a saute dans la plage de
-- l'app, et la sequence s'est mise a rendre des numeros DEJA PRIS -- plus aucune
-- creation d'offre, de compromis ni de vente ne passait, sous un message qui
-- parlait d'autre chose. mandat_ledger.py applique la regle corrigee des le
-- premier jour : `WHERE app_mandat_id < 1000000`.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- DROP TABLE public.app_mandat; DROP SEQUENCE public.app_mandat_id_app_seq;
-- Rien ne la lit encore : la supprimer ne casse rien.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.app_mandat (
    app_mandat_id        bigint PRIMARY KEY,
    app_dossier_id       bigint,
    hektor_annonce_id    text NOT NULL,
    numero_mandat        text NOT NULL,
    hektor_mandat_id     text,
    famille              text,
    type                 text,
    date_enregistrement  text,
    date_debut           text,
    date_fin             text,
    montant              text,
    mandants_texte       text,
    note                 text,
    payload_json         text,
    origine              text,
    offre_type           text,
    date_cloture         text,
    first_seen_at        text,
    last_seen_at         text,
    present_in_hektor    boolean NOT NULL DEFAULT true,
    CONSTRAINT app_mandat_couple_unique UNIQUE (hektor_annonce_id, numero_mandat)
);

CREATE INDEX IF NOT EXISTS idx_app_mandat_annonce  ON public.app_mandat (hektor_annonce_id);
CREATE INDEX IF NOT EXISTS idx_app_mandat_numero   ON public.app_mandat (numero_mandat);
CREATE INDEX IF NOT EXISTS idx_app_mandat_dossier  ON public.app_mandat (app_dossier_id);

-- La plage reservee aux mandats NES DANS L'APP. Meme valeur que l'affaire et la
-- recherche. Le run local ne la regarde jamais : il compte sous 1 000 000.
CREATE SEQUENCE IF NOT EXISTS public.app_mandat_id_app_seq
    START WITH 1000000 MINVALUE 1000000 INCREMENT BY 1;

ALTER TABLE public.app_mandat ENABLE ROW LEVEL SECURITY;

-- Meme politique que app_affaire_ledger : lecture pour les utilisateurs actifs.
-- Les ecritures passent par la cle de service (le run et le worker), qui
-- contourne RLS -- rien d'autre ne doit pouvoir ecrire ici.
DROP POLICY IF EXISTS app_mandat_select_active_users ON public.app_mandat;
CREATE POLICY app_mandat_select_active_users ON public.app_mandat
    FOR SELECT USING (is_app_user_active());

COMMENT ON TABLE public.app_mandat IS
  'A.3-tech phase 1 (29/09/2026) -- LE REGISTRE DES MANDATS. Une ligne par mandat, '
  'jamais supprimee (present_in_hektor passe a false, la ligne reste). Cle = le '
  'couple (hektor_annonce_id, numero_mandat) -- PAS hektor_mandat_id, que Hektor '
  'reutilise pour un meme mandat. Remplie par phase2/sync/mandat_ledger.py depuis '
  'le miroir, et par le worker a chaque mandat cree depuis l''app.';

COMMENT ON COLUMN public.app_mandat.app_mandat_id IS
  'NOTRE numero de mandat. Sous 1 000 000 : distribue par le run local. Au-dessus : '
  'app_mandat_id_app_seq, pour les mandats nes dans l''app. Les deux series ne se '
  'croisent JAMAIS -- c''est la regle qui a manque a l''affaire en aout.';

COMMENT ON COLUMN public.app_mandat.origine IS
  'D''ou vient la ligne : ''mandat'' (la fiche Hektor, complete) ou ''annonce'' (le '
  'seul numero porte par l''annonce, quand aucune fiche n''existe -- 2 072 cas le '
  '29/09). Un numero EMIS doit figurer au registre meme si sa fiche n''est jamais '
  'redescendue.';

COMMENT ON COLUMN public.app_mandat.offre_type IS
  'Le type d''offre de l''annonce. La table porte TOUT, locations comprises (« le '
  'serveur recoit tous les types ») ; c''est la VUE qui filtre sur 0/10/6. Sans '
  'cette colonne on annonce 2 983 pertes la ou il y en a 635.';

COMMENT ON COLUMN public.app_mandat.date_cloture IS
  'HORS de la mise a jour par le run : protection par omission. L''app possede ce '
  'champ (CHAMPS_APP_MANDAT) et le carnet app_mandat_champ_app le porte.';
