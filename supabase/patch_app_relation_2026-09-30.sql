-- ═══════════════════════════════════════════════════════════════════════════════
-- LE REGISTRE DES LIENS DANS SUPABASE -- app_relation             30/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL. Je ne l'execute pas : c'est une
-- ecriture en base de production.
--
-- ─── POURQUOI CETTE TABLE ───────────────────────────────────────────────────────
-- `app_contact_relation_current` n'est pas un registre : elle est EFFACEE ET
-- REFAITE chaque nuit depuis six fenetres de Hektor, et le push ne monte que les
-- biens du parc. Un bien qui se vend emporte donc ses liens hors du cloud.
--
--    le cloud porte aujourd'hui     50 236 liens mandant / proprietaire
--    le serveur en connait         132 622
--                                  ────────
--    ce qu'un bien vendu emportait  82 386 liens
--
-- 82 386 fois, le jour ou un bien s'est vendu, on a cesse de savoir qui en etait
-- le mandant. `app_relation` est le registre : une ligne par lien, et RIEN N'EN
-- SORT JAMAIS (present_in_hektor passe a false, la ligne reste).
--
-- ─── TOUT MONTE -- DECISION DE FREDERIC, 30/09 ──────────────────────────────────
-- « Il faut tout monter pour avoir le registre des liens entier. »
-- C'est le montage du mandat, decide le matin meme : LE REGISTRE PORTE TOUT, LES
-- ECRANS FILTRENT. La regle « serveur = tout / cloud = biens vivants » vaut pour
-- les FICHIERS (documents, photos, qui pesent des gigaoctets), pas pour un
-- registre. Cout mesure : ~1 346 octets par ligne, soit ~116 Mo de plus.
--
-- ─── CE QU'ELLE PORTE, ET CE QU'ELLE NE PORTE PAS ───────────────────────────────
--    mandant + proprietaire   132 622   ELLE LES PORTE
--    acquereur (3 types)       34 925   ELLE NE LES PORTE PAS
-- Un acquereur n'est pas un lien au bien : il existe PARCE QU'IL A FAIT UNE
-- OFFRE, et `app_affaire_ledger` le tient deja durablement et a deux robinets
-- (30 352 affaires portent app_contact_id, toutes dans la plage de l'app). Le
-- registre les PROJETTERA. Deux copies finissent toujours par dire deux choses --
-- c'est exactement ce qui est arrive au registre des mandats, qui a menti deux
-- mois.
--
-- ─── LE FAIT BRUT, PAS LE LIBELLE ───────────────────────────────────────────────
-- Hektor ne connait qu'UN fait : « proprietaire du bien ». `mandant` et
-- `proprietaire` sont deux affichages du meme fait, choisis selon que l'annonce
-- porte un numero de mandat.
-- ⭐ MESURE : sur 132 622 couples (contact, bien), ZERO ne porte les deux roles.
--    74 166 + 58 456 = 132 622 = le nombre de couples distincts. AUCUN doublon.
--
-- ─── LA CLE, ET SA LIMITE, DITE FRANCHEMENT ─────────────────────────────────────
--    UNIQUE (app_contact_id, hektor_annonce_id)
-- app_contact_id est rempli a 100 % et hektor_annonce_id est toujours la, puisque
-- tout lien nait chez Hektor jusqu'a la coupure. NOTRE numero de bien
-- (app_dossier_id) est porte a cote, comme identite -- meme montage que app_mandat.
-- ⚠ LE JOUR OU L'APP CREERA UN LIEN SUR UNE ANNONCE NEE DANS L'APP, il n'y aura
--   pas de hektor_annonce_id : il faudra alors basculer la cle sur
--   (app_contact_id, app_dossier_id). Ce sera le premier geste de l'etape
--   « le worker ecrit ». C'est ecrit ici pour ne pas le redecouvrir.
--
-- ─── LE PIEGE DES DEUX DISTRIBUTEURS, DEJA PAYE UNE FOIS ────────────────────────
--    sous 1 000 000  le run local, « le plus grand SOUS LA PLAGE + 1 »
--    au-dessus       app_relation_id_app_seq, pour les liens nes dans l'app
-- Le ratage de cette regle a coute cinq jours en aout cote affaires : le run
-- regardait le MAX GLOBAL, sautait dans la plage de l'app, et la sequence rendait
-- des numeros DEJA PRIS.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- DROP TABLE public.app_relation; DROP SEQUENCE public.app_relation_id_app_seq;
-- Rien ne la lit encore : la supprimer ne casse rien.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.app_relation (
    app_relation_id      bigint PRIMARY KEY,
    app_contact_id       bigint NOT NULL,
    app_dossier_id       bigint,
    hektor_annonce_id    text NOT NULL,
    fait                 text NOT NULL DEFAULT 'proprietaire_du_bien',
    role_hektor          text,
    source               text,
    relation_key         text,
    first_seen_at        text,
    last_seen_at         text,
    present_in_hektor    boolean NOT NULL DEFAULT true,
    absent_depuis        text,
    CONSTRAINT app_relation_couple_unique UNIQUE (app_contact_id, hektor_annonce_id)
);

-- L'ecran cherchera « les liens de CE contact » et « les liens de CE bien ».
CREATE INDEX IF NOT EXISTS idx_app_relation_contact ON public.app_relation (app_contact_id);
CREATE INDEX IF NOT EXISTS idx_app_relation_dossier ON public.app_relation (app_dossier_id);
CREATE INDEX IF NOT EXISTS idx_app_relation_annonce ON public.app_relation (hektor_annonce_id);

-- La plage reservee aux liens NES DANS L'APP. Meme valeur que le mandat,
-- l'affaire et le dossier. Le run local ne la regarde jamais.
CREATE SEQUENCE IF NOT EXISTS public.app_relation_id_app_seq
    START WITH 1000000 MINVALUE 1000000 INCREMENT BY 1;

ALTER TABLE public.app_relation ENABLE ROW LEVEL SECURITY;

-- Meme politique que app_mandat et app_affaire_ledger : lecture pour les
-- utilisateurs actifs. Les ecritures passent par la cle de service (le run et le
-- worker), qui contourne RLS -- rien d'autre ne doit pouvoir ecrire ici.
DROP POLICY IF EXISTS app_relation_select_active_users ON public.app_relation;
CREATE POLICY app_relation_select_active_users ON public.app_relation
    FOR SELECT USING (is_app_user_active());

COMMENT ON TABLE public.app_relation IS
  'LE REGISTRE DES LIENS personne <-> bien (30/09/2026). Une ligne par lien, '
  'jamais supprimee (present_in_hektor passe a false, la ligne reste). Porte '
  'mandant et proprietaire ; les acquereurs sont PROJETES depuis '
  'app_affaire_ledger, jamais recopies. Remplie par phase2/sync/relation_ledger.py.';

COMMENT ON COLUMN public.app_relation.fait IS
  'LE FAIT BRUT : « proprietaire du bien », le seul que Hektor connaisse. '
  '« mandant » et « proprietaire » sont deux AFFICHAGES de ce fait, derives selon '
  'que l''annonce porte un numero de mandat. Stocker le libelle ferait changer '
  'l''identite du lien a chaque mandat signe.';

COMMENT ON COLUMN public.app_relation.role_hektor IS
  'Ce que Hektor en disait au dernier passage. INFORMATION, jamais identite.';

COMMENT ON COLUMN public.app_relation.app_relation_id IS
  'NOTRE numero de lien. Sous 1 000 000 : distribue par le run local, qui ne '
  'regarde JAMAIS le MAX global. Au-dessus : app_relation_id_app_seq. Les deux '
  'series ne se croisent jamais -- c''est la regle qui a manque a l''affaire en aout.';

COMMENT ON COLUMN public.app_relation.relation_key IS
  'Le hache historique (stable_hash de contact/bien/role/source/transaction), garde '
  'EN DOUBLURE le temps de la transition : c''est lui que le carnet C.9-d connait. '
  'Il n''est PAS la cle de cette table -- un hache change quand un ingredient change, '
  'et le role, lui, change.';
