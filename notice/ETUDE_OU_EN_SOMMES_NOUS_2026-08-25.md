# Où en sommes-nous vraiment — étude du 25/08/2026

Deux questions de Frédéric, et j'y réponds par la mesure, pas par l'impression :

1. **Si tout le monde continue à saisir dans Hektor**, est-ce que l'app, le serveur et
   Supabase fonctionnent correctement ? Et qu'y a-t-il dedans ?
2. **Si je leur dis demain de tout saisir dans l'app**, est-ce que tout marche —
   Hektor sera-t-il correctement mis à jour ?

*(Cette étude est, de fait, la tâche **E.0** du plan.)*

---

# QUESTION 1 — tout le monde reste dans Hektor

## La réponse : oui, et sans réserve sérieuse

```
   52 sondes de surveillance
   49 OK  ·  3 avertissements  ·  0 CRITIQUE
```

Les trois avertissements sont mineurs et sans rapport avec le flux : **57 notifications sans
destinataire** et **863 non lues** *(seuils 20 et 300)*. Rien qui touche la donnée.

Et sur **54 737 travaux** exécutés par les workers depuis mai : **0 en erreur.**

## Ce qu'il y a dedans

### Le miroir de Hektor — 3,63 Go

| | |
|---|---|
| annonces | **56 896** |
| contacts | **355 687** |
| mandats | **24 125** |
| offres · compromis · ventes | **10 990 · 10 454 · 7 537** |

### Ton serveur — 4,05 Go, 151 tables

| | |
|---|---|
| annonces : identité **et contenu** *(130 colonnes)* | **56 899** |
| contacts : identité **et contenu** | **355 687** |
| recherches acquéreur | **76 889** |
| affaires *(offres, compromis, ventes)* | **28 981** |
| registre des mandats | **23 816** |
| rapprochements | **47 257** |

### Supabase — ce que l'app voit

| | |
|---|---|
| annonces actives *(+ leur détail)* | **13 209** |
| contacts | **57 557** |
| relations contact ↔ annonce | **77 382** |
| rapprochements | **47 257** |
| registre des mandats | **23 816** |
| recherches acquéreur | **10 793** |

## Ce qui circule chaque jour

```
   annonces modifiees dans Hektor  15 a 30 par jour
   contacts modifies               15 a 30 par jour
```

**C'est modeste**, et c'est un chiffre important pour la question 2 : c'est le volume que
l'app aurait à absorber, et il ne change pas selon l'endroit où on saisit.

## Les réserves, honnêtement

- **62 annonces** *(0,26 %)* ont un mandat que le registre ne porte pas — sans perte, la vue
  générale les a *(voir `NOTE_CHAINE_DES_MANDATS_2026-08-25`)*
- **36 fonctions Supabase** restent appelables sans être connecté — dette assumée de la tâche 0.7
- **le journal des doublures est plat à 45** depuis trois jours : *l'app ne produit presque rien,
  parce que personne ne s'en sert*

---

# QUESTION 2 — tout le monde bascule sur l'app demain

## La réponse : **presque, mais pas demain.** Quatre choses manquent.

Et il faut d'abord dire ce qui **marche**, parce que c'est beaucoup.

## Ce que l'app sait déjà écrire dans Hektor — et qui a été éprouvé

**31 types de travaux ont tourné, tous à 0 erreur :**

| Ce que le négociateur ferait | Éprouvé |
|---|---|
| modifier les champs d'une annonce | **66 fois**, dernier le 21/08 |
| modifier un contact | **20 fois**, le 21/08 |
| modifier une recherche acquéreur | **24 fois**, le 21/08 |
| **créer une annonce dans Hektor** *(via le wizard réel)* | **73 fois**, le 05/08 |
| créer un contact · un mandant | **8** · **16 fois** |
| déposer un document · une photo | **100** · **15 fois** |
| affecter un négociateur | **14 fois** |
| supprimer une annonce | **113 fois** |
| générer un mandat *(PDF + Hektor)* | **18 fois** |
| relancer / annuler une signature | 1 · 1 fois |

**Ce n'est pas une maquette.** Le chemin app → worker → Hektor fonctionne, et il n'a jamais
échoué.

## Ce qui manque VRAIMENT — les quatre points

### ① Il n'y a que 5 comptes actifs, dont **2 commerciaux**

```
   admin       3 actifs
   commercial  2 actifs
```

Tes portefeuilles montrent **une douzaine de négociateurs** *(Sylvie 2 181 annonces, Marion
1 878, Nicolas 1 522, Christèle 1 330, Arnaud 1 122, Nadège, Stéphanie, Tatiana, Mélanie,
Aline…)*. **Il manque une dizaine de comptes.**

### ② Le cœur du métier est **réservé aux admins**

```jsx
   onChangeAnnonceStatus = {isAdmin ? … : undefined}    // offre, compromis, vente
   onArchiveAnnonce      = {isAdmin ? … : undefined}
   onDeleteAnnonce       = {isAdmin ? … : undefined}
```

**Un négociateur ne peut pas passer une offre, un compromis ou une vente depuis l'app.**
C'est le geste le plus important de son métier, et il n'y a pas accès. *(C'est la tâche C.4.)*

### ③ La création de mandat n'a été éprouvée **qu'une fois**

`create_hektor_mandat_auto_number` : **1 exécution, le 28/07**. Le chemin existe et il a
marché — mais une fois. Sur un geste qui réserve un numéro officiel et irréversible chez
Hektor, c'est peu.

### ④ Six chemins n'ont **jamais** tourné

`link_hektor_mandant` · les quatre actions **Matterport** · `archive_cloud_documents`.

## Et ce que l'app fait EN PLUS de Hektor

Il faut le dire aussi : estimations, rapprochements acquéreurs, agenda, pilotage de la
diffusion, registre des mandats, cockpit du dossier — **Hektor ne fait rien de tout ça.**
La bascule n'est pas une perte, c'est un échange.

---

# ALORS, OÙ EN SUIS-JE ?

## Trois marches, et tu es sur la deuxième

```
   1. TOUT DANS HEKTOR (aujourd'hui)        -> fonctionne, 0 sonde critique
   2. TOUT DANS L'APP                        -> 4 manques, dont 1 seul est du code
   3. LA COUPURE                             -> portails + signature, a zero
```

## Ce qu'il faudrait pour franchir la deuxième — dans l'ordre

| | | Qui |
|---|---|---|
| **1** | **Créer les comptes** des négociateurs | toi, une heure |
| **2** | **Ouvrir le changement de statut aux négociateurs** *(offre, compromis, vente)* | moi — c'est **C.4** |
| **3** | **Éprouver la création de mandat** deux ou trois fois de plus | toi + moi |
| **4** | **T'en servir toi-même une semaine** avant de leur ouvrir | toi |

Le point **4** n'est pas une formalité : *tout ce qu'on sait de « l'app comme auteur » est
mesuré sur une app que personne n'exerce.* Le journal des doublures est plat à 45 depuis
trois jours pour cette raison.

## Ce qui te rassurera le plus

**Hektor sera correctement mis à jour** : le chemin app → worker → Hektor a exécuté
**54 737 travaux sans une seule erreur**, et le volume réel à absorber — 15 à 30 annonces et
autant de contacts par jour — est **dix fois inférieur** à ce que le worker traite déjà.

**Ce qui n'est pas prêt, ce n'est pas la plomberie. C'est la couverture fonctionnelle d'un
seul geste** — passer une offre, un compromis, une vente — **et les comptes.**
