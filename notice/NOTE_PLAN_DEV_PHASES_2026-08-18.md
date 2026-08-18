# Plan de développement — révision 2 du 18 août 2026

**Remplace `NOTE_PLAN_DEV_PHASES_2026-08-17.md`.**
Artefact : *Plan de développement — Indépendance Hektor*.
Chiffres relevés en base le 18/08.

---

## Deux objectifs, dans cet ordre

1. **La rapidité** — l'app répond tout de suite ; un convoi unique part vers Hektor **2×/jour**.
2. **L'indépendance** — reconstruire ce qui disparaîtra le jour où Hektor s'éteindra.

La rapidité passe **avant** les chantiers d'indépendance (numéro de mandat, référentiels…) :
sans elle, personne ne bascule sur l'app. Personne n'abandonne un outil qui répond au quart de
seconde pour un outil qui fait patienter.

**Le moment est bon** : la mécanique d'écriture vers Hektor s'est stabilisée.
Taux d'échec sur les actions utilisateur : **15 % sur tout l'historique → 3,9 % depuis le 1er juillet**
(254 actions, 10 échecs). Les causes majeures d'avant (ex. `terrace_count`) sont corrigées ;
le dernier échec de modification de bien date du 30/06.

---

## Étape 1 — La réactivité *(le chantier principal)*

### 1a. Lister ce qui fait encore attendre *(audit)*
Certaines actions sont déjà instantanées (prix, fiche contact, recherche) ; d'autres bloquent
l'écran. Ranger les ~30 types d'action en trois cases : *déjà instantanée* / *peut le devenir* /
*doit rester immédiate*.

### 1b. Rendre instantané ce qui peut l'être
Créer un bien, changer un statut, affecter un négociateur, envoyer un document. **Rien à inventer** :
on étend le patron du calque optimiste déjà éprouvé.

### 1c. Le convoi 2×/jour *(le morceau délicat)*
Deux contraintes commandent :
- **L'ordre** — créer avant d'affecter, affecter avant de publier. Sinon Hektor refuse.
- **L'identité** — chaque écriture se fait au nom du négociateur concerné (impersonation `idUser`).
  Un convoi groupé doit donc **changer d'identité en cours de route**.

Méthode : trier par négociateur, puis par ordre logique dans chaque lot.
**Variante A puis B** : d'abord un passage quotidien qui rejoue dans l'ordre ; deux passages
une fois qu'il tourne sans surprise.

*Gain caché* : le login Hektor à froid coûte ~30 s, payées **à chaque action** aujourd'hui.
Un convoi ne les paie **qu'une fois par passage**.

### 1d. Ce qui reste immédiat *(exceptions assumées)*
- **Mandats** — numéro généré par Hektor, engagement juridique.
- **Diffusion portails** — une mise en ligne ne peut pas attendre 12 h.
- **Signature électronique** — le client attend son document.

---

## En parallèle, sans développement — les fichiers

Temps machine, pas temps de dev. Tourne pendant l'étape 1 sans la gêner.
**Seul chantier irréversible** : ce qui n'est pas rapatrié avant la coupure est perdu.

| Index | Annonces | Documents | Photos |
|---|---:|---|---|
| Actives | 13 212 | ✅ **terminé** | à faire |
| Archivées | 34 450 | à faire | à faire |
| Historiques | 8 802 | à faire | à faire |
| Brouillons | 403 | à faire | à faire |

- **21 136 documents, 100 % sur le serveur, 33 Go** — 772 Go libres.
- Photos : 1 355 rapatriées. Pour la plupart des biens, **l'inventaire des photos reste à
  constituer** avant tout téléchargement — deux opérations, pas une.
- Mesurer un échantillon avant de lancer les 34 450 archivées (les actives ont coûté 33 Go
  contre 25 estimés).

---

## Étapes 2 à 7 — L'indépendance

Critère d'entrée unique : **est-ce que ça disparaît avec Hektor ?**

2. **Référentiels** *(bloquant)* — agences, négociateurs, nomenclatures en tables app ;
   réconcilier les copies divergentes de types de bien.
3. **Numéro de mandat** *(bloquant)* — obligation légale ; l'app reprend la suite de la série.
4. **Fiche PDF + logo** — les QR codes vitrine pointent vers un site qui n'est pas à nous.
5. **Diffusion portails** *(à trancher)* — établir la liste exacte des données exigées, puis
   décider : remplacer ou continuer à alimenter Hektor. **Commande la date de coupure.**
6. **Signature** — audit court du circuit hybride avant toute estimation.
7. **Adresse** *(le jour J)* — voir `NOTE_ADRESSE_PRIVEE_NE_PAS_PERSISTER_2026-08-17.md`.

---

## Hors développement — les interrupteurs

Protéger les données saisies dans l'app **ne demande aucun code**. Envoi et import sont les deux
bouts du même tuyau : aujourd'hui une modification faite dans l'app part chez Hektor en quelques
minutes, et le run de nuit rapporte la même valeur — il la confirme, il ne l'écrase pas.
Le jour où l'on arrête de pousser, **on arrête d'importer**.

- **À la bascule** : couper l'import de nuit sur ce qui est devenu propre à l'app ; réduire le
  convoi à ce dont portails / numérotation / signature ont besoin.
- **Règle permanente** : ne rien retirer dont un automate se sert pour viser Hektor —
  `hektor_annonce_id`, `hektor_contact_id`, `idUser`, `search_index`, `base_snapshot`.

*(Les phases « app autoritaire » et « identité des recherches » du plan du 17/08 sont retirées du
développement : la première est un interrupteur, la seconde se résout seule. Travail engagé puis
annulé le 18/08 sur cette base ; les fichiers touchés ont été restaurés à l'identique du commit.)*

---

## Correctifs à prévoir — aucun bloquant

- **Ciblage des recherches acquéreur** — l'automate recompte les recherches sur la page Hektor et
  se trompe (11 comptées pour une seule). Seul l'index 0 tombe juste. **Aucun dégât** : les 29
  actions passées visaient toutes l'index 0. **Ne rien coder** — disparaît à l'étape 1c/bascule.
- Types de fichiers refusés par le cloud (223) ; sessions Hektor expirées en cours de run (29) ;
  une annonce sans document.
