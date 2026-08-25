# FEUILLE DE ROUTE — 24/08/2026, au soir

**16 faites · 20 restantes · 4 supprimées** · *C.2b et C.12 faites le 25/08*

*(la feuille du matin annonçait 21 restantes : le compte était faux d'une unité, recompté tâche par tâche le 24/08 au soir)*

> Remplace la feuille du 24/08 au matin, qui disait deux choses fausses :
> *« C.1' bloquée sur tes 3 arbitrages »* (elle ne l'était pas) et
> *« pendant l'étape 2 »* (rien n'attend que les gens bougent).
> La **liste** des tâches, elle, n'a pas changé.

---

## ✅ CE QUI EST FAIT — on n'y revient plus

**BLOC 0 · protéger l'existant**

| | | |
|---|---|---|
| ✅ | **0.1** | `app_search_registry` + `app_affaire_ledger` dans la sauvegarde de nuit · *22/08* |
| ✅ | **0.2** | la règle « le miroir ne se supprime jamais » · *22/08* |
| ✅ | **0.4** | fermer l'accès public à `app_dossiers_current` · *24/08* |
| ✅ | **0.5** | fermer les 5 vues de surveillance + `app_search_count_high_water` · *24/08* |
| ✅ | **0.6** | supprimer `tmp_etape12_avant` · *24/08* |
| ✅ | **0.7** | audit des fonctions publiques · **12 fermées** · *24/08* · ⚠ 36 restent ouvertes *(dette assumée)* |
| ✅ | **0.8** | le correctif d'une ligne : `and p.conflict = false` sur les 3 fonctions · *24/08* |

**BLOC B · le serveur apprend de l'app**

| | | |
|---|---|---|
| ✅ | **B.1** | la descente · 110 tables · *22/08* |
| ✅ | **B.2** | les doublures · 10 tables, 174 720 lignes · *22/08* |
| ✅ | **B.4** | le journal + l'alarme · *22/08* |
| ✅ | **B.5** | la tâche `GTI Descente` de 07:30 · *22/08* |

**BLOC C · l'app devient l'auteur**

| | | |
|---|---|---|
| ✅ | **C.3** | fermer la porte sortante des recherches · *24/08* |
| ✅ | **C.1'** | **« une saisie ne se perd jamais »** · *24/08* — purge des 24 h retirée, sortie de conflit, bandeau à deux causes, 4 sondes de plus |
| ✅ | **C.2a** | identité des contacts — la relecture · *24/08* |

---

# 🛤 PISTE 1 — LE CODE · **se construit maintenant, dormant · n'attend personne**

## 1 · C.2b — l'identité des contacts · ✅ **FAIT le 25/08**

`app_contact` locale : **355 687 numéros**, patron d'`app_dossier` à l'identique.
`app_contact_id` posée sur **19 tables** Supabase, **144 985 lignes remplies**.

**Vérifié** : 0 incohérence entre les tables, 0 numéro pour deux contacts.
**Non fait, et voulu** : la clé primaire n'est pas touchée, et personne ne lit encore la
colonne — c'est une doublure.

> ⚠ **Le chantier a révélé ce que le plan n'avait pas vu** : le registre doit se
> **maintenir**. Le jour même, 15 contacts créés la veille étaient déjà dans Supabase et
> pas encore en local. Il tourne désormais chaque nuit.
>
> ℹ **35 orphelins** trouvés au passage dans `app_search_count_high_water` — signalés,
> pas corrigés.

## 2 · C.12 — la sortie de conflit pour les **contacts** · ✅ **FAIT le 25/08**

`app_contact_edit_status` + `app_contact_pending_resolve`, et le bandeau à deux causes
posé dans **les deux versions** de la fiche contact.

**Vérifié** : les deux causes, les deux modes, les refus, l'archivage de la saisie.
État final 0/0 — rien laissé derrière.

> ✅ **Les recherches n'en avaient pas besoin** — tu l'avais vu, et c'est vérifié :
> C.3 a fermé leur porte, elles ne peuvent plus produire de conflit.
>
> ⚠ **Un défaut trouvé par l'essai, avant mise en service** : la trace lisait le numéro
> sur la ligne d'attente, que seule une ligne déjà rattrapée porte. Elle le résout
> désormais à la source.

## 3 · C.6 — le domicile de l'annonce · **1 à 2 j**

**Ce que ça fait.** La base locale ne contient de l'annonce que **10 colonnes d'identité** ; tout
le contenu vit dans le miroir. On crée les tables propres de l'annonce, plus les 36 champs
calculés à l'export.

**Pourquoi.** Sans ça, il n'y a **rien à réconcilier** à l'étape 4. Et le jour de la coupure, le
miroir disparaît — le contenu des annonces avec lui.

**Interrupteur :** qui **lit** la table. On l'écrit ; personne ne la lit encore.

## 4 · C.7 — le miroir devient un **témoignage** · **2 à 3 j**

**Ce que ça fait.** Ta phrase : *« le miroir de Hektor devient une source d'information »*.

```
   ce que dit le MIROIR  +  ce que dit L'APP (relu dans Supabase)
        -> on tranche  ->  on ecrit dans la base locale  ->  Supabase
```

**Pourquoi c'est le cœur.** Détecter un écart ne le résout pas : chaque nuit le serveur se
reconstruit depuis le miroir, donc **Hektor regagne par défaut — pas par décision, parce qu'il
est seul dans la pièce.** C.7 crée la pièce où l'arbitrage a lieu.

**Interrupteur : la liste des champs app.** Livrée **vide** = « Hektor gagne partout » =
**comportement identique à aujourd'hui**.

## 5 · C.8 — le calque disparaît · la barrière

Le calque *(l'affichage optimiste)* devient inutile une fois la base locale faisant foi. Et un
travail sans numéro Hektor **attend** au lieu d'échouer.

**Interrupteur :** le calque, côté front.

## 6 · C.9 — la création part de l'app · **1 à 2 sem.** · *après C.7*

Créer annonce ou contact **depuis l'app**, avec son numéro à elle, la case Hektor vide jusqu'à ce
que le worker rapporte la sienne.

**Le patron est déjà dans le schéma** — `app_dossier.id` en série propre, `hektor_annonce_id`
nullable. Il n'a **jamais servi** : 0 ligne sur 56 894.

**Interrupteur :** le drapeau, déjà posé et éteint.

## 7 · C.4 — les **16** workers *(et non 35)* · **2 à 3 sem.**

Rendre l'app capable de faire elle-même ce que le worker fait en pilotant Hektor : statut,
archiver/désarchiver, créer contact et mandant, **affectation du négociateur en dernier**
*(impersonation)*.

**Mesuré :** 16 workers, pas 35. Et **7 sur 34 marchent déjà sans Hektor**.

**Interrupteur : la même liste de champs** — c'est ici que se répondent les 3 réglages.

## 8 · C.5 — registre d'affaires et mandat des transactions · *indépendante*

Clé propre du registre d'affaires ; cesser de deviner le mandat **dans le HTML de Hektor**.

## 9 · C.11 — ménage des tables mortes

## 10 · E.0 — **que ne peut-on PAS faire dans l'app ?** · **½ j**

Croiser ce qu'un négociateur fait dans sa journée avec ce que l'app sait faire.
**En fin de piste**, parce qu'elle se nourrit de ton usage réel.

> **Total piste 1 : environ 6 semaines.**

---

# 🚶 PISTE 2 — LES GENS · **ne dépend que de toi**

**Maintenant, en parallèle :** *tu* passes sur l'app pendant qu'*eux* restent dans Hektor.

Ce n'est pas du confort. Le journal dit `app seule = 45`, **plat depuis 3 jours, parce que
personne n'utilise l'app**. Tout ce qu'on croit savoir de « l'app comme auteur » est mesuré sur
une app que personne n'exerce.

**Puis, quand tu veux :** ils basculent, **un par un**. Jamais les deux systèmes **pour la même
personne**.

| | | |
|---|---|---|
| ⏳ | **E.1** | **19-R2** — le rattrapage des recherches, **la veille de la bascule** · ⚠ dernière occasion |
| ⏳ | **E.2** | la bascule elle-même — *décision d'organisation, pas technique* |

> ⚠ **« Pas les deux en même temps » se lit PAR PERSONNE.** Les portefeuilles rendent ça tenable
> *(Sylvie 2 181 · Marion 1 878 · Groupe GTI 1 702 · Nicolas 1 522…)*. Le risque porte sur les
> **dossiers partagés** — et c'est ce que le journal verra chaque matin.

---

# ✂ PISTE 3 — LA COUPURE · **ne dépend pas de toi · À ZÉRO**

| | | |
|---|---|---|
| ⏳ | **A.1** | **Portails en nom propre** + reprise des ~350 annonces · *semaines à mois* |
| ⏳ | **A.2** | **Ton contrat de signature** *(Yousign)* · *semaines* |
| ⏳ | **A.3** | Registre de mandats en propre · *après A.1/A.2* |
| ⏳ | **D.1a** | **mesurer d'abord** le périmètre des documents · *1 h* |
| ⏳ | **D.1** | documents · à redimensionner |
| ⏳ | **D.2** | photos · 1 397 |
| ⏳ | **E.3** | les workers Hektor deviennent invisibles |
| ⏳ | **E.4** | le jour J |

> **Rien de la piste 1 ne rapproche la coupure.** A.1 et A.2 commandent la date.
> La piste 1 te rend **prêt**, pas **libre**.

---

# EN PARALLÈLE, SANS ORDRE

| | | |
|---|---|---|
| ⏳ | **0.3** | finir le rattrapage acquéreurs · ≈ 4 h 35 · *autre session* |
| ⏳ | **B.3** | le déclencheur · **en observation** — si le journal reste plat 3 semaines, **la tâche est inutile** |

---

# ✂ SUPPRIMÉES le 24/08

| | |
|---|---|
| ~~**C.1**~~ | l'arbitrage et ses 3 cas → le cas ③ disparaît quand personne n'ouvre Hektor |
| ~~**la notification de conflit**~~ | plus de conflit à notifier |
| ~~**C.10**~~ | le modèle « au moins » de la modale → sans objet après C.3 |
| ~~**5a**~~ | renommer les 11 paramètres → **rayée le 20/08**, Postgres refuse le rename |

---

# LE SEUL VRAI INTERRUPTEUR

*Elle existe déjà. Elle fait trois lignes. Elle marche.*

```
   phase2/sync/push_contacts_to_supabase.py:476
   APP_OWNED_CONTACT_FIELDS = ("birth_date", "birth_place", "marital_status")
```

Elles marchent **parce que Hektor ne connaît pas ces champs** — il n'y a rien à arbitrer.
**Côté annonce : aucune liste n'existe.**

> ❗ **Le jour de la coupure, Hektor n'existe plus : il n'y a plus rien à arbitrer, l'app gagne
> tout.** Donc `statut_annonce`, `negociateur_email` et les champs de mandat ne sont pas trois
> décisions de fond sur ton métier. Ce sont **trois réglages de transition, réversibles**, qui ne
> valent que pendant la cohabitation.
