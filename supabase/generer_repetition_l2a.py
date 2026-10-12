"""Assemble la REPETITION du lot L2-A depuis les VRAIS fichiers de patch.

Meme principe que pour L4 et L4-bis (lecon du point 4d) : assemblee, jamais
recopiee, donc aucune divergence possible avec ce qui sera applique.

Ce que la repetition verifie :
    - les 3 empreintes de fonction AVANT (celles du 12/10) ;
    - qu'apres le patch les 3 ont change, que le commercial connait 12 types au
      lieu de 7, que le garde du prix est dans LES DEUX chemins, et que le cas
      particulier admin (statut, archivage) est intact ;
    - qu'apres l'inverse les 3 empreintes sont EXACTEMENT celles d'AVANT.

Usage, depuis la racine du depot :
    python supabase/generer_repetition_l2a.py
"""

from pathlib import Path
import sys

ICI = Path(__file__).resolve().parent
PATCH = ICI / "patch_l2a_negociateur_champs_mandants_2026-10-12.sql"
INVERSE = ICI / "patch_l2a_negociateur_champs_mandants_2026-10-12_INVERSE.sql"
SORTIE = ICI / "patch_l2a_negociateur_champs_mandants_2026-10-12_REPETITION.sql"

FONCTIONS = [
    "app_console_can_request_job",
    "app_edit_annonce_optimistic",
    "app_console_create_update_annonce_job",
]
# Les 12 types que le commercial doit connaitre apres le patch (7 anciens + 5 neufs)
TYPES_COMMERCIAL = [
    "prepare_document_cloud", "upload_document_to_hektor",
    "prepare_archived_annonce_detail", "prepare_historical_annonce_detail",
    "sync_console_documents", "relance_signature", "cancel_signature_procedure",
    "update_hektor_annonce_fields", "link_hektor_mandant", "unlink_hektor_mandant",
    "create_hektor_mandant_contact", "update_hektor_mandant_contact",
]


def corps_sans_transaction(chemin: Path) -> str:
    if not chemin.exists():
        sys.exit(f"ERREUR : fichier introuvable -> {chemin}")
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    gardees = [l for l in lignes if l.strip().lower() not in ("begin;", "commit;")]
    print(f"  {chemin.name} : {len(lignes)} lignes, {len(lignes) - len(gardees)} begin/commit retiree(s)")
    return "\n".join(gardees)


def bloc_mesures(etape: str) -> str:
    liste_f = ", ".join(f"'{f}'" for f in FONCTIONS)
    liste_t = ", ".join(f"'{t}'" for t in TYPES_COMMERCIAL)
    return f"""
-- ---------- MESURES : {etape} ----------
-- ⚠ on compare l'empreinte SANS les retours chariot : un collage depuis Windows
--   en ajoute, et l'empreinte brute ne correspondrait jamais (piege du 08/10).
insert into _l2a_mesures(etape, cle, valeur)
select '{etape}', 'corps__' || p.proname, md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ({liste_f});

insert into _l2a_mesures(etape, cle, valeur)
select '{etape}', 'types_connus_du_commercial', count(*)::text
  from unnest(array[{liste_t}]) AS t(nom)
 where position(t.nom in (select pg_get_functiondef(p.oid)
                            from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                           where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
                           limit 1)) > 0;

insert into _l2a_mesures(etape, cle, valeur)
select '{etape}', 'garde_du_prix_dans_les_chemins', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_edit_annonce_optimistic', 'app_console_create_update_annonce_job')
   and position('prix_sur_demande' in pg_get_functiondef(p.oid)) > 0;

insert into _l2a_mesures(etape, cle, valeur)
select '{etape}', 'statut_et_archivage_admin_seul',
       case when position('archive_hektor_annonce' in d.def) > 0
             and position('change_hektor_annonce_status' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2a_mesures(etape, cle, valeur)
select '{etape}', 'controle_ses_biens_present',
       case when position('app_console_can_access_dossier' in d.def) > 0
            then 'oui' else 'NON' end
  from (select pg_get_functiondef(p.oid) as def
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
         limit 1) d;

insert into _l2a_mesures(etape, cle, valeur)
select '{etape}', 'fonctions_joignables_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ({liste_f})
   and has_function_privilege('anon', p.oid, 'EXECUTE');
"""


def main() -> None:
    print("Assemblage de la repetition L2-A, depuis les vrais fichiers :")
    patch = corps_sans_transaction(PATCH)
    inverse = corps_sans_transaction(INVERSE)

    entete = """-- ============================================================================
-- REPETITION DU LOT L2-A -- CE QUE LE NEGOCIATEUR FAIT SEUL (1/2)
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN :
--   ESSAI ANNULE -- RIEN N'A ETE ECRIT
--   FONCTIONS QUI NE REVIENNENT PAS A LEUR CORPS D'ORIGINE : 0   (0 attendu)
--   FONCTIONS QUE LE PATCH N'A PAS CHANGEES                : 0   (0 attendu)
--
--   AVANT          types_connus_du_commercial         = 7
--                  garde_du_prix_dans_les_chemins     = 0
--                  statut_et_archivage_admin_seul     = oui
--                  controle_ses_biens_present         = oui
--                  fonctions_joignables_sans_compte   = 0
--
--   APRES_PATCH    types_connus_du_commercial         = 12  <<< les 5 gestes ouverts
--                  garde_du_prix_dans_les_chemins     = 2   <<< le prix est garde
--                                                             DANS LES DEUX chemins
--                  statut_et_archivage_admin_seul     = oui <<< pas touche
--                  controle_ses_biens_present         = oui <<< « ses biens » tient
--                  fonctions_joignables_sans_compte   = 0   <<< chantier 1 intact
--
--   APRES_INVERSE  identique a AVANT
--
-- ⚠ CE QUE CETTE REPETITION NE PROUVE PAS : qu'un negociateur peut vraiment
--   modifier un champ et vraiment pas le prix. Cela se verifie en empruntant son
--   identite, APRES le collage (lecture seule, transaction annulee).
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_l2a.py.
--   NE PAS LE MODIFIER A LA MAIN : modifier les patchs, puis relancer le generateur.
-- ============================================================================

begin;

create temporary table _l2a_mesures(
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
    v_pas_revenues int;
    v_pas_changees int;
begin
    select count(*) into v_pas_revenues
      from _l2a_mesures a
      join _l2a_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'corps__')
       and a.valeur is distinct from z.valeur;

    select count(*) into v_pas_changees
      from _l2a_mesures a
      join _l2a_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and starts_with(a.cle, 'corps__')
       and a.valeur = p.valeur;

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l2a_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\\'A ETE ECRIT.\\n\\nFONCTIONS QUI NE REVIENNENT PAS A LEUR CORPS D\\'ORIGINE : %   (0 attendu)\\nFONCTIONS QUE LE PATCH N\\'A PAS CHANGEES                : %   (0 attendu)\\n\\n%\\n',
        v_pas_revenues, v_pas_changees, v_txt;
end
$final$;

-- jamais atteint
rollback;
"""

    texte = "".join([
        entete,
        bloc_mesures("AVANT"),
        "\n\n-- ############ LE VRAI PATCH L2-A, CORPS EXACT ############\n",
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
