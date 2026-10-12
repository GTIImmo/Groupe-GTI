"""Assemble la REPETITION du lot L4 depuis les VRAIS fichiers de patch.

Pourquoi un generateur plutot qu'un fichier ecrit a la main : lecon du chantier 4,
point 4d. Une repetition recopiee a la main peut divergier du patch reel sans qu'on
le voie ; assemblee, elle ne peut pas.

La repetition produite :
    1. releve les mesures AVANT ;
    2. joue LE VRAI PATCH (corps exact, begin/commit retires) ;
    3. releve les mesures APRES PATCH ;
    4. joue LE VRAI INVERSE (corps exact) ;
    5. releve les mesures APRES INVERSE ;
    6. leve une erreur volontaire finale qui ANNULE TOUT et affiche les mesures.

Usage, depuis la racine du depot :
    python supabase/generer_repetition_l4.py
"""

from pathlib import Path
import sys

ICI = Path(__file__).resolve().parent
PATCH = ICI / "patch_l4_cloisonnement_2026-10-12.sql"
INVERSE = ICI / "patch_l4_cloisonnement_2026-10-12_INVERSE.sql"
SORTIE = ICI / "patch_l4_cloisonnement_2026-10-12_REPETITION.sql"

# Les 8 tables dont on suit la regle de lecture, et les 4 vues dont on suit le reglage.
TABLES = [
    "app_dossier_current",
    "app_contact_current",
    "app_contact_relation_current",
    "app_archive_annonce_index_current",
    "app_historical_annonce_index_current",
    "app_affaire_ledger",
    "app_mandat",
    "app_mandat_register_current",
]
VUES = [
    "app_dossiers_current",
    "app_contacts_current",
    "app_contact_relations_current",
    "app_registre_mandats_current",
]
VUES_FERMEES = ["app_contacts_sans_numero", "app_console_action_abandonnees"]


def corps_sans_transaction(chemin: Path) -> str:
    """Rend le fichier tel quel, moins les begin;/commit; de premier niveau."""
    if not chemin.exists():
        sys.exit(f"ERREUR : fichier introuvable -> {chemin}")
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    gardees = [l for l in lignes if l.strip().lower() not in ("begin;", "commit;")]
    retirees = len(lignes) - len(gardees)
    print(f"  {chemin.name} : {len(lignes)} lignes, {retirees} ligne(s) begin/commit retiree(s)")
    return "\n".join(gardees)


def bloc_mesures(etape: str) -> str:
    """Le meme releve, aux trois etapes. Genere, donc identique mot pour mot."""
    liste_tables = ", ".join(f"'{t}'" for t in TABLES)
    liste_vues = ", ".join(f"'{v}'" for v in VUES)
    liste_fermees = ", ".join(f"'{v}'" for v in VUES_FERMEES)
    return f"""
-- ---------- MESURES : {etape} ----------
insert into _l4_mesures(etape, cle, valeur)
select '{etape}', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ({liste_tables});

insert into _l4_mesures(etape, cle, valeur)
select '{etape}', 'vues_qui_regardent_le_gardien', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relkind = 'v' and c.relname in ({liste_vues})
   and exists (select 1 from pg_options_to_table(c.reloptions)
                where option_name = 'security_invoker' and option_value in ('on', 'true'));

insert into _l4_mesures(etape, cle, valeur)
select '{etape}', 'vues_techniques_lisibles_par_un_compte', count(*)::text
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname in ({liste_fermees})
   and has_table_privilege('authenticated', c.oid, 'SELECT');

insert into _l4_mesures(etape, cle, valeur)
select '{etape}', 'case_perimetre',
       case when exists (select 1 from information_schema.columns
                          where table_schema = 'public' and table_name = 'app_user_profile'
                            and column_name = 'perimetre')
            then 'presente' else 'absente' end;

-- ⚠ On lit le perimetre par to_jsonb(p) ->> 'perimetre', PAS par « p.perimetre ».
--   Raison : aux etapes AVANT et APRES_INVERSE la colonne n'existe pas, et un CASE
--   ne protege de rien -- PostgreSQL ANALYSE toute la requete avant de l'executer,
--   branche non prise comprise, donc il echoue sur « column perimetre does not
--   exist ». to_jsonb rend NULL quand la colonne est absente : la mesure passe aux
--   trois etapes, avec la meme ligne de code.
insert into _l4_mesures(etape, cle, valeur)
select '{etape}', 'comptes_hors_reseau',
       (select count(*)::text
          from public.app_user_profile p
         where coalesce(to_jsonb(p) ->> 'perimetre', 'reseau') <> 'reseau');

insert into _l4_mesures(etape, cle, valeur)
select '{etape}', 'fonctions_neuves_presentes', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre');

insert into _l4_mesures(etape, cle, valeur)
select '{etape}', 'fonctions_neuves_ouvertes_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre')
   and has_function_privilege('anon', p.oid, 'EXECUTE');

insert into _l4_mesures(etape, cle, valeur)
select '{etape}', 'fonctions_neuves_utilisables_par_un_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_perimetre_courant', 'app_mon_agence',
                     'app_voit_cette_ligne', 'app_voit_ce_dossier_selon_perimetre')
   and has_function_privilege('authenticated', p.oid, 'EXECUTE');
"""


def main() -> None:
    print("Assemblage de la repetition L4, depuis les vrais fichiers :")
    patch = corps_sans_transaction(PATCH)
    inverse = corps_sans_transaction(INVERSE)

    entete = f"""-- ============================================================================
-- REPETITION DU LOT L4 -- CLOISONNER LES CONSULTATIONS
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN -- le message doit commencer par
--   « ESSAI ANNULE -- RIEN N'A ETE ECRIT »
-- et les mesures doivent dire EXACTEMENT ceci :
--
--   AVANT          vues_qui_regardent_le_gardien                = 0
--                  vues_techniques_lisibles_par_un_compte       = 2
--                  case_perimetre                               = absente
--                  fonctions_neuves_presentes                   = 0
--
--   APRES_PATCH    vues_qui_regardent_le_gardien                = 4
--                  vues_techniques_lisibles_par_un_compte       = 0
--                  case_perimetre                               = presente
--                  comptes_hors_reseau                          = 0
--                  fonctions_neuves_presentes                   = 4
--                  fonctions_neuves_ouvertes_sans_compte        = 0   <<< chantier 1 intact
--                  fonctions_neuves_utilisables_par_un_compte   = 4   <<< l'ecran marche
--
--   APRES_INVERSE  vues_qui_regardent_le_gardien                = 0
--                  vues_techniques_lisibles_par_un_compte       = 2
--                  case_perimetre                               = absente
--                  fonctions_neuves_presentes                   = 0
--
-- ET SURTOUT : les 8 empreintes « regle__* » de AVANT doivent etre IDENTIQUES a
-- celles de APRES_INVERSE. C'est la preuve que le retour arriere est exact.
-- Les 8 de APRES_PATCH doivent, elles, etre DIFFERENTES de AVANT.
--
-- NE PAS COLLER LE VRAI PATCH tant que ces chiffres ne sont pas ceux-la.
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_l4.py depuis
--   patch_l4_cloisonnement_2026-10-12.sql et son INVERSE.
--   NE PAS LE MODIFIER A LA MAIN : modifier les patchs, puis relancer le generateur.
-- ============================================================================

begin;

create temporary table _l4_mesures(
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
    v_ecarts int;
begin
    select count(*) into v_ecarts
      from _l4_mesures a
      join _l4_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur is distinct from z.valeur;
    -- starts_with, PAS « like 'regle__%' » : dans LIKE, le caractere _ est un
    -- joker, donc le motif aurait aussi attrape des cles voisines. Piege deja
    -- paye le 08/10 sur une mesure SQLite.

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l4_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\\'A ETE ECRIT.\\n\\nREGLES QUI NE REVIENNENT PAS A LEUR ETAT D\\'ORIGINE : %\\n(0 attendu)\\n\\n%\\n',
        v_ecarts, v_txt;
end
$final$;

-- jamais atteint
rollback;
"""

    texte = "".join([
        entete,
        bloc_mesures("AVANT"),
        "\n\n-- ############ LE VRAI PATCH, CORPS EXACT ############\n",
        patch,
        "\n",
        bloc_mesures("APRES_PATCH"),
        "\n\n-- ############ LE VRAI INVERSE, CORPS EXACT ############\n",
        inverse,
        "\n",
        bloc_mesures("APRES_INVERSE"),
        final,
    ])

    # On encode AVANT d'ouvrir le fichier : sinon une erreur d'encodage laisse un
    # fichier tronque derriere elle (lecon du 02/10).
    donnees = texte.encode("utf-8")
    SORTIE.write_bytes(donnees)
    print(f"\nEcrit : {SORTIE}")
    print(f"  {len(texte.splitlines())} lignes, {len(donnees)} octets")


if __name__ == "__main__":
    main()
