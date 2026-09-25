# Audit — la vitrine publique et les deux systèmes de rendez-vous

*25/09/2026, signalé par Frédéric : « il y a un système indépendant pour l'affichage en
vitrine et la prise de RDV à partir d'un site GitHub, et aussi un système de prise de RDV à
partir des rapprochements via Google. Les deux doivent normalement rester indépendants de
Hektor, mais attention aux identifiants. »*

⚠ **Ces deux systèmes n'apparaissaient dans AUCUN de mes audits.** Ni le tableau objets ×
gestes, ni la liste des tâches, ni le plan ne les mentionnent. **Ils sont pourtant dans le run
de nuit**, comme deux étapes à part entière *(`backfill appointment public links` et
`android vitrine export and push`)*.

## 1. La vitrine GitHub — l'hébergement est indépendant, les liens ne le sont pas

Chaque nuit, le run exporte le catalogue et **le pousse sur GitHub** *(dépôt `gtiimmo`,
publié en `gtiimmo.github.io`)*. L'hébergement ne doit donc rien à Hektor : **c'est bien
indépendant.**

**Mais les liens qu'il fabrique, eux, portent le numéro Hektor.** Deux cas, et ils ne se
valent pas :

| lien fabriqué | forme | verdict |
|---|---|---|
| **la fiche visite (PDF)** | `https://gti-immobilier.fr/admin/pdf.php?…&idann={hektor_annonce_id}` | ⛔ **C'est HEKTOR lui-même qui produit le PDF.** À la coupure, **le lien meurt** — ce n'est pas un problème d'identifiant, c'est un service qui disparaît |
| **la prise de rendez-vous** | `https://gtiimmo.github.io/vitrine/rdv/index.html?ref={hektor_annonce_id}` | ⚠ la page est chez nous, mais **le `ref` est le numéro Hektor** |
| le QR code | construit sur l'URL ci-dessus | suit le même sort |

## 2. Le rendez-vous public — déjà à moitié prêt, et c'est une bonne surprise

Le paramètre `ref` **accepte déjà deux formes** *(`appointment_service.py`, l. 192-201)* :

```
ref n'est PAS un nombre  ->  c'est un JETON  ->  lecture par app_appointment_public_link
ref EST un nombre        ->  c'est le numero HEKTOR de l'annonce
```

Et la table des liens publics est **bien équipée** :

| | |
|---|---|
| liens publics | **2 227** |
| portant **notre** numéro de bien | **2 227 — soit 100 %** |
| portant un **jeton** | **2 227 — soit 100 %** |
| sans notre numéro | **0** |

➡ **Chaque lien a déjà un jeton et notre numéro.** Le chemin par jeton existe et fonctionne.

⚠ **Mais il retombe sur Hektor au dernier moment** : une fois le jeton résolu, le service
relit le bien par `hektor_annonce_id` *(l. 198)*. **Une annonce née dans l'app — sans numéro
Hektor — ne serait donc pas trouvée, ni par son numéro, ni par son jeton.** C'est exactement
le point que Frédéric signale.

## 3. Le rendez-vous depuis les rapprochements (Google) — le plus sain des trois

La table `app_google_calendar_event_link` porte **les deux numéros pour le bien comme pour le
contact** *(`app_dossier_id` / `hektor_annonce_id`, `app_contact_id` / `hektor_contact_id`)*.

| | |
|---|---|
| liens d'agenda | **11** |
| avec **notre** numéro de bien | **10** · aucun sous le seul numéro Hektor |
| avec **notre** numéro de contact | **8** · **1** encore sous le seul numéro Hektor |

➡ **Ce système est le mieux préparé.** Google est indépendant de Hektor par nature, et
l'identité est déjà traduite presque partout.
⚠ **Le 1 restant** est le lien vers le contact **603496**, qui n'existe nulle part — déjà noté
le 25/09, c'est un contact supprimé chez Hektor, pas un défaut de traduction.

## 4. Ce qu'il faut faire — et ce n'est pas gros

| | quoi | poids |
|---|---|---|
| **①** | **La vitrine fabrique ses liens de RDV avec le JETON**, pas avec le numéro Hektor. Le jeton existe déjà pour les 2 227 liens ; il suffit de l'exporter à la place. | petit |
| **②** | **Le service de RDV lit le bien par NOTRE numéro** quand il vient d'un jeton, au lieu de repasser par `hektor_annonce_id`. | petit |
| **③** | **La fiche visite PDF** : aujourd'hui produite **par Hektor**. À la coupure elle disparaît — il faudra la produire nous-mêmes *(l'app sait déjà fabriquer des PDF : estimation, cadastre, mandat)*. | moyen |
| **④** | Traduire le dernier lien d'agenda *(contact 603496)*, ou le marquer. | minuscule |

⚠ **ET UNE PRÉCAUTION QUI COMMANDE L'ORDRE** : ces liens sont **publics**. Ils ont été
diffusés par QR code, par mail, sur des affiches. **Changer leur forme ne doit pas casser ceux
qui circulent déjà** — il faut donc que l'ancienne forme *(numéro Hektor)* continue de
fonctionner tant que Hektor vit, et que la nouvelle *(jeton)* soit servie en parallèle.
**C'est un recouvrement, pas un remplacement.**

## 5. Non mesuré

- Depuis quand les liens **déjà diffusés** portent le numéro Hektor, et combien circulent.
- Si la vitrine expose d'autres liens vers Hektor que ces deux-là.
- Ce que devient le **QR code** d'un support déjà imprimé.
