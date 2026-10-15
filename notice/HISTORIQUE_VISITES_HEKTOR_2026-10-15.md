# L'historique des visites — **sujet à part, SORTI du chantier ⑥**

**15/10/2026 · audit en lecture seule, 0 appel à Hektor · statut : AUCUN TRAVAIL ENGAGÉ**

> **Décision de Frédéric, 15/10 :** *« Clôture le 6e, c'est un autre problème, rien à voir
> avec ce chantier. »* Le point **6e** du chantier ⑥ est donc **clos**, et le sujet vit
> désormais ici, seul. **Où il ira — un chantier, une note, jamais — est SA décision, pas la
> mienne.** Rien ne doit être relancé de soi-même.

Cette note est **autoportante** : elle contient toute la mesure, pour qu'une session future
n'ait pas à la refaire.

---

## 1. Le fait, mesuré

**L'agenda des visites de Hektor** *(qui a visité, quand, avec quel négociateur)* **n'est
importé nulle part.** Ce n'est pas une panne : c'est un périmètre **jamais ouvert**.

```
points d'entree Hektor que la descente lit          : 12  -> AUCUN agenda
familles d'API Hektor connues du projet             : 12
   Agence · Annonce · Contact · ExternalConnect · Lead · Mandat
   Negociateur · OAuth · Offre · Passerelle · User · Vente
   -> AUCUNE famille RDV / Visite / Agenda
tables du miroir local (data/hektor.sqlite)         : 38  -> AUCUNE de visites
```

Le chiffre de **« ~115 bons de visite par mois »** vient de l'audit du 07/10 et y est
lui-même marqué **« non remesuré »** *(`AUDIT_AUTONOMIE_COMPLET_2026-10-07.md`, l. 559)*.
**Il n'a jamais été vérifié.**

## 2. Notre propre système — une bonne et une mauvaise nouvelle

✅ **Le bon de visite est 100 % à nous.** `visitVoucherHtml` *(`apps/hektor-v1/src/App.tsx`,
~l. 38304)* fabrique un A4 imprimable **dans l'app**, avec la photo du bien et les
coordonnées de l'acquéreur ; **aucun appel à Hektor** *(la seule mention « Hektor » est une
étiquette imprimée : « Annonce Hektor : <n°> »)*.
⚠ **L'audit du 07/10 est donc PÉRIMÉ sur ce point** : il écrivait *« la fiche visite PDF de
la page RDV est fabriquée par Hektor (pdf.php) »* et classait ça **⛔ bloquant (C3)**. Ce
n'est plus vrai — à ne pas recopier.

⚠ **Mais il ne sert pas encore.** `app_google_calendar_event_link` *(mesure du 15/10)* :

| type | lignes | dont bon de visite prêt | période | depuis 30 j |
|---|---|---|---|---|
| `visite` | **10** | 9 | 02 → 15 juin 2026 | **0** |
| `autre` | 1 | 0 | 03 juin 2026 | 0 |

Construit, essayé en juin, **pas entré dans les habitudes**. Ce que décrit la note
`NOTE_AGENDA_RDV_QUALIFICATION_2026-07-31.md` reste vrai : *« les négociateurs saisissent
d'abord leurs rendez-vous directement dans Google Agenda »*, et l'app ne voit ces créneaux
que comme « occupés ». Cette note porte un **cadrage validé dont le développement n'a jamais
commencé** — le socle existe déjà *(table de liens qualifiée type/contact/bien, endpoints,
délégation Google Workspace)*, **il ne manque que l'ingestion Google → app**.

## 3. ⭐ LA TROUVAILLE : l'historique est déjà sur notre serveur

Comptage **des fichiers**, sur notre disque, sans toucher à Hektor :

```
bons de visite deja archives chez nous : 1 721   sur 1 182 annonces
   1 632 PDF · 80 JPG · 8 PNG · 1 DOCX
   -> LISIBLES EN TEXTE, gratuitement  : 1 089
   -> SCANS (OCR necessaire)           :   632
   -> illisibles                       :     0
```

C'est la **synchro des documents** qui les a rapatriés, sans qu'on le demande. Le texte
extrait d'un vrai bon porte le mot *visite*, l'*acquéreur*, le *mandat*, les *honoraires*,
le *téléphone* et la *signature* — **la matière d'un historique est déjà payée.**

⚠ **À ne pas confondre** : **814** documents nommés « Bon de Visite Groupe GTI » sur 276
annonces sont des **modèles Hektor** *(`metadata_json.modelo`, regénérés à la demande)* —
**pas** des visites réelles. Ils ne sont pas comptés dans les 1 721.

⚠ Et les bons déposés n'ont **aucune date Hektor** en base *(`created_at_hektor` est nul sur
les 2 794 lignes dont le nom contient « visite »)* : la date de la visite est **dans le
PDF**, pas dans la ligne.

## 4. Les trois chemins, et leur coût

| | ce qu'on obtient | coût | charge Hektor |
|---|---|---|---|
| **A — rien de plus** | les 1 721 bons restent consultables un par un sur la fiche du bien | **0** | 0 |
| **B — lire ce qu'on a déjà** ⭐ *(recommandé)* | une table d'historique *(date · bien · acquéreur · négociateur · le PDF d'origine)* bâtie sur les **1 089 lisibles**, les 632 scans marqués « à OCR » | **~½ journée** | **0 appel** |
| **C — ouvrir le carnet Hektor** | **toutes** les visites, même sans bon déposé | **~1 journée**, + un relevé d'exploration d'abord *(le point d'entrée est INCONNU)* | récurrente — ⚠ c'est la mécanique du **bannissement d'IP du 20/08** |

**Le premier pas de B est gratuit** : relire les 1 089 textes pour établir **quelle période
couvre cet historique et combien de visites par mois** — ce qui remplacerait enfin le
« ~115/mois » jamais vérifié. Aucune écriture.

**Ce que B pourrait casser ailleurs** : rien chez Hektor *(aucun appel)* · rien dans les
documents *(on les **lit** sur le serveur, on ne les déplace ni ne les supprime — règle « la
ligne ne disparaît jamais »)* · rien dans le run de nuit *(outil à part, lancé à la main)*.
La seule nouveauté serait **une table neuve**, et ⚠ **il faudrait sa politique RLS** pour
qu'un écran la lise *(leçon du 13/10 : une colonne posée en base ne remonte pas toute seule
à l'écran)*.

## 5. Ce qui reste à décider — et à personne d'autre que Frédéric

1. **A, B ou C**, ou rien pour l'instant ;
2. si **B** : fait-on d'abord la mesure gratuite *(vraie période, vrai rythme)* ;
3. **où ce sujet atterrit** : un chantier à lui, la fin de l'étape 2, l'étape 3.

➡ **Tant qu'il n'a pas tranché, ce sujet ne se relance pas.** *(Règle du projet : un
périmètre, une taille, un ordre ou un report ne se décident jamais sans lui.)*
