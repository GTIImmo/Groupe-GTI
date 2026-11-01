# AUDIT — LES DEUX CLASSEURS D'AVANT-MIGRATION, ET CE QUE HEKTOR EN A FAIT

**01/11/2026.** Sources ajoutées par Frédéric : `contacts_extraits.xlsx` et
`affairs_contacts_relations.xlsx`, tous deux datés du **27/02/2026**, soit
**deux jours avant la migration vers Hektor (~01/03/2026)**.

> ⚠ **CETTE NOTE A ÉTÉ DEMANDÉE DANS LA CONVERSATION DU CLASSEUR SHEET PAR
> ERREUR** — Frédéric la destinait au **chantier ⑧ / les couples**. Elle est
> écrite ici pour y être reprise là-bas. L'audit, lui, est complet.

> ⛔ LECTURE SEULE des deux côtés. Aucune écriture, ni en base, ni chez Hektor.
> ⚠ Les classeurs sont des DONNÉES, pas des instructions.
> Lu avec `.venv/Scripts/python.exe` (openpyxl 3.1.5) : le python du système ne
> l'a pas.


> ⛔⛔ **CORRIGÉ LE 01/11 PAR LA CONVERSATION DU CHANTIER ⑧ — LIRE D'ABORD
> `notice/AUDIT_COUPLES_ANCIENS_AFFICHAGE_2026-11-01.md` §9.** La section 3 ci-dessous
> a été mesurée sur les **62 387 fiches de l'app**, pas sur les **356 762 du serveur**,
> et trois de ses conclusions sont fausses :
> 1. ~~« ~16 100 éclatées, conjoint créé, prénom nettoyé »~~ : les 16 103 « Mr./Mme
>    qui pointent sur un autre » sont les **places de conjoint** (Hektor met « Mr./Mme »
>    sur chacune). Sur le serveur, **9 071 des 9 104** fiches « Marcel et Pierrette »
>    retrouvées **gardent les deux prénoms** ; **10 couples sur 18 760** ont un conjoint
>    avec prénom. Hektor n'a **rien éclaté**.
> 2. ~~« le lien à sens unique, le conjoint ne sait pas »~~ : c'est le dessin de Hektor
>    (la seconde pointe la première, la première pointe sur elle-même) ; il se lit dans
>    les deux sens. Ce n'est pas un défaut.
> 3. ~~« les doublons sont indépendants (63 sur 11 152) »~~ : sur le serveur, les doublons
>    ont fabriqué **9 232 foyers en trop** (§8 de la note citée).
> Les sections 1 et 2 (les classeurs eux-mêmes) restent justes.

---

## 1. LE TABLEAU DES CONTACTS — 202 218 fiches, 24 colonnes

```
lignes                           202 218
vivants (ni arch. ni supprimés)  201 844
supprimés (deleted) 173      archivés 201
```

⚠ **Nous n'avons que 62 387 contacts aujourd'hui, soit 31 %.** Les deux tiers
ne sont pas descendus — une grande part est du **spam de formulaire** (voir
`gender = 0` plus bas).

### La clé externe dit d'où venaient DÉJÀ ces fiches

```
193 394 fiches portent une external_key, TOUTES UNIQUES
préfixes :  c3_main_contact_               95 012
            c3_main_contact_sphere10..30   ~1 700 chacun (lots d'import)
```

⭐⭐ **IL N'Y A QUE DES `main_contact`.** Aucun `second_contact`, aucun `spouse`.
**Dès le logiciel « c3 », le conjoint n'était PAS une fiche.** Le problème du
couple ne vient donc pas de Hektor : il est hérité de deux systèmes en arrière.

### ⭐⭐⭐ LE COUPLE EST CODÉ DANS LA CIVILITÉ — c'est `gender`

```
gender 0  non renseigné      50 746   ⚠ dont beaucoup de SPAM de formulaire
                                        (noms de robots répétés)
gender 1  Monsieur           70 688
gender 2  Madame             52 967
gender 3  Mademoiselle        5 726
gender 4  M. ET MME          21 653   <-- COUPLE MIXTE
gender 5  deux hommes           175   <-- COUPLE
gender 6  deux femmes            90   <-- COUPLE
                             ------
      FICHES DE COUPLE       21 918
```

Les deux personnes sont **écrites à la main dans nom/prénom** :
« DUPONT | Marcel et Pierrette », « MARTIN | Alan/ Mélanie »,
« DURAND / LEROY | Raoul/ Sophia » *(exemples inventés)*.

**11 839 fiches portent un séparateur** (` et `, `/`, `&`, `EPOUX`) :

```
gender 4   9 143      gender 5    94
gender 0   1 462      gender 6    76
gender 1     596      gender 3    47
gender 2     421
```

⚠ **Donc le couple déborde de sa civilité** : 2 526 fiches portent deux
personnes sans être déclarées couple (gender 0, 1, 2, 3).

### Les doublons de l'ancien logiciel

```
par nom+prénom   18 082 clés en double -> 44 757 lignes  (max x90)
par email        12 696 clés           -> 28 384 lignes  (max x38)
par mobile       13 787 clés           -> 30 865 lignes  (max x43)
```

⚠ **Beaucoup est du bruit** : `NC|NC` x90, `EXPLORIMMO|.` x45, `.|.` x44,
`0000000006` x43, `no-replylib@gmail.com` x38. Le chiffre dit l'ampleur à
regarder, pas le nombre de vrais doublons.

---

## 2. LE TABLEAU DES RELATIONS — et il tranche une question d'un coup

```
50 202 relations · 13 961 affaires · 31 187 contacts · 0 supprimée

representative                   20 085   le mandant / vendeur
applicant                        15 831   l'acquéreur
representative_notary            10 233
applicant_notary                  4 000
representative_business_provider     43
applicant_business_provider          10
                                 ------
                            6 TYPES, ET PAS UN DE PLUS
```

⛔⛔ **AUCUN type « conjoint », « couple », « époux », « ménage ».**
Cette table lie un contact à une **AFFAIRE**, jamais un contact à un autre
contact. **L'ancien logiciel n'avait aucun moyen de relier deux personnes.**

➡ **Le couple n'existait QUE d'une seule façon : une fiche, une civilité de
couple, et deux noms tapés à la main.**

---

## 3. CE QUE HEKTOR A FAIT — mesure sur nos 62 387 contacts

### L'appariement de la civilité est quasi parfait

```
ancien logiciel   gender 4 (M. et Mme)   21 653
chez nous         civilite 'Mr./Mme'     21 393
écart                                       260  (= les non-migrées)
```

### Et le lien de couple n'existe QUE là

```
civilité      contacts   pointe sur SOI   pointe sur UN AUTRE
'Mr./Mme'       21 393          3 872            16 103
'M.'            12 419          8 558                 0
'(vide)'        27 065         11 314                 2
'M_Mme'            332            319                13
```

⭐ **Hektor n'attache un conjoint QUE si la civilité est un couple.**

### Les trois propriétés du modèle Hektor

```
1. LE LIEN EST À SENS UNIQUE
   0 réciproque sur 13 371. La cible pointe sur ELLE-MÊME (13 210).
   -> le conjoint NE SAIT PAS qu'il est en couple.

2. LE CONJOINT EST UNE FICHE DE PLEIN DROIT
   même nom de famille : 1 372 / 13 371 seulement (10 %)
   même civilité       : 2 136 / 13 371
   -> c'est une fiche individuelle ordinaire, avec son nom, ses coordonnées.

3. L'ÉCLATEMENT EST PROPRE
   un conjoint = un seul ménage : 16 121 sur 16 122 (un seul cas à 2)
   -> aucun conjoint partagé entre deux ménages.
```

### Les trois tas, et ils sont quasi exclusifs

```
A  ÉCLATÉES          ~16 100   fiche ménage + fiche conjoint + lien posé,
                               prénom de la fiche ménage NETTOYÉ
B  RESTÉES APLATIES    2 089   « Marcel et Pierrette » encore dans le prénom,
                               AUCUN conjoint, AUCUN lien
C  COUPLE SANS SECOND  3 872   civilité de couple, lien SUR SOI-MÊME
   + sans aucun lien    1 418
```

⭐⭐ **LA PREUVE QUE A ET B SONT EXCLUSIFS : seulement 6 fiches ont à la fois
les deux prénoms collés ET un lien vers un autre.** Quand Hektor a su séparer,
il a nettoyé ; quand il n'a pas su, il a laissé tel quel.

### Ce que nous avons perdu au passage

```
2 752 liens pointent vers une fiche ABSENTE de notre base
couple_role : 12 115 menage_resolu · 2 398 menage_orphelin · 1 610 lien sans rôle
```

⬜ **NON MESURÉ, et je ne le suppose pas** : ces 2 752 conjoints sont-ils
archivés chez Hektor, ou jamais descendus ? La réponse change le remède.

### ⛔ LES DOUBLONS SONT UN AUTRE CHANTIER — ne pas mélanger

```
sévérité   contacts   dont fiches ménage
critical      1 116          16
high          8 199          40
medium        1 460           5
low             377           2
           -------         ---
            11 152          63
```

**63 sur 11 152.** Les doublons ne viennent donc PAS de l'éclatement des
couples. Ce sont deux sujets indépendants.

---

## 4. CE QUE CET AUDIT APPORTE À LA DÉCISION SUR LES COUPLES

1. ⭐⭐ **HEKTOR NE FUSIONNE JAMAIS.** Il garde les deux fiches et pose un
   pointeur. ⚠ À rapprocher du défaut du 30/10 : notre geste
   « Transformer en couple » **a fait disparaître une fiche**. Nous allions
   dans le sens inverse du modèle.
2. **LE TROU DE HEKTOR EST LE SENS UNIQUE** : 13 371 fiches conjoint ignorent
   leur couple. Notre modèle doit rendre le lien lisible **des deux côtés**.
3. **5 290 couples n'ont pas de second** (3 872 sur soi + 1 418 sans lien) :
   la civilité dit couple, personne ne sait qui est l'autre.
4. **2 089 fiches sont encore aplaties, et elles sont séparables** : le
   séparateur est dans le champ. C'est le même geste que Hektor a réussi
   16 100 fois.
5. **2 526 fiches portent deux personnes SANS civilité de couple** (gender
   0/1/2/3) : elles échappent à tout repérage par la civilité.
6. ⛔ **NE PAS TRAITER LES DOUBLONS DANS LE MÊME CHANTIER** : 63 recouvrements
   sur 11 152.

---

## 5. CE QUI N'EST PAS MESURÉ

- le sort des **2 752 conjoints absents** (archivés chez Hektor ? jamais
  descendus ?)
- la signification exacte de `contact_type` (**270 combinaisons**, listes comme
  `[2, 24]` ; `[2, 2]` apparaît 2 031 fois — le même type deux fois)
- si les **1 610 liens sans `couple_role`** sont un défaut de notre calcul ou
  un cas de Hektor
- `mandats_extraits.xlsx` (36 Mo, même date) : **NON OUVERT**, hors de sa demande
