# C.2a — relecture de l'identité des contacts

Date : 2026-08-24. **Lecture et mesure seules. Aucune ligne de code écrite.**

Cette relecture reprend `AUDIT_IDENTITE_CONTACTS_2026-08-20.md`, qui s'était arrêté sur un
verrou explicite :

> *« 5b doit attendre que le sort de `contact_search_key` soit tranché. »*

**Il a été tranché le lendemain.** C'est le résultat principal de cette relecture, et il change
la nature de la tâche.

---

## 1. Le verrou du 20/08 est levé

Le 20/08, le dossier était pris entre deux mauvaises options :

| | |
|---|---|
| garder le hachage du numéro **Hektor** | un contact né après la coupure n'a pas de numéro Hektor → **pas de clé possible** |
| basculer sur le numéro de **l'app** | les 3 961 clés changent **en même temps** → tout ce qui y pend se détache |

La sortie était déjà nommée : *« cesser de hacher, faire de la clé une identité et non une
empreinte de contenu »*. **C'est fait depuis le 21/08.** Vérifié aujourd'hui :

```
   app_search_registry            76 880 paires, 76 880 noms figes, 0 doublon
   ecart table courante/registre  0
   fonctions Supabase touchant contact_search_key             27
   fonctions Supabase qui le FABRIQUENT                        0
```

**Un seul fabricant, local, et il consulte le registre avant de calculer.** Supabase ne fait que
lire et écrire une valeur qu'il reçoit.

> **Conséquence** : ajouter une colonne `app_contact_id` **ne peut déplacer aucune clé de
> recherche**. Ni par le contenu — figé. Ni par le numéro — `hektor_contact_id` ne change pas,
> on *ajoute*, on ne renumérote pas. Le sinistre que la note du 20/08 redoutait n'a plus de
> mécanisme pour se produire.

---

## 2. Le périmètre, remesuré — plus petit qu'il n'en a l'air

**18 tables** portent `hektor_contact_id` *(la note disait 17)*, plus **8 vues** qui suivront
seules. Comptages réels, pas des estimations :

| Table | Lignes | Porte déjà `app_dossier_id` |
|---|---|---|
| `app_contact_relation_current` | 77 393 | oui |
| `app_contact_current` | 57 553 | |
| `app_rapprochement` | 46 864 | oui |
| `app_contact_search_current` | 10 785 | |
| `app_search_count_high_water` | 9 680 | |
| `app_email_envoi` | 82 | |
| `app_proposition` · `app_google_calendar_event_link` | 11 · 11 | oui |
| `app_relance_rapprochement` · `app_bien_acquereur_statut` | 10 · 7 | oui |
| `app_console_deleted_contact_log` · `app_espace_visite_request` | 5 · 3 | |
| **6 tables vides** *(pending, override, consent, duplicate_member, espace_message, search_pending)* | **0** | |
| **TOTAL** | **202 404** | **8 sur 18** |

**Quatre tables portent 95 % des lignes. Six sont vides.** Le chantier réel, c'est *quatre
tables et quatre miettes* — pas dix-huit.

---

## 3. Les points de code — et le précédent qui rassure

| | `hektor_contact_id` | `app_dossier_id` *(le précédent)* |
|---|---|---|
| app (front) | 169 | **550** |
| Supabase | 145 | **440** |
| phase2 | 167 | **401** |
| backend | 92 | 141 |
| Console (worker) | 88 | 76 |
| **Total** | **701** | **1 711** |

La note annonçait ~530 ; c'est 701. **Mais le même geste a déjà été fait sur 1 711 points**,
pour les annonces, et il a tenu. Ce n'est pas un chantier sans précédent : c'est le même, à
**40 % de l'échelle**.

---

## 4. Les 11 fonctions ambiguës — l'ambiguïté se résout par la destination

`5a` — le renommage seul — a été **rayée le 20/08** : Postgres refuse le rename, l'appel se fait
par nom, et la compilation ne voit rien *(mémoire `renommer-parametre-rpc-supabase-piege`)*.
Il faut donc trancher autrement. Le classement par **ce que la fonction fait de son paramètre**
sépare les 11 sans ambiguïté :

| Famille | Combien | Destin du numéro |
|---|---|---|
| **A** — fabrique un travail pour le worker | **8** | **reste celui de Hektor**, à jamais. Le worker doit retrouver la fiche chez Hektor |
| **B** — écrit dans les tables de l'app | **3** | devient celui de l'app |

Famille B, en entier : `app_edit_contact_optimistic`, `app_edit_search_optimistic`,
`app_espace_edit_search_optimistic`. **Trois fonctions.** Les deux dernières viennent d'être
touchées par C.3 — elles sont déjà sous la main.

> La note disait « 6 fabriquent un travail ». **C'est 8.** Et il n'y a que **3** fonctions à
> faire basculer, pas 5.

---

## 5. La vraie difficulté — que la note du 20/08 n'avait pas vue

```
   app_contact_current.hektor_contact_id  =  CLE PRIMAIRE
```

**Pour les annonces, `app_dossier_id` existait déjà à côté du numéro Hektor.** Ici, le numéro de
Hektor **est** l'identité de la table. Ce n'est donc pas « ajouter une colonne » : c'est
**donner une seconde identité à la table maîtresse**, puis décider laquelle des deux fait foi.

Deux constats qui encadrent cette difficulté :

| | |
|---|---|
| **0 contrainte de clé étrangère** ne pointe `app_contact_current` | **mécaniquement, rien ne bloque.** Pas de cascade à combattre, pas de contrainte à démonter |
| **et c'est aussi la mauvaise nouvelle** | les 17 autres tables pointent le contact **par convention seule**. Rien n'empêche un orphelin, rien ne le signale. C'est exactement le terrain sur lequel `contact_search_key` a fabriqué 1 373 orphelins entre juin et août |

---

## 6. Ce qui reste ouvert — et qui n'appartient pas à C.2b

**Un contact né dans l'app, après la coupure, n'a pas de numéro Hektor.** Or le registre des
noms de recherche est indexé sur `(hektor_contact_id, search_index)`.

Ce n'est **pas** un obstacle à C.2b — qui n'ajoute qu'une colonne à des contacts qui ont tous
leur numéro Hektor. C'est une question de **C.9** *(la création part de l'app)*, et elle doit y
être nommée explicitement, faute de quoi elle sera découverte le jour de la coupure.

---

## 7. Recommandation sur la forme de C.2b

| | |
|---|---|
| **Faire** | ajouter `app_contact_id` aux **4 tables qui portent 95 % des lignes**, le remplir, le laisser vivre à côté sans rien basculer — **exactement la méthode de la doublure** : observer avant de commuter |
| **Ne pas faire** | changer la clé primaire de `app_contact_current` dans le même geste. C'est un second chantier, et il n'a pas à être simultané |
| **Les 6 tables vides** | y ajouter la colonne coûte zéro et évite d'y revenir |
| **Les 3 fonctions de la famille B** | ne les toucher qu'**après** que la colonne soit remplie et observée |
| **Durée revue** | la note disait « 1 à 2 semaines ». Avec le verrou levé, 4 tables au lieu de 18 et 3 fonctions au lieu de 11 : **3 à 5 jours** semble juste — à condition de ne pas y attacher le changement de clé primaire |

---

*Sources : mesure directe des trois supports le 24/08 · `AUDIT_IDENTITE_CONTACTS_2026-08-20` ·
`ETUDE_ORIGINE_CLE_RECHERCHE_2026-08-21` · mémoire `renommer-parametre-rpc-supabase-piege` ·
`app_search_registry` (76 880 lignes) · `pg_proc` / `pg_constraint` du projet
`dwaqxfrinihnychuoptk`.*
