-- ═══════════════════════════════════════════════════════════════════════════
-- REPETITION de la cascade -- jouee puis ANNULEE                   11/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⚠ ELLE N'APPELLE PAS LA RPC, et ce n'est pas un raccourci :
--   app_geste_affaire_optimistic exige is_app_manager_or_admin(), qui vaut FALSE
--   sans utilisateur connecte. Une repetition en service_role n'ecrirait donc
--   rien et rendrait un faux vert (lecon du projet : « la mise en scene en
--   authenticated n'ecrit RIEN »).
-- ➡ Elle eprouve donc LE COEUR DE LA REGLE : la requete qui CHOISIT les offres a
--   refuser. C'est elle qui peut abimer des donnees ; le reste est de la plomberie.
--
--   a coller tel quel. 7 lignes, toutes OK.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

create temporary table resultat_repetition (ordre int, controle text, verdict text) on commit drop;

-- ─── LA REQUETE DE LA CASCADE, EXTRAITE TELLE QUELLE ───────────────────────
create temporary view cascade_choisirait as
select a.app_chaine_id as dossier, l.app_affaire_id as offre, l.hektor_affaire_id as offre_hektor
from public.app_affaire_ledger a
join public.app_affaire_ledger l on l.app_chaine_id = a.app_chaine_id
                                and l.app_affaire_id <> a.app_affaire_id
where a.kind = 'compromis'
  and lower(coalesce(a.state,'')) in ('cancelled','annule')
  and l.kind = 'offre'
  and lower(coalesce(l.state,'')) in ('accepted','acceptee')
  and btrim(coalesce(l.hektor_affaire_id::text,'')) <> ''
  and not (btrim(coalesce(l.hektor_affaire_id::text,'')) <> '' and l.present_in_hektor is false)
  and not exists (
        select 1 from public.app_affaire_ledger v
         where v.app_chaine_id = a.app_chaine_id
           and v.app_affaire_id <> a.app_affaire_id
           and not (btrim(coalesce(v.hektor_affaire_id::text,'')) <> '' and v.present_in_hektor is false)
           and ( v.kind = 'vente'
              or (v.kind = 'compromis' and lower(coalesce(v.state,'')) not in ('cancelled','annule')) ));

-- ① Elle trouve bien la population mesuree le 10/11 : 661 dossiers, 661 offres.
insert into resultat_repetition
select 1, '① la cascade vise 661 dossiers, une offre chacun',
       case when count(distinct dossier) = count(*) and count(*) between 640 and 680
            then 'OK  (' || count(*) || ' offres dans ' || count(distinct dossier) || ' dossiers)'
            else 'A REGARDER  (' || count(*) || ' offres / ' || count(distinct dossier) || ' dossiers)' end
from cascade_choisirait;

-- ② ⛔ TEMOIN INVERSE, LE PLUS IMPORTANT : aucun dossier portant une VENTE.
--   Les 8 658 « vente + offre acceptee » sont NORMAUX. Si un seul apparait ici,
--   la regle detruirait l'histoire vraie de 8 658 affaires abouties.
insert into resultat_repetition
select 2, '② TEMOIN INVERSE : aucun dossier portant une vente',
       case when count(*) = 0 then 'OK  (0 -- les 8 658 affaires vendues sont intactes)'
            else 'ECHEC  (' || count(*) || ' -- NE PAS POSER)' end
from cascade_choisirait c
where exists (select 1 from public.app_affaire_ledger v
               where v.app_chaine_id = c.dossier and v.kind = 'vente');

-- ③ ⛔ TEMOIN INVERSE : aucun dossier portant un compromis encore VIVANT.
insert into resultat_repetition
select 3, '③ TEMOIN INVERSE : aucun compromis encore vivant',
       case when count(*) = 0 then 'OK  (0)'
            else 'ECHEC  (' || count(*) || ' -- NE PAS POSER)' end
from cascade_choisirait c
where exists (select 1 from public.app_affaire_ledger v
               where v.app_chaine_id = c.dossier and v.kind = 'compromis'
                 and lower(coalesce(v.state,'')) not in ('cancelled','annule'));

-- ④ ⛔⛔ LE VRAI TEMOIN POSITIF -- ET IL A FALLU LE FABRIQUER.
--   Premiere version, le 11/11 : elle comparait « avec la garde » et « sans la
--   garde » sur les donnees reelles, et rendait ECHEC -- 661 des deux cotes.
--   ⭐ La garde n'etait pas cassee : elle n'avait RIEN A FILTRER. Il n'existe
--     AUCUN dossier « compromis annule + vente » dans la base (mesure : 0).
--   Un garde-fou qu'aucune donnee ne declenche ne peut pas s'eprouver sur ces
--   donnees : il faut lui FABRIQUER son cas. On ajoute donc une vente a un vrai
--   dossier des 661, dans la transaction annulee, et on verifie qu'il disparait.
create temporary table cible on commit drop as
select a.app_chaine_id as dossier, a.hektor_annonce_id, a.app_dossier_id
from public.app_affaire_ledger a
where a.kind='compromis' and lower(coalesce(a.state,'')) in ('cancelled','annule')
  and exists (select 1 from public.app_affaire_ledger l
               where l.app_chaine_id=a.app_chaine_id and l.kind='offre'
                 and lower(coalesce(l.state,'')) in ('accepted','acceptee'))
order by a.app_chaine_id limit 1;

insert into resultat_repetition
select 4, '④ TEMOIN INVERSE du temoin : sans la vente, le dossier passait bien',
       case when count(*) > 0 then 'OK  (' || count(*) || ' -- il etait bien candidat avant)'
            else 'ECHEC  (le dossier d''essai n''est pas candidat : temoin inutilisable)' end
from cascade_choisirait where dossier = (select dossier from cible);

insert into public.app_affaire_ledger
       (app_affaire_id, app_chaine_id, app_dossier_id, hektor_annonce_id, kind, state, hektor_affaire_id)
select 999999999, dossier, app_dossier_id, hektor_annonce_id, 'vente', null, '999999999' from cible;

insert into resultat_repetition
select 5, '⑤ TEMOIN POSITIF : une VENTE ajoutee -- la garde doit ecarter ce dossier',
       case when count(*) = 0 then 'OK  (la garde a ECARTE le dossier : elle MORD)'
            else 'ECHEC  (' || count(*) || ' -- elle laisse passer un dossier VENDU : NE PAS POSER)' end
from cascade_choisirait where dossier = (select dossier from cible);

-- ⑤ Toutes les offres visees ont un numero Hektor -- sans lui, le worker jette.
insert into resultat_repetition
select 6, '⑥ toutes les offres visees ont un numero Hektor',
       case when count(*) filter (where btrim(coalesce(offre_hektor::text,'')) = '') = 0
            then 'OK  (0 sans numero)' else 'ECHEC' end
from cascade_choisirait;

-- ⑥ Aucun recouvrement avec les offres SEULES du rattrapage : deux populations.
insert into resultat_repetition
select 7, '⑦ aucun recouvrement avec le rattrapage des offres seules',
       case when count(*) = 0 then 'OK  (0 -- les deux travaux s''additionnent)'
            else 'A REGARDER  (' || count(*) || ' en commun)' end
from cascade_choisirait c
where not exists (select 1 from public.app_affaire_ledger x
                   where x.app_chaine_id = c.dossier and x.kind = 'compromis');

select controle, verdict from resultat_repetition order by ordre;

rollback;   -- ⛔ RIEN N'EST POSE.
