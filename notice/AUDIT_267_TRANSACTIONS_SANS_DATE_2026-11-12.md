# AUDIT — LES 267 TRANSACTIONS SANS DATE : est-ce nouveau, et est-ce grave ?

**12/11/2026, au soir** — demandé par Frédéric : *« Audit de nouveau comment as ton
autant de transactions sans date surtout des compromis actif reprend le chat et le
chantier nos audit et analyse as ton deja vue cela autant de transactions sans date
dont des récent et vivantes !!!! Audit en profondeur. »*

> ⛔ **MA FAUTE DE MÉTHODE, ET ELLE EST LA PREMIÈRE CHOSE À DIRE.** J'ai présenté ces
> 267 comme une trouvaille du soir. **Deux audits dédiés existaient déjà dans le
> dépôt**, dont un d'avant-hier, et ils répondaient à presque tout :
> `notice/AUDIT_DATES_0000_COMPROMIS_ET_OFFRES_2026-11-02.md` (405 lignes) et
> `notice/AUDIT_OFFRES_SEULES_ET_COMPROMIS_SANS_DATE_2026-11-10.md` (125 lignes).
> La liste de relecture du projet demande « est-ce documenté ? » **avant** de
> conclure. Je ne l'ai pas fait.

---

## 1. ⭐ LA PREMIÈRE RÉPONSE : CE N'EST PAS NOUVEAU, ET CE N'EST PAS MOI

Le témoin est la **base locale**, remplie par la descente de ce matin **07:45** —
donc un état **antérieur à tout mon travail du jour**, et postérieur à la cascade
d'annulation du 11/11.

```
app_affaire_ledger   (local, 07:45)              les 13 compromis actifs y sont,
                                                 les 13 deja a 0000-00-00
app_affaire_ledger__sb (ce que Supabase a rendu) les 13, idem
photo « avant_offre_sans_date » du 02/11         1 des 13 y est, deja a 0000-00-00
```

Et le chiffre **n'a pas bougé depuis dix jours** :

```
                                     02/11 (audit)   12/11 (ce soir)
compromis a 0000-00-00 au registre        204              204
compromis a 1990-01-01                      7                7
```

⚠ **LE « +5 » QUE J'AI CRU VOIR ÉTAIT UNE FAUTE DE MESURE, PAS UN MOUVEMENT.** Mon
critère local comptait `1990-01-01` comme « sans date » (année hors 2000-2030) ; mon
critère Supabase, non. **Deux critères différents donnent deux chiffres différents** —
et les 7 écarts sont exactement les 7 compromis à `1990` que l'audit du 02/11 avait
déjà comptés. ⭐ *Leçon : comparer deux bases exige le MÊME prédicat, écrit une fois.*

---

## 2. LA RAISON, MESURÉE LE 02/11 ET TOUJOURS VRAIE

**Un compromis sans date n'a pas été signé.** Le `date_start` de Hektor **est** la date
de signature : annulé avant signature, il n'y a rien à y mettre.

Le ratio le prouve sans discussion :

```
compromis ANNULES  : 191 sans date sur 1 377   = 13,9 %
compromis ACTIFS   :  13 sans date sur 9 276   =  0,14 %
```

⭐ **Un compromis annulé a cent fois plus de chances d'être sans date.** Ce n'est donc
ni un défaut de lecture, ni une perte : **c'est une information**. Hektor dit « pas de
date » parce qu'il n'y en a pas eu.

⚠ Et l'affichage `0000-00-00` à l'écran n'est pas un bug non plus : `formatDate`
(App.tsx:7449) rend une date invalide telle quelle.

---

## 3. LA COMPOSITION EXACTE DES 267, VÉRIFIÉE DEUX FOIS

```
compromis annules                   191     transactions MORTES
offres sans etat (coquilles)         48     EXCLUES du registre par app_affaire_est_coquille
compromis ACTIFS                     13     <- la famille a regarder
offres refusees                      10     dont les 5 datees ce soir
offres proposees                      3     \  les 5 offres VIVANTES
offres acceptees                      2     /
                                    ---
                                    267
```

L'arithmétique se referme de deux façons :
`267 = 191+48+13+10+3+2` et `267 = 173` (dans un dossier daté par ailleurs) `+ 94`
(dans un dossier dont aucune transaction n'a de jour).

---

## 4. ⭐ LES 5 OFFRES VIVANTES SANS DATE — AUCUN ENJEU, ET C'EST MESURÉ

```
offre   etat       dossier       bien    statut du bien        le dossier entier
3582    proposed   D2024-0438    8315    vendu/clos/archive    compromis:active + VENTE
9291    proposed   D2025-0116   18412    vendu/clos/archive    compromis:active + VENTE
14186   accepted   D2018-0082   28709    vendu/clos/archive    compromis:active + VENTE
19567   accepted   D2025-0192   40590    vendu/clos/archive    compromis:active + VENTE
27741   proposed   D2019-0256   53984    vendu/clos/archive    compromis:active + VENTE
```

⭐⭐ **LES CINQ SONT DANS UN DOSSIER COMPLET** : offre → compromis → vente, et le bien
est vendu ou clos. Seul le **jour de l'offre** manque, et la cascade du registre
emprunte alors la date du compromis. **Rien à réparer.** Leur état « proposée » ou
« acceptée » est un résidu chez Hektor sur une affaire terminée.

⚠ Leur `date` est `NULL`, pas `0000-00-00` : ce sont des offres dont Hektor ne rend
aucune date, pas même la sentinelle.

---

## 5. ⭐⭐ LES 13 COMPROMIS ACTIFS — TROIS FAMILLES, ET UNE SEULE COMPTE

```
compromis  dossier      bien    statut du bien       chez Hektor  le dossier entier
-- (A) LE DOSSIER PORTE DEJA SA VENTE -- residu d'etat, aucun enjeu : 8
28660      D2026-0009   59272   vendu/clos/archive   oui    compromis + offre acceptee + VENTE
27094      D2024-0184   53256   vendu/clos/archive   oui    compromis + offre acceptee + VENTE
16407      D2020-0550   34259   vendu/clos/archive   oui    compromis + offre acceptee + VENTE
20672      D2020-0341   42025   vendu/clos/archive   oui    compromis + offre acceptee + VENTE
25827      D2006-0065   49831   vendu/clos/archive   oui    compromis + offre acceptee + VENTE
16197      D2021-0199   33458   vendu/clos/archive   oui    compromis + VENTE
7212       D2017-0138   14732   vendu/clos/archive   oui    compromis + VENTE
7208       D2017-0137   14730   vendu/clos/archive   oui    compromis + VENTE
-- (B) EFFACES CHEZ HEKTOR, GARDES CHEZ NOUS -- voulu (audit 02/11) : 3
19049      D2025-0423   39684   vendu/clos/archive   NON    compromis SEUL
19414      D2025-0426   40318   « Sous compromis »   NON    compromis SEUL   <- ⚠
28568      D2025-0436   58979   « Sous offre »       NON    compromis SEUL   <- ⚠
-- (C) ACTIF CHEZ HEKTOR SUR UN BIEN VIVANT : 2
3699       D2022-0350    8494   « Sous offre »       oui    compromis + offre acceptee  <- ⚠
28341      D2025-0146   55091   vendu/clos/archive   oui    compromis + offre acceptee
```

### ⭐ LA FAMILLE A — 8 sur 13, et il n'y a rien à faire

Le dossier porte **déjà sa vente**. Le compromis « actif » est un état que Hektor n'a
jamais refermé après l'acte. L'affaire est complète, la date de la vente est là, le
registre et le pilotage sont justes. ⭐ C'est exactement ce que l'audit du 10/11
appelait *« 9 actifs sur un bien VENDU : le compromis de la vente, coupé de son
dossier faute de date »* — et **le remède existe déjà, codé et éteint** :
`APP_CHAINAGE_SANS_DATE=2` (le § 2.7), mesuré à « +10 ». La production est au cran 1.

### ⚠ LA FAMILLE B — 3 compromis effacés chez Hektor

`present_in_hektor = false`. Les garder est une **décision écrite** (audit du 02/11 :
*« 5 de ces compromis ont été effacés chez Hektor et conservés chez nous. C'est
voulu — le carnet est à nous, on garde la trace »*).

⛔ **MAIS DEUX D'ENTRE EUX PORTENT UN BIEN ENCORE VIVANT, et ça n'avait pas été dit :**
le bien **40318 est affiché « Sous compromis »** et le bien **58979 « Sous offre »**,
alors que leur compromis **n'existe plus chez Hektor**. Un bien annoncé sous compromis
dont le compromis a disparu est une incohérence visible par un négociateur.

### ⚠ LA FAMILLE C — 2, dont la dernière anomalie ouverte du 10/11

`3699` (bien 8494, « Sous offre ») est **la troisième des « 3 vraies anomalies
Hektor »** nommées le 10/11. Elle est **toujours ouverte**.

⭐⭐ **ET LES DEUX AUTRES ONT ÉTÉ RÉPARÉES ENTRE LE 10/11 ET AUJOURD'HUI** — mesuré :
`27033` (bien 53015) et `28155` (bien 54726), que l'audit du 10/11 décrivait comme
*« actifs chez Hektor sur un bien clos »*, sont **passés à `cancelled`**. C'est le
seul vrai mouvement depuis le 10/11, et il va dans le bon sens.

---

## 6. ➡ CE QU'IL FAUT RETENIR, ET CE QUI MÉRITE UN GESTE

```
267 transactions sans date   CONNU, STABLE, DOCUMENTE depuis le 02/11. Pas moi.
239 sur 267                  transactions MORTES ou coquilles exclues -> rien a faire
  8 compromis actifs         le dossier porte deja sa VENTE -> residu, remede code et
                             ETEINT (APP_CHAINAGE_SANS_DATE=2, mesure a « +10 »)
  5 offres vivantes          dossier COMPLET (compromis + vente), bien vendu/clos
                             -> rien a faire
```

⚠ **LES 3 SEULES LIGNES QUI TOUCHENT UN BIEN VIVANT AUJOURD'HUI :**

```
bien 40318   affiche « Sous compromis »   son compromis 19414 a DISPARU de Hektor
bien 58979   affiche « Sous offre »       son compromis 28568 a DISPARU de Hektor
bien  8494   affiche « Sous offre »       compromis 3699 ACTIF chez Hektor
                                          (3e anomalie du 10/11, toujours ouverte)
```

⭐ **Trois biens, pas treize.** Et ce sont des cas à regarder **un par un chez Hektor**,
pas une règle à écrire : trois lignes ne justifient pas un mécanisme.

⬜ **RIEN N'EST DÉCIDÉ, ET RIEN N'A ÉTÉ ÉCRIT NULLE PART POUR CET AUDIT** (lecture
seule de bout en bout). Les deux questions qui restent à Frédéric :
1. regarde-t-on les 3 biens vivants à la main chez Hektor ?
2. passe-t-on `APP_CHAINAGE_SANS_DATE` au cran 2 ? Il recollerait les 8 compromis de
   la famille A à leur vente. ⚠ Mesuré à « +10 » le 10/11 — donc à remesurer avant,
   les quatre règles de chaînage ayant été allumées depuis.
