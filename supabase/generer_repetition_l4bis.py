"""Assemble la REPETITION du lot L4-BIS depuis les VRAIS fichiers de patch.

Meme principe que generer_repetition_l4.py (lecon du point 4d) : la repetition
n'est pas recopiee, elle est ASSEMBLEE, donc elle ne peut pas divergier du patch.

Ce que la repetition verifie :
    - les 7 empreintes de regles AVANT (= l'etat laisse par L4 ce matin) ;
    - qu'apres le patch elles ont TOUTES change, et que les 2 ensembles sont la,
      ouverts a un compte connecte et FERMES sans compte ;
    - que les 4 fonctions de L4 sont intactes (L4-bis ne les supprime pas) ;
    - qu'apres l'inverse, les 7 empreintes sont EXACTEMENT celles d'AVANT.

⚠ L'EQUIVALENCE DES NOMBRES VUS (un admin voit tout, Melanie voit 13 475 annonces,
   3 affaires sur son bien, 0 sur celui d'un collegue, 0 au registre) ne se verifie
   PAS ici : la repetition tourne en tant que proprietaire de la base, qui ignore
   ces regles. Elle se verifie en empruntant chaque identite le temps d'une lecture,
   AVANT et APRES le collage -- c'est ce que fait Claude, et les nombres d'avant
   sont deja releves dans la note du chantier.

Usage, depuis la racine du depot :
    python supabase/generer_repetition_l4bis.py
"""

from pathlib import Path
import sys

ICI = Path(__file__).resolve().parent
PATCH = ICI / "patch_l4bis_vitesse_2026-10-12.sql"
INVERSE = ICI / "patch_l4bis_vitesse_2026-10-12_INVERSE.sql"
SORTIE = ICI / "patch_l4bis_vitesse_2026-10-12_REPETITION.sql"

TABLES = [
    "app_dossier_current",
    "app_archive_annonce_index_current",
    "app_historical_annonce_index_current",
    "app_contact_current",
    "app_contact_relation_current",
    "app_affaire_ledger",
    "app_mandat",
]
ENSEMBLES = ["app_mes_biens_portefeuille", "app_mes_biens_selon_perimetre"]
FONCTIONS_L4 = ["app_perimetre_courant", "app_mon_agence",
                "app_voit_cette_ligne", "app_voit_ce_dossier_selon_perimetre"]


def corps_sans_transaction(chemin: Path) -> str:
    if not chemin.exists():
        sys.exit(f"ERREUR : fichier introuvable -> {chemin}")
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    gardees = [l for l in lignes if l.strip().lower() not in ("begin;", "commit;")]
    print(f"  {chemin.name} : {len(lignes)} lignes, {len(lignes) - len(gardees)} begin/commit retiree(s)")
    return "\n".join(gardees)


def bloc_mesures(etape: str) -> str:
    liste_tables = ", ".join(f"'{t}'" for t in TABLES)
    liste_ens = ", ".join(f"'{f}'" for f in ENSEMBLES)
    liste_l4 = ", ".join(f"'{f}'" for f in FONCTIONS_L4)
    return f"""
-- ---------- MESURES : {etape} ----------
insert into _l4bis_mesures(etape, cle, valeur)
select '{etape}', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename in ({liste_tables});

insert into _l4bis_mesures(etape, cle, valeur)
select '{etape}', 'ensembles_presents', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ({liste_ens});

insert into _l4bis_mesures(etape, cle, valeur)
select '{etape}', 'ensembles_ouverts_sans_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ({liste_ens})
   and has_function_privilege('anon', p.oid, 'EXECUTE');

insert into _l4bis_mesures(etape, cle, valeur)
select '{etape}', 'ensembles_utilisables_par_un_compte', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ({liste_ens})
   and has_function_privilege('authenticated', p.oid, 'EXECUTE');

insert into _l4bis_mesures(etape, cle, valeur)
select '{etape}', 'fonctions_de_L4_intactes', count(*)::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ({liste_l4});

insert into _l4bis_mesures(etape, cle, valeur)
select '{etape}', 'regles_de_lecture_au_total', count(*)::text
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT'
   and tablename in ({liste_tables}, 'app_mandat_register_current');

insert into _l4bis_mesures(etape, cle, valeur)
select '{etape}', 'registre_des_mandats_reserve',
       case when exists (select 1 from pg_policies
                          where schemaname = 'public' and cmd = 'SELECT'
                            and tablename = 'app_mandat_register_current'
                            and qual like '%is_app_manager_or_admin%')
            then 'oui' else 'NON' end;
"""


def main() -> None:
    print("Assemblage de la repetition L4-BIS, depuis les vrais fichiers :")
    patch = corps_sans_transaction(PATCH)
    inverse = corps_sans_transaction(INVERSE)

    entete = """-- ============================================================================
-- REPETITION DU LOT L4-BIS -- LA VITESSE DU CLOISONNEMENT
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN -- le message doit commencer par
--   « ESSAI ANNULE -- RIEN N'A ETE ECRIT »
-- et dire :
--   REGLES QUI NE REVIENNENT PAS A LEUR ETAT D'ORIGINE : 0
--   REGLES QUE LE PATCH N'A PAS CHANGEES : 0
--
-- Les mesures doivent dire EXACTEMENT ceci :
--
--   AVANT          ensembles_presents                        = 0
--                  fonctions_de_L4_intactes                  = 4
--                  regles_de_lecture_au_total                = 8
--                  registre_des_mandats_reserve              = oui
--
--   APRES_PATCH    ensembles_presents                        = 2
--                  ensembles_ouverts_sans_compte             = 0   <<< chantier 1 intact
--                  ensembles_utilisables_par_un_compte       = 2   <<< l'ecran marche
--                  fonctions_de_L4_intactes                  = 4   <<< rien n'est supprime
--                  regles_de_lecture_au_total                = 8
--                  registre_des_mandats_reserve              = oui <<< pas touche
--
--   APRES_INVERSE  ensembles_presents                        = 0
--                  fonctions_de_L4_intactes                  = 4
--                  regles_de_lecture_au_total                = 8
--                  registre_des_mandats_reserve              = oui
--
-- ET les 7 empreintes « regle__* » : AVANT = APRES_INVERSE, et toutes
-- DIFFERENTES dans APRES_PATCH.
--
-- ⚠ CE QUE CETTE REPETITION NE PEUT PAS PROUVER : que les memes comptes voient
--   les memes lignes qu'avant. Elle tourne en tant que proprietaire de la base,
--   qui ignore ces regles. Cette preuve se fait en empruntant chaque identite le
--   temps d'une lecture, avant et apres le collage -- les nombres d'avant sont
--   deja releves (admin : 13 475 / 62 189 / 24 502 / 35 318 / 8 940 / 26 851 ·
--   Melanie : 13 475 annonces, 3 affaires sur son bien 1346424, 0 sur le bien
--   1357257 d'un collegue, 0 au registre, agence Groupe GTI Saint-Etienne).
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_l4bis.py.
--   NE PAS LE MODIFIER A LA MAIN : modifier les patchs, puis relancer le generateur.
-- ============================================================================

begin;

create temporary table _l4bis_mesures(
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
      from _l4bis_mesures a
      join _l4bis_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur is distinct from z.valeur;

    select count(*) into v_pas_changees
      from _l4bis_mesures a
      join _l4bis_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur = p.valeur;

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _l4bis_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\\'A ETE ECRIT.\\n\\nREGLES QUI NE REVIENNENT PAS A LEUR ETAT D\\'ORIGINE : %   (0 attendu)\\nREGLES QUE LE PATCH N\\'A PAS CHANGEES : %   (0 attendu)\\n\\n%\\n',
        v_pas_revenues, v_pas_changees, v_txt;
end
$final$;

-- jamais atteint
rollback;
"""

    texte = "".join([
        entete,
        bloc_mesures("AVANT"),
        "\n\n-- ############ LE VRAI PATCH L4-BIS, CORPS EXACT ############\n",
        patch,
        "\n",
        bloc_mesures("APRES_PATCH"),
        "\n\n-- ############ LE VRAI INVERSE, CORPS EXACT ############\n",
        inverse,
        "\n",
        bloc_mesures("APRES_INVERSE"),
        final,
    ])

    # On encode AVANT d'ouvrir : une erreur d'encodage ne laissera pas un fichier
    # tronque derriere elle.
    donnees = texte.encode("utf-8")
    SORTIE.write_bytes(donnees)
    print(f"\nEcrit : {SORTIE}")
    print(f"  {len(texte.splitlines())} lignes, {len(donnees)} octets")


if __name__ == "__main__":
    main()
