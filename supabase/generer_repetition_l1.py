"""Assemble la REPETITION du lot L1 depuis les VRAIS fichiers de patch.

Meme principe que pour L4, L4-bis, L2-A et L2-B (lecon du point 4d).

Usage, depuis la racine du depot :
    python supabase/generer_repetition_l1.py
"""

from pathlib import Path
import sys

ICI = Path(__file__).resolve().parent
PATCH = ICI / "patch_l1_manager_et_rappro_2026-10-12.sql"
INVERSE = ICI / "patch_l1_manager_et_rappro_2026-10-12_INVERSE.sql"
SORTIE = ICI / "patch_l1_manager_et_rappro_2026-10-12_REPETITION.sql"

AFFAIRES = [
    "app_affaire_note_ecrire", "app_affaire_personne_ecart_fermer",
    "app_conditions_affaire_ecrire", "app_edit_affaire_optimistic",
    "app_geste_affaire_optimistic", "app_modifier_affaire_optimistic",
]
RAPPRO = ["app_rapprochement", "app_rapprochement_score_history", "app_relance_rapprochement"]
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
    liste_a = ", ".join(f"'{f}'" for f in AFFAIRES)
    liste_r = ", ".join(f"'{t}'" for t in RAPPRO)
    liste_t = ", ".join(f"'{t}'" for t in TYPES_21)
    return f"""
-- ---------- MESURES : {etape} ----------
insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'corps__' || p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ({liste_a}, 'app_console_can_request_job');

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'fonctions_affaire_ouvertes_au_manager', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ({liste_a})
   and position('is_app_manager_or_admin()' in pg_get_functiondef(p.oid)) > 0;

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'is_app_admin_existe_toujours',
       case when exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                          where n.nspname = 'public' and p.proname = 'is_app_admin')
            then 'oui' else '*** NON ***' end;

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'statut_et_archivage_ouverts_au_manager',
       case when position('current_app_role in (''admin'', ''manager'')' in d.def) > 0
            then 'oui' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'types_du_commercial_intacts', count(*)::text
  from unnest(array[{liste_t}]) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'archivage_entre_dans_la_liste_du_commercial',
       case when position('''archive_hektor_annonce''' in
                          substring(d.def from position('current_app_role = ''commercial''' in d.def))) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job' limit 1) d;

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'regles_rapprochement_qui_suivent_le_perimetre', count(*)::text
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ({liste_r})
   and coalesce(qual, '') like '%app_perimetre_courant%';

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'rapprochements_lisibles_sans_compte', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname in ({liste_r})
   and has_table_privilege('anon', c.oid, 'SELECT');

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'comptes_manager', count(*)::text
  from public.app_user_profile where role::text = 'manager';

insert into _l1_mesures(etape, cle, valeur)
select '{etape}', 'comptes_hors_reseau', count(*)::text
  from public.app_user_profile p
 where coalesce(to_jsonb(p) ->> 'perimetre', 'reseau') <> 'reseau';
"""


def main() -> None:
    print("Assemblage de la repetition L1, depuis les vrais fichiers :")
    patch = corps_sans_transaction(PATCH)
    inverse = corps_sans_transaction(INVERSE)

    entete = """-- ============================================================================
-- REPETITION DU LOT L1 -- « manager = admin » + les rapprochements
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN :
--   ESSAI ANNULE -- RIEN N'A ETE ECRIT
--   CORPS QUI NE REVIENNENT PAS A L'ORIGINE : 0   (0 attendu)
--   CORPS QUE LE PATCH N'A PAS CHANGES      : 0   (0 attendu)
--
--   AVANT          fonctions_affaire_ouvertes_au_manager          = 0
--                  statut_et_archivage_ouverts_au_manager         = non
--                  regles_rapprochement_qui_suivent_le_perimetre  = 0
--                  types_du_commercial_intacts                    = 21
--                  archivage_entre_dans_la_liste_du_commercial    = non
--                  is_app_admin_existe_toujours                   = oui
--                  rapprochements_lisibles_sans_compte            = 0
--
--   APRES_PATCH    fonctions_affaire_ouvertes_au_manager          = 6
--                  statut_et_archivage_ouverts_au_manager         = oui
--                  regles_rapprochement_qui_suivent_le_perimetre  = 3
--                  types_du_commercial_intacts                    = 21  <<< PAS TOUCHES
--                  archivage_entre_dans_la_liste_du_commercial    = non <<< TOUJOURS
--                  is_app_admin_existe_toujours                   = oui <<< CONSERVEE
--                  rapprochements_lisibles_sans_compte            = 0   <<< chantier 1
--
--   APRES_INVERSE  identique a AVANT
--
-- ⚠ POURQUOI « is_app_admin_existe_toujours » COMPTE : cette fonction sert AUSSI
--   a la regle de lecture des profils. On ne la modifie pas -- on remplace
--   seulement son APPEL dans les 6 fonctions « affaire ».
--
-- ⚠ AU COLLAGE, RIEN NE CHANGE POUR PERSONNE : comptes_manager = 0 et
--   comptes_hors_reseau = 0. Le mecanisme est pose, eteint.
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_l1.py.
--   NE PAS LE MODIFIER A LA MAIN : modifier les patchs, puis relancer le generateur.
-- ============================================================================

begin;

create temporary table _l1_mesures(
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
    v_pas_revenus int;
    v_pas_changes int;
begin
    select count(*) into v_pas_revenus
      from _l1_mesures a
      join _l1_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'corps__')
       and a.valeur is distinct from z.valeur;

    select count(*) into v_pas_changes
      from _l1_mesures a
      join _l1_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and starts_with(a.cle, 'corps__')
       and a.valeur = p.valeur;

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l1_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\\'A ETE ECRIT.\\n\\nCORPS QUI NE REVIENNENT PAS A L\\'ORIGINE : %   (0 attendu)\\nCORPS QUE LE PATCH N\\'A PAS CHANGES      : %   (0 attendu)\\n\\n%\\n',
        v_pas_revenus, v_pas_changes, v_txt;
end
$final$;

-- jamais atteint
rollback;
"""

    texte = "".join([
        entete,
        bloc_mesures("AVANT"),
        "\n\n-- ############ LE VRAI PATCH L1, CORPS EXACT ############\n",
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
