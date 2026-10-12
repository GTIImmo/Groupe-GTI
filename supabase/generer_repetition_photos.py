"""Assemble la REPETITION du patch « photos » depuis les VRAIS fichiers.

Meme principe que pour L4, L4-bis, L2-A, L2-B et L1 (lecon du point 4d).
Avec le TEMOIN INVERSE partout (lecon du 12/10, memoire « repetition-temoin-inverse ») :
on verifie qu'une phrase APPARAIT *et* que l'ancienne DISPARAIT.

Usage, depuis la racine du depot :
    python supabase/generer_repetition_photos.py
"""

from pathlib import Path
import sys

ICI = Path(__file__).resolve().parent
PATCH = ICI / "patch_photos_reseau_2026-10-12.sql"
INVERSE = ICI / "patch_photos_reseau_2026-10-12_INVERSE.sql"
SORTIE = ICI / "patch_photos_reseau_2026-10-12_REPETITION.sql"


def corps_sans_transaction(chemin: Path) -> str:
    if not chemin.exists():
        sys.exit(f"ERREUR : fichier introuvable -> {chemin}")
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    gardees = [l for l in lignes if l.strip().lower() not in ("begin;", "commit;")]
    print(f"  {chemin.name} : {len(lignes)} lignes, {len(lignes) - len(gardees)} begin/commit retiree(s)")
    return "\n".join(gardees)


def bloc_mesures(etape: str) -> str:
    return f"""
-- ---------- MESURES : {etape} ----------
insert into _ph_mesures(etape, cle, valeur)
select '{etape}', 'regle__' || tablename, md5(coalesce(qual, ''))
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT'
   and tablename in ('app_console_photo', 'app_console_document');

-- LES PHOTOS : la nouvelle phrase doit APPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select '{etape}', 'photos_suivent_le_perimetre',
       case when position('app_mes_biens_selon_perimetre' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;

-- ...et l'ancienne DISPARAITRE (temoin inverse)
insert into _ph_mesures(etape, cle, valeur)
select '{etape}', 'photos_encore_sur_l_ancienne_fonction',
       case when position('app_console_can_access_dossier' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_photo' limit 1;

-- LES DOCUMENTS : la forme rapide doit APPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select '{etape}', 'documents_en_forme_rapide',
       case when position('app_mes_biens_portefeuille' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

-- ...l'ancienne DISPARAITRE...
insert into _ph_mesures(etape, cle, valeur)
select '{etape}', 'documents_encore_sur_l_ancienne_fonction',
       case when position('app_console_can_access_dossier' in coalesce(qual, '')) > 0
            then 'oui' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

-- ...et SURTOUT : les documents NE DOIVENT JAMAIS suivre le perimetre.
--    C'est le controle qui protege la decision « le dossier reste prive ».
insert into _ph_mesures(etape, cle, valeur)
select '{etape}', 'documents_suivent_le_perimetre_NE_DOIT_JAMAIS',
       case when position('app_perimetre_courant' in coalesce(qual, '')) > 0
            then '*** OUI, GRAVE ***' else 'non' end
  from pg_policies
 where schemaname = 'public' and cmd = 'SELECT' and tablename = 'app_console_document' limit 1;

insert into _ph_mesures(etape, cle, valeur)
select '{etape}', 'photos_lisibles_sans_compte',
       case when has_table_privilege('anon', c.oid, 'SELECT') then '*** OUI ***' else 'non' end
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relname = 'app_console_photo';
"""


def main() -> None:
    print("Assemblage de la repetition « photos », depuis les vrais fichiers :")
    patch = corps_sans_transaction(PATCH)
    inverse = corps_sans_transaction(INVERSE)

    entete = """-- ============================================================================
-- REPETITION -- LES PHOTOS SUIVENT LE BIEN
--
-- ⚠ CE SCRIPT N'ECRIT RIEN. Il joue le vrai patch, puis le vrai inverse, puis il
--   ECHOUE EXPRES pour tout annuler, et il affiche les mesures des trois etapes.
--
-- A COLLER dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- CE QU'IL FAUT VOIR A LA FIN :
--   ESSAI ANNULE -- RIEN N'A ETE ECRIT
--   REGLES QUI NE REVIENNENT PAS A L'ORIGINE : 0   (0 attendu)
--   REGLES QUE LE PATCH N'A PAS CHANGEES     : 0   (0 attendu)
--
--   AVANT          photos_suivent_le_perimetre                   = non
--                  photos_encore_sur_l_ancienne_fonction         = oui
--                  documents_en_forme_rapide                     = non
--                  documents_encore_sur_l_ancienne_fonction      = oui
--                  documents_suivent_le_perimetre_NE_DOIT_JAMAIS = non
--                  photos_lisibles_sans_compte                   = non
--
--   APRES_PATCH    photos_suivent_le_perimetre                   = oui  <<< BASCULE
--                  photos_encore_sur_l_ancienne_fonction         = non  <<< TEMOIN
--                  documents_en_forme_rapide                     = oui  <<< BASCULE
--                  documents_encore_sur_l_ancienne_fonction      = non  <<< TEMOIN
--                  documents_suivent_le_perimetre_NE_DOIT_JAMAIS = non  <<< LE PLUS IMPORTANT
--                  photos_lisibles_sans_compte                   = non  <<< chantier 1
--
--   APRES_INVERSE  identique a AVANT
--
-- ⚠ LES MESURES VONT PAR PAIRES et doivent basculer ENSEMBLE (non->oui et
--   oui->non). C'est la lecon du 12/10 : une mesure qui ne regarde qu'un sens
--   peut ne rien mesurer du tout.
--
-- ⚠ ET « documents_suivent_le_perimetre_NE_DOIT_JAMAIS » doit rester « non » AUX
--   TROIS ETAPES : le dossier d'un bien (mandat, diagnostics) reste prive, c'est
--   la decision de Frederic. Si cette ligne passe a OUI, on ne colle pas.
--
-- ⚠ Fichier ASSEMBLE par supabase/generer_repetition_photos.py.
-- ============================================================================

begin;

create temporary table _ph_mesures(
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
      from _ph_mesures a
      join _ph_mesures z on z.cle = a.cle and z.etape = 'APRES_INVERSE'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur is distinct from z.valeur;

    select count(*) into v_pas_changees
      from _ph_mesures a
      join _ph_mesures p on p.cle = a.cle and p.etape = 'APRES_PATCH'
     where a.etape = 'AVANT' and starts_with(a.cle, 'regle__')
       and a.valeur = p.valeur;

    select string_agg(etape || ' | ' || cle || ' = ' || coalesce(valeur, '(null)'), chr(10)
                      order by ordre)
      into v_txt
      from _ph_mesures;

    raise exception E'ESSAI ANNULE -- RIEN N\\'A ETE ECRIT.\\n\\nREGLES QUI NE REVIENNENT PAS A L\\'ORIGINE : %   (0 attendu)\\nREGLES QUE LE PATCH N\\'A PAS CHANGEES     : %   (0 attendu)\\n\\n%\\n',
        v_pas_revenues, v_pas_changees, v_txt;
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

    donnees = texte.encode("utf-8")
    SORTIE.write_bytes(donnees)
    print(f"\nEcrit : {SORTIE}")
    print(f"  {len(texte.splitlines())} lignes, {len(donnees)} octets")


if __name__ == "__main__":
    main()
