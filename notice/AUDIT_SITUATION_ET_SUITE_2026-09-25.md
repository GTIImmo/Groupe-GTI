# Audit de situation — où en est le projet, et ce qui vient après

*25/09/2026 au matin, demandé par Frédéric : « audit de la situation et de mon plan de dev,
ensuite dis-moi ce qui suit, L5 ou e3, et si tu n'as rien oublié ». Lecture seule : plan,
liste, notes (y compris les 12 supprimées du git), mémoire, code, les deux bases.*

## 1. L'état, mesuré ce matin

| | |
|---|---|
| travaux (`app_console_job`) | **55 509 terminés, 0 en attente, 0 en erreur, 0 en conflit** |
| annonces visibles | 13 437 |
| sondes d'identité (annonce, contact, satellites) | **toutes à 0** |
| run de 3 h | 3 983 contacts, exit 0, **0 403** (2 les nuits précédentes) |
| run de 5 h | 05:00 → 06:55, exit 0 |
| réglages en base | 2, dont `c9_annonce_nait_dans_app` = **off** |

**C.9 est codé de bout en bout** : a, b, c, d, e1, e2, e3, f, plus D6, la seconde passe du
build et la retraduction des satellites. Il reste **trois gestes**, aucun n'est du code :
le contrôle de la nuit du 26/09, l'allumage de e3, la suppression des annonces d'essai.

## 2. Ce que le plan dit de la suite

`L0` à `L4` sont finis ou en voie de l'être. Restent **L5 → L9**, puis la coupure.

| lot | ce qu'il porte |
|---|---|
| **L5** | les gestes manquants : **102 champs d'annonce et 40 de contact créables mais jamais corrigibles** · modifier un mandat existant · photos (supprimer, réordonner, principale) · fusionner des doublons |
| **L6** | ce que Hektor fait remonter : **D.0** documents et mandats signés, état de signature, de diffusion, numéro de mandat |
| **L7** | les fichiers chez l'app (D.1a, D.1, D.2) |
| **L8** | exploitation et bascule (C.4-bis élargi, E.3, rattrapages, E.2) |
| **L9** | le registre électronique des mandats — ⚠ **se remplit depuis le miroir : à finir AVANT la coupure** |

## 3. Réponse : **e3 d'abord, L5 ensuite** — et ni l'un ni l'autre en premier

**e3 d'abord, parce que c'est une décision, pas un chantier.** Tout est éprouvé (essai réel
du 24/09, run de jour, descente, nuit). Le laisser éteint, c'est garder une pièce prouvée hors
service ; **quatre drapeaux dorment déjà depuis des semaines sans avoir jamais été allumés**
(mémoire `trois-pistes-independantes`). Coût : une ligne de SQL. Gain : chaque annonce créée
naît avec notre numéro, ce qui est l'objet même de l'étape 2.

**Mais le vrai premier, c'est `D.0`** — et il n'est ni dans L5 ni dans e3 :

> **La redescente des documents est arrêtée depuis le 23/08**, après le bannissement d'IP du
> 20/08. **Un document ajouté ou SIGNÉ chez Hektor n'arrive plus dans l'app depuis un mois.**
> La liste le marque **« BLOQUANT ÉTAPE 2 »**. La reprise est déjà **conçue** (empreinte de
> contenu + suivi de signature sur 242 annonces, derrière le frein anti-bannissement) : 1 à 2 j.

C'est la seule chose ouverte qui **dégrade l'app aujourd'hui, en silence**, et elle dure depuis
33 jours. L5 améliore le confort ; D.0 répare une perte de données en cours.

**Ordre proposé :** ① allumer e3 *(décision, 5 min)* · ② **D.0** *(1-2 j, avec la cadence
anti-bannissement)* · ③ L5, en commençant par les 102 + 40 champs.

## 4. Ce que j'avais oublié — treize points, dont trois sérieux

### Sérieux
1. **`D.0` — documents arrêtés depuis le 23/08** *(ci-dessus)*. **Je ne l'avais jamais remonté.**
2. **`A.1` portails et `A.2` signature : à zéro.** Aucun travail technique ne permet de couper
   Hektor tant qu'ils ne sont pas réglés, et **chaque semaine de retard s'ajoute intégralement
   à la date de coupure**. A.2 a en plus un versant étape 2 : l'app ne sait pas *lancer* une
   signature (le bouton ouvre Hektor) — soit un worker ImmoSign, soit une exception assumée.
3. **4 annonces actives restent invisibles dans l'app** : 63118, 63122, 62859, **62660 depuis
   le 10 juillet**. Mesurées le 23/09, jamais traitées. *(Sur les 7 d'origine, 3 sont revenues
   — 63120, 63123, 63124, en statut « Estimation ».)*
   ⭐ **Mesure complétée le 25/09, et elle change le diagnostic.** Le serveur local est
   **complet** : sur les 12 tables du miroir, **0 annonce ne lui manque** (61 277 comparées).
   Les 4 sont donc bien chez nous — `app_dossier` **et** `app_view_generale` les portent — mais
   **ne sont jamais arrivées dans Supabase**. Leur point commun : **aucun détail lu**
   (`hektor_annonce_detail` = 0), et **3 des 4 sont étiquetées brouillon** dans le miroir
   *(63118, 62859, 62660)* — donc écartées par conception, ce qui explique enfin leur silence.
   **Reste 63122** : non archivée, non brouillon, sans détail, absente de Supabase — la seule
   vraie anomalie du lot. ➡ le trou n'est **pas** « l'annonce n'arrive pas chez nous » mais
   « son détail n'est jamais lu, et sans détail elle ne part pas ». Chantier bien plus petit.

### Moyens
4. **`0.3` / 19-R1** : rattrapage des recherches arrêté le 23/08 ; ~270 recherches créées chez
   Hektor **invisibles dans l'app**. À faire **avant E.2**.
5. **`3.5`** : l'essai réel de suppression d'une transaction n'a jamais été fait.
6. **`26bis-TRANSACTIONS`** : une transaction née dans l'app sans numéro Hektor n'a **jamais
   été éprouvée** — c'est un essai, pas du code.
7. **`C.9-couple`** : on ignore toujours si Hektor crée **une** fiche ou **deux** pour un couple.
8. **`C.13-c`** : 23 715 dates de clôture à rattraper, règles déjà validées.

### Petits, notés en passant ces deux jours
9. **9 liens de propriété** pointent vers 6 biens que Hektor ne connaît plus *(trouvé ce matin)*.
10. **1 lien d'agenda** pointe vers le contact 603496, qui n'existe **nulle part** — ni identité,
    ni cible. Ce n'est pas un reste de la bascule : c'est un contact supprimé chez Hektor.
11. **C.16 et le registre se contredisent** : 7 658 marques « absent » levées puis reposées
    chaque nuit, ce qui réécrit la date.
12. **17 fiches contact** sous leur identité n'ont pas de `app_contact_id`.
13. **Écrans** : le compteur de l'annuaire lit un instantané du 06/06 · 9 compteurs de filtre
    répondent 503 · 2 contacts provisoires du 18/09 restent affichés · l'alarme « critères
    différents : 1 » est la fiche d'essai TEST CHAINE 25-08.

## 5. Ce qui attend une décision de Frédéric

- **e3** : allumer la création d'annonce sous notre numéro.
- **Les annonces d'essai** 63146 et 63147, à supprimer chez Hektor.
- **L5** : fusion de doublons, suppression d'annonce, reprise d'un brouillon — dans l'app ou
  réservé à l'admin ?
- **A.2** : worker ImmoSign, ou exception assumée à l'étape 2 ?
- **RDV et visites** *(tout est construit, presque rien n'est utilisé)* · **le rapprochement
  automatique** *(mode, seuil, RGPD, relances)* · **E.2, qui passe en premier**.
