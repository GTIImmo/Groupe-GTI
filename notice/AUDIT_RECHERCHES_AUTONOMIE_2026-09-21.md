# 🔎 LES RECHERCHES SERONT-ELLES AUTONOMES À LA COUPURE ?

**21/09/2026.** Question de Frédéric. Audit mené avec la règle du jour : **objets × gestes**,
toutes les cases remplies ou dites « non mesuré ». Lecture seule, rien n'a été modifié.

> **Réponse courte : presque.** Tout ce qui se fait *après* la création est déjà autonome et le
> restera. **Deux gestes passent encore par Hektor** — l'ajout et l'archivage, ce qui est la
> décision du 20/08 — et **un trou n'avait jamais été nommé** : le serveur ne sait pas tenir une
> recherche que le miroir ignore, alors que le filet existe pour l'annonce, le contact et la
> relation.

---

## 1. Le tableau, geste par geste

| Geste | Passe par Hektor ? | Autonome à la coupure ? | Mesure |
|---|---|---|---|
| **Créer** une recherche | **Oui** *(décision du 20/08 : l'ajout part chez Hektor)* | ❌ **Non** — la ligne réelle vient de Hektor | 5 créations depuis l'app |
| **Modifier** les critères | **Non**, depuis le 24/08 | ✅ **Oui**, et la saisie est protégée **à vie** | 0 saisie protégée aujourd'hui — jamais utilisé en réel *(dernier envoi à Hektor : 20/08)* |
| **Archiver** | **Oui** *(décision du 20/08, confirmée le 20/09 : envoi sans retour)* | ❌ **Non** en l'état | 3 archivages depuis l'app |
| **Supprimer** | Sans objet — Hektor ne sait pas supprimer une recherche, il archive | ✅ | — |
| **Rapprochements** | Non — calculés dans l'app | ✅ | 50 152 |
| **Propositions, relances, retours acquéreur** | Non | ✅ | 11 · 10 |
| **Numéro et nom de la recherche** | Non — registre à part, jamais vidé, nom figé | ✅ | 77 068 numéros, 0 sans numéro de contact Hektor |
| **Contenu de la recherche, côté serveur** | **Oui** — reconstruit chaque nuit depuis le miroir | ❌ **Non** — voir §3 | 11 369 actives |

---

## 2. Ce qui est déjà solide, et pourquoi

- **La modification n'part plus chez Hektor** *(C.3, 24/08)*. Sa ligne d'attente n'est jamais
  effacée : elle protège la valeur de l'app du run de nuit, **définitivement**.
- **Les critères se fusionnent** *(30/08)* : un critère posé dans Hektor que l'app ne sait pas
  produire est **conservé** au lieu d'être écrasé — 1 045 recherches sur 10 910 en portent un.
- **Le nom de la recherche est figé** *(21/08)* : il ne change plus quand les critères changent,
  donc rien ne se détache. C'est ce qui fabriquait les orphelins.
- **La case Hektor du registre est facultative** *(30/08)* : une recherche peut y vivre sans
  numéro Hektor.
- **Tout ce qui pend sous la recherche** — rapprochements, propositions, relances, retours,
  notifications — **est calculé et stocké dans l'app**, jamais chez Hektor.

---

## 3. Le trou, et il n'avait pas de nom

**Le serveur reconstruit la table des recherches chaque nuit à partir du miroir**
*(`build_contacts_layer`, `DELETE` puis `INSERT`, à partir du détail contact)*. Une recherche
**née dans l'app** n'a aucune ligne dans le miroir.

Le filet « le serveur tient ce que le miroir ignore » existe pour :

| Objet | Filet | Depuis |
|---|---|---|
| Annonce | `app_annonce_app_seule` | 26/08 |
| Contact | `app_contact_app_seul` | 21/09 |
| Relation | `app_relation_app_seule` | 21/09 |
| **Recherche** | **aucun** | — |

➡ **Tâche manquante, à nommer : `26bis-RECHERCHES`.** Même patron, même journée de travail que
les deux posées ce matin. À faire **tant que Hektor vit**, comme les trois autres.

**Aujourd'hui le risque est nul** : aucune recherche n'est née dans l'app sans passer par Hektor
*(2 lignes provisoires, toutes rattachées)*. Mais le jour où la création devient app-first — lot
L4 — ce filet devient indispensable, et il sera trop tard après la coupure.

---

## 4. Les deux gestes qui passent encore par Hektor, et ce qu'il leur faut

| Geste | Pourquoi il y passe aujourd'hui | Ce qu'il faut pour la coupure |
|---|---|---|
| **Créer** | Hektor exige qu'un acheteur ait une recherche avant un compromis ou une vente *(la qualification)*. C'est ce qui lui fait poser la typologie « acquéreur » | La création écrit **chez nous d'abord**, avec son numéro pris au registre ; l'envoi à Hektor devient un geste **sans retour**, comme l'archivage. **Lot L4** |
| **Archiver** | Utile à la typologie des transactions *(décision du 20/09 : on garde l'envoi, sans retour)* | La marque locale ne doit plus dépendre du succès du travail — sinon, sans Hektor, elle se relâche. **Petit correctif, à faire avec L4** |

---

## 5. Ce qui reste à surveiller, et qui n'est pas de la mécanique

- **La modale n'exprime qu'une douzaine de critères** sur la centaine que Hektor peut porter.
  Ce n'est pas une dépendance — c'est un confort à enrichir côté app, quand tu voudras.
- **Le rattrapage 19-R2** reste la **dernière occasion** de récupérer les recherches créées dans
  Hektor et invisibles dans l'app. Après la bascule des équipes, plus personne n'en crée là-bas.
- **La modification n'a jamais servi en réel** : 0 saisie protégée à ce jour. Le mécanisme est
  écrit et éprouvé en essai, pas par l'usage. Un essai de bout en bout reste à faire.

---

## 6. Verdict

| | |
|---|---|
| **Le cœur du métier acquéreur** *(critères, rapprochements, propositions, relances, retours)* | ✅ **Déjà autonome** |
| **L'identité** *(numéro, nom figé, registre)* | ✅ **Déjà autonome** |
| **La création et l'archivage** | ⚠️ À rendre app-first — **lot L4**, c'était prévu |
| **Le contenu côté serveur** | ❌ **Filet manquant** — `26bis-RECHERCHES`, à poser **tant que Hektor vit** |
