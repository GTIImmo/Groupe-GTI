"""Assemble la REPETITION du lot L2-B depuis les VRAIS fichiers de patch.

Meme principe que pour L4, L4-bis et L2-A (lecon du point 4d) : assemblee,
jamais recopiee.

Usage, depuis la racine du depot :
    python supabase/generer_repetition_l2b.py
"""

from pathlib import Path
import sys

ICI = Path(__file__).resolve().parent
PATCH = ICI / "patch_l2b_negociateur_documents_photos_2026-10-12.sql"
INVERSE = ICI / "patch_l2b_negociateur_documents_photos_2026-10-12_INVERSE.sql"
SORTIE = ICI / "patch_l2b_negociateur_documents_photos_2026-10-12_REPETITION.sql"

# Les 21 types que le commercial doit connaitre a la fin (7 + 5 de L2-A + 9 de L2-B)
TYPES_21 = [
    "prepare_document_cloud", "upload_document_to_hektor",
    "prepare_archived_annonce_detail", "prepare_historical_annonce_detail",
    "sync_console_documents", "relance_signature", "cancel_signature_procedure",
    "update_hektor_annonce_fields", "link_hektor_mandant", "unlink_hektor_mandant",
    "create_hektor_mandant_contact", "update_hektor_mandant_contact",
    "delete_document_from_hektor", "generate_estimation_pdf",
    "generate_mandat_document", "generate_cadastre_document",
    "upload_hektor_photo", "sync_hektor_photos", "matterport_action",
    "create_hektor_mandat_auto_number", "restore_hektor_annonce",
]


def corps_sans_transaction(chemin: Path) -> str:
    if not chemin.exists():
        sys.exit(f"ERREUR : fichier introuvable -> {chemin}")
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    gardees = [l for l in lignes if l.strip().lower() not in ("begin;", "commit;")]
    print(f"  {chemin.name} : {len(lignes)} lignes, {len(lignes) - len(gardees)} begin/commit retiree(s)")
    return "\n".join(gardees)


def bloc_mesures(etape: str) -> str:
    liste_t = ", ".join(f"'{t}'" for t in TYPES_21)
    return f"""
-- ---------- MESURES : {etape} ----------
insert into _l2b_mesures(etape, cle, valeur)
select '{etape}', 'corps__videur', md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

insert into _l2b_mesures(etape, cle, valeur)
select '{etape}', 'types_connus_du_commercial', count(*)::text
  from unnest(array[{liste_t}]) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l2b_mesures(etape, cle, valeur)
select '{etape}', 'statut_et_archivage_admin_seul',
       case when position('archive_hektor_annonce' in d.def) > 0
             and position('change_hektor_annonce_status' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

-- ⚠ le controle qui compte VRAIMENT : archive_hektor_annonce ne doit JAMAIS
--   entrer dans la liste du commercial (il n'existe que dans le cas particulier,
--   AVANT la liste). On regarde donc seulement la partie qui suit « commercial ».
insert into _l2b_mesures(etape, cle, valeur)
select '{etape}', 'archivage_entre_dans_la_liste_du_commercial',
       case when position('''archive_hektor_annonce''' in
                          substring(d.def from position('current_app_role = ''commercial''' in d.def))) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2b_mesures(etape, cle, valeur)
select '{etape}', 'controle_ses_biens_present',
       case when position('app_console_can_access_dossier' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2b_mesures(etape, cle, valeur)
select '{etape}', 'garde_du_prix_de_L2A_intact', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_edit_annonce_optimistic', 'app_console_create_update_annonce_job')
   and position('prix_sur_demande' in pg_get_functiondef(p.oid)) > 0;

insert into _l2b_mesures(etape, cle, valeur)
select '{etape}', 'videur_joignable_sans_compte',
       case when has_function_privilege('anon', p.oid, 'EXECUTE') then '*** OUI ***' else 'non' end
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'app_console_can_request_job';
"""


def main() -> None:
    print("Assemblage de la repetition L2-B, depuis les vrais fichiers :")
    patch = corps_sans_transaction(PATCH)
    inverse = corps_sans_transaction(INVERSE)

    entete = """-- ============================================================================
-- REPETITION DU LOT L2-B -- CE QUE LE NEGOCIATEUR FAIT SEUL (2/2)
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN :
--   ESSAI ANNULE -- RIEN N'A ETE ECRIT
--   LE VIDEUR NE REVIENT PAS A SON ETAT L2-A : 0   (0 attendu)
--   LE PATCH N'A RIEN CHANGE                 : 0   (0 attendu)
--
--   AVANT          types_connus_du_commercial                   = 12
--                  statut_et_archivage_admin_seul               = oui
--                  archivage_entre_dans_la_liste_du_commercial  = non
--                  controle_ses_biens_present                   = oui
--                  garde_du_prix_de_L2A_intact                  = 2
--                  videur_joignable_sans_compte                 = non
--
--   APRES_PATCH    types_connus_du_commercial                   = 21  <<< les 9 ouverts
--                  statut_et_archivage_admin_seul               = oui
--                  archivage_entre_dans_la_liste_du_commercial  = non  <<< LE PLUS IMPORTANT
--                  controle_ses_biens_present                   = oui
--                  garde_du_prix_de_L2A_intact                  = 2   <<< L2-A pas abime
--                  videur_joignable_sans_compte                 = non <<< chantier 1 intact
--
--   APRES_INVERSE  identique a AVANT
--
-- ⚠ POURQUOI LA LIGNE « archivage_entre_dans_la_liste_du_commercial » COMPTE
--   TANT : « archiver » et « desarchiver » se ressemblent, et l'un est ouvert
--   tandis que l'autre doit rester ferme. Si archive_hektor_annonce se retrouvait
--   dans la liste du commercial, un negociateur pourrait archiver n'importe lequel
--   de ses biens sans demander -- exactement ce que Frederic a refuse.
--
-- ⚠ CE QUE CETTE REPETITION NE PROUVE PAS : ce qu'un negociateur peut vraiment
--   faire. Cela se verifie en interrogeant le videur EN TANT QUE MELANIE, en
--   lecture seule, apres le collage (methode du lot L4).
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_l2b.py.
--   NE PAS LE MODIFIER A LA MAIN : modifier les patchs, puis relancer le generateur.
-- ============================================================================

begin;

create temporary table _l2b_mesures(
    ordre  serial,
    etape  text,
    cle    text,
    valeur text
) on commit drop;
"""

    final = """
-- ============================================================================
-- L'ERREUR VOLONTAIRE : elle annule les trois etapes et rend les mesures
-- ============================================================================
do $final$
declare
    v_txt text;
    v_pas_revenu int;
    v_pas_change int;
begin
    select count(*) into v_pas_revenu
      from _l2b_mesures a
      join _l2b_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and a.cle = 'corps__videur'
       and a.valeur is distinct from z.valeur;

    select count(*) into v_pas_change
      from _l2b_mesures a
      join _l2b_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and a.cle = 'corps__videur'
       and a.valeur = p.valeur;

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l2b_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\\'A ETE ECRIT.\\n\\nLE VIDEUR NE REVIENT PAS A SON ETAT L2-A : %   (0 attendu)\\nLE PATCH N\\'A RIEN CHANGE                 : %   (0 attendu)\\n\\n%\\n',
        v_pas_revenu, v_pas_change, v_txt;
end
$final$;

-- jamais atteint
rollback;
"""

    texte = "".join([
        entete,
        bloc_mesures("AVANT"),
        "\n\n-- ############ LE VRAI PATCH L2-B, CORPS EXACT ############\n",
        patch,
        "\n",
        bloc_mesures("APRES_PATCH"),
        "\n\n-- ############ LE VRAI INVERSE, CORPS EXACT ############\n",
        inverse,
        "\n",
        bloc_mesures("APRES_INVERSE"),
        final,
    ])

    donnees = texte.encode("utf-8")
    SORTIE.write_bytes(donnees)
    print(f"\nEcrit : {SORTIE}")
    print(f"  {len(texte.splitlines())} lignes, {len(donnees)} octets")


if __name__ == "__main__":
    main()
