# L3 · chantier classeur · ㉑ quinquies · 22/11 soir — le patch accordé, les deux familles de copies, la mise de côté fabriquée

**Ton mot :** `C:\Hektor\mot_du_22_11_le_patch_accorde.md`.

**Rien n'est écrit en base, dans ton Sheet ni chez Hektor. Rien n'est poussé.** La mise de côté est fabriquée et répétée
sur une copie. Elle n'est pas jouée.

---

## 1. Le patch du journal : prêt à être contrôlé dès que tu l'as collé

À 22:20, puis à nouveau à 22:36, le patch n'était **pas encore collé** : la fonction est toujours 815e956f, et la colonne
`ancien_numero` est absente.

**Tes trois points se lisent par une seule commande**, en lecture seule :
`python -u -X utf8 phase2/checks/controle_patch_journal_en_production.py apres-collage`
1. **La répétition**, contrôle par contrôle : 9 sur 9, ou ceux qui manquent.
2. **La colonne, remplie** : les lignes de fusion et de scission d'avant le patch (190, comptées en production ce soir)
   portent toutes leur ancien numéro, et aucune n'est vide.
3. **L'empreinte de la fonction après le patch**, écrite en clair. Elle doit avoir quitté 815e956f… et être celle que la
   copie a donnée : e695bf7e….

Je l'ai essayée avant le collage : elle crie « le patch n'est pas collé » (code 1). C'est le témoin qu'elle ne dit pas
vert à tort.

**Demain matin, avant tout le reste**, une commande pour ton ordre (a) puis (b) :
`python -u -X utf8 phase2/checks/controle_patch_journal_en_production.py matin`
- **(a)** Les dossiers, comparés à la **photo prise ce soir à 22:21** (11 551 dossiers, 31 368 pièces, aucun dossier à
  deux numéros, journal à l'id 34 545). Chaque dossier disparu ou renuméroté doit être expliqué par une ligne de la nuit
  au journal. Sinon, c'est rouge, et on joue l'inverse tout de suite.
- **(b)** Les lignes neuves du journal : chaque fusion et chaque scission doit porter son ancien numéro, et il doit être
  juste (la naissance de l'uuid coupé ou absorbé).
- **(c)** Ensuite seulement : la mesure du matin, puis le passage.

## 2. La coupe « C5 aux portes » : gardée

Rien à ajouter : elle est dans `protocole_portes.py`, et le brouillon du passage 22 porte ses 4 morceaux.

## 3. Les deux familles : je te donne raison sur le geste, et je te contredis sur un cas, puis sur un autre

**J'ai jugé l'acheteur des deux côtés** : celui de ton classeur (la note posée avec la copie, lue avec les mots du gel),
contre celui des pièces de Hektor sur le même bien. Mais **pas sur le nom seul**, parce que le projet a déjà tranché ce
point, sur ton audit V2 du 19/11 : chez Hektor, le contact d'une transaction ment souvent, souvent celui de l'acheteur
précédent. « Une date au jour exact bat un nom seul » ; un nom différent fait douter, il ne prouve rien.

### Ta famille 1 : la cause est établie, et je le prouve pour chacune

- **1001482** (UTLG66LE, ta ligne 4131) : STAUFFER dans ton classeur, STAUFFER sur l'offre 5055 du 18/12/2019. Notre lot
  « table » l'a refusée le 11/11 à 18:21, ce qui a déplacé sa date.
- **1001563** (A07EC3DH, ta ligne 535) : GUERIN des deux côtés, et ta note de vente dit « FERNANDES/GUERIN ». L'offre 1876
  du 12/01/2024 a été refusée par la cascade puis réacceptée le 12/11.
- **1001580** (3S4ZWOFK, ta ligne 2388) : ⚠ **le nom ne correspond pas, et pourtant c'est la même transaction.** Ta ligne
  porte « Acquéreur DI FORTI ROLLAND, Vendeur CIMINO » : **les colonnes sont inversées**. Ta ligne voisine 4113 dit
  « Vendeur DI FORTI », et chez Hektor l'acheteur de l'offre 11958, du compromis 11956 et de la vente 11960 est CIMINO.
  Jugée sur le nom seul, elle serait tombée en famille 2.

### Ta famille 2 : deux cas, deux réponses, et aucun n'est celui que tu as lu

**1001561, bien 47557 : ton classeur a raison.** Une offre acceptée a bien existé pour cet acheteur, et c'est **nous**
qui l'avons fait passer à refusée.
- La copie n'est pas sur ta ligne de MAITRIAS. Elle est sur **ta ligne de MARTINEZ** (TRJ5Y59U, ta ligne 457, « Vente
  réglée », offre du 25/03/2024).
- MAITRIAS est l'acheteur précédent : ta ligne DAMOO7OU (ta ligne 3518, « Annulée »), avec son offre 23996 du 28/02/2024,
  refusée par Hektor, et son compromis 23993 du 26/03/2024, annulé.
- **Ta propre note de vente** (colonne G, sur la vente 23997) dit « BELLAN/MARTINEZ GAY- 44 600 € ».
- L'offre **23995, au contact GAY Frédéric**, est celle de ce ménage. Elle a été proposée et acceptée le 25/03/2024 à
  23:00, à **44 600 €, le prix de la vente**.
- **Où elle est passée : notre cascade l'a refusée le 11/11/2026 à 19:30:34**, et personne ne l'a réacceptée. Le refus
  l'a sortie de la chaîne de la vente, et sa date porte depuis le 11/11.
- Si Hektor porte MAITRIAS sur le compromis 23994 et sur la vente, c'est le contact de l'acheteur précédent qu'il a gardé
  (la règle du 19/11).

➡ **Par la mesure, 1001561 est une cicatrice de cause établie, comme la famille 1.** En plus, son offre a été refusée
à tort par notre cascade : le ménage a acheté. **Je ne l'ai pas touchée**, comme tu l'as dit. La remettre en famille 1,
et décider de l'état de 23995 chez Hektor, ce sont tes décisions.

**1001593, bien 28422 : ce n'est pas notre geste, c'est une préemption.** Ta note de vente (colonne G, sur la vente
14009) le dit, mot pour mot :
- « Mme M. OKUTAN Hamza et Güler ont été avertis » ;
- « 01.8 La locataire Liliane Matra a vu sa banque, elle peut acheter. Elle a envoyé son courrier et eu l'AR pour la
  préemption. »

L'offre acceptée du 28/06/2025 (14008, à 100 000 €) est donc celle des OKUTAN. MATRA, la locataire, l'a **préemptée** :
- elle n'a jamais fait d'offre à elle ;
- **son contact naît chez Hektor le 06/08/2025**, 39 jours après la date que ton classeur donne à « son » offre ;
- ton classeur date l'offre de MATRA du jour de l'offre qu'elle a reprise.

Notre cascade a bien refusé 14008 le 11/11 à 19:16, mais elle n'est pas la cause de la copie. Même avec la vraie date,
le lot l'aurait posée : la jumelle est sur une autre chaîne et au nom d'un autre acheteur.

➡ **1001593 reste en famille 2, « cause non établie »** au sens où tu l'entends : ce n'est pas notre geste. Je n'y ai pas
touché.

### Y en a-t-il d'autres ? Le compte par motif, sur les 190 copies

`phase2/checks/classeur_copies_par_motif.py`, en lecture seule. La sortie
`notice/CLASSEUR_COPIES_PAR_MOTIF_2026-11-22.csv` a une ligne par copie.
- **M1, une jumelle (même genre, même vraie date) au même nom : 4 copies.** Ce sont 1001482 et 1001563 (cicatrices),
  plus 1001480 (PAOLONE) et 1001520 (HALLAERT-THEYS), dont la date n'a pas été déplacée par nous.
- **M2, une jumelle à la même date mais à un autre nom : 20 copies**, que je sous-classe par des faits :
  - **2 sont le même acheteur, écrit autrement** : 1001580 (colonnes inversées) et 1001477 (« VAN ROSSUM » /
    « VANROSSUM ») ;
  - **2 sont nommées par une note de ton classeur** : 1001561 (le ménage MARTINEZ GAY) et 1001593 (la préemption) ;
  - **9 ont une jumelle tenue par une ligne sœur** dans le gel. Leur date est peut-être celle de la sœur : ce sont les
    acheteurs successifs croisés de l'audit du 18/11 ;
  - **7 n'ont rien d'autre que la date au jour exact**, et un autre contact : le cas du contact réutilisé, du 19/11.
- **M3, l'acheteur a une pièce de ce genre, mais à une autre date : 3 copies.**
- **M4, l'acheteur n'a aucune pièce de ce genre chez Hektor : 155 copies.** C'est le cas que le lot devait remplir.
- **M5, pas de nom lisible au classeur : 8 copies.**

**Ta famille 2 au sens strict** (une offre « Vente réglée » reproduite, qui n'existe pas chez Hektor pour cet acheteur) :
sur les 59 copies d'offres « Vente réglée », 3 seulement ont une jumelle au nom d'un autre. Ce sont 1001580 (même
acheteur, colonnes inversées), 1001561 (même ménage) et 1001593 (préemption). **Il n'y en a pas d'autre.**

**Au sens large** (toute copie dont la jumelle par la date est à un autre nom) : 20. Parmi elles, **17 ne touchent aucun
de nos gestes**. Ce sont les 15 compromis annulés, plus 1001474 et 1001477 : ils appartiennent à la famille des 25 de
l'audit du 18/11, toujours « à décider ».

⚠ Si l'on prend tes mots au pied de la lettre (« une offre acceptée qui n'existe pas chez Hektor pour cet acheteur »), il
faut ajouter les 51 offres « Vente réglée » du motif M4. Mais elles ne reproduisent rien : c'est précisément le vide que
le lot comblait.

## 4. La mise de côté de la famille 1 : fabriquée, répétée sur copie, NON jouée

**Ce que le retrait fait aux dossiers.** Le vrai chaînage a été rejoué sur une copie de l'image, sans les 3 copies :
- **dans la nuit telle qu'elle tourne aujourd'hui** (l'outil de coupe éteint) : **10 pièces changent de compagnie, sur 2
  biens.**
  - GUERIN et PAYSAC se réunissent : 1875, 1876 et 1878 passent de D2024-0477 à D2023-0541.
  - CIMINO et SOUDANI se réunissent : 11957 et 11959 passent de D2020-0601 à D2020-0214.
  - **Le retrait de 1001482 seul ne déplace rien.**
- **dans l'arrivée du protocole** (avec la coupe « C5 aux portes ») : **0 pièce, 0 étiquette.**

⛔ **Donc l'ordre n'est pas négociable : la coupe en production d'abord.** Le geste local le vérifie lui-même.

**Les numéros qui partent.** Les 3 copies sont seules sous un numéro né d'elles seules, à la scission du 18/11 à 06:34 :
D2019-0649, D2024-0505 et D2020-0607. Aucune autre pièce ne porte ces étiquettes, aucun avis ne cite ces numéros, et
aucun verdict du protocole ne s'appuie sur elles (0 étiquette, 0 pièce). Par ta règle 6, **le registre des cicatrices
garde leur ancien numéro**.

**Le geste, en deux côtés, comme le 18/11 :**
- **Supabase** : `supabase/patch_mise_de_cote_cicatrices_famille1_2026-11-22.sql`, avec son `_INVERSE` et sa
  `_REPETITION`.
  - Ses gardes : exactement ces 3 lignes, telles que mesurées (ligne du classeur, numéro, seules dans leur chaîne et
    sous leur étiquette), leurs jumelles à la même vraie date, et la table de garde qui n'existe pas encore.
  - Il met de côté **les lignes entières** (et leurs 3 notes) dans des tables de garde datées. Le registre
    `app_classeur_cicatrice_mise_de_cote` garde pour chacune sa jumelle, son ancienne chaîne, son ancienne étiquette,
    son ancien numéro et son pourquoi.
  - Il juge sa part : 0 reste, 3 gardées avec leur ancien numéro, et le témoin inverse (187 autres copies, 3 jumelles
    intactes).
- **Le registre local** : `phase2/checks/mettre_de_cote_cicatrices_du_local_2026-11-22.py`. Il est à blanc par défaut,
  avec `--verifier-avant` et `--pour-de-vrai`.
  - Il refuse si la coupe n'est pas en production, ou si Supabase porte encore les copies (avec un témoin positif).
  - Il met les lignes de côté dans une table de garde locale.
  - Il juge sa part : le total local doit être égal à celui de Supabase.

**Répété sur une copie**, avec le Postgres 17.6 local et les vraies colonnes du registre (53) et des notes :
- **le patch, joué tel quel, passe**, et sa répétition dit **7 oui sur 7** ;
- **l'inverse repose tout à l'identique** : registre et notes reviennent à leur empreinte d'avant ;
- **le témoin inverse est attrapé** : sur une copie dont le numéro a changé, le patch refuse et n'écrit rien ;
- rejoué une seconde fois, le patch refuse.

⚠ Une limite : le déclencheur des parties n'existe pas sur la copie. Les copies n'ont ni acquéreur ni mandant, il
n'aurait rien à faire.

**Essayé ce soir, en lecture :**
- `--verifier-avant` répond « PAS PRÊT » : l'outil de coupe est éteint et les 4 morceaux sont absents du fichier de
  production ;
- à blanc, le script voit que Supabase porte encore les 3 copies, et n'écrit rien.

**L'ordre, quand tu l'accorderas :**
0. la coupe des 4 lignes en production, à la fin du protocole ;
1. `--verifier-avant` ;
2. le patch SQL, puis sa répétition ;
3. `--pour-de-vrai`, le même jour, avant la nuit.

## 5. Ce qui ne change pas

- La colonne `date` n'est corrigée nulle part.
- Ton verrou tient, et les 225 lignes en attente restent un reste à vider.
- Rien ne se pousse.

## Ce qui attend ta décision

1. **Le patch du journal** : tu le colles. Je lance alors `apres-collage` et je te donne les trois points en clair.
2. **1001561** : la mesure la ramène à la cause établie (ta note de vente, le ménage MARTINEZ GAY, son offre 23995
   refusée par notre cascade). Je l'ajoute à la mise de côté de la famille 1, ou elle reste à part pour l'instant ? Et
   l'état de 23995 chez Hektor, c'est toi qui décides.
3. **1001593** (la préemption) : on la laisse telle quelle, ou tu veux une règle pour ce motif ?
