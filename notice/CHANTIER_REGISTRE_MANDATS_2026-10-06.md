# CHANTIER — le registre des mandats *(note de memoire, 06/10/2026)*

> **A quoi sert cette note** : la session du 05 et du 06/10 a produit beaucoup de
> mesures et **cinq corrections de mes propres affirmations**. Tout ce qui suit est
> MESURE. Les chiffres que j'ai annonces puis retires sont nommes, pour qu'on ne les
> ressorte pas.
>
> **Rien n'est lance.** Le LOT 0 attend le « vas-y » de Frederic.

---

## 0. CE QUI EST DEJA FAIT ET DEPLOYE

```
e060bb5  (pousse le 06/10, Vercel deploye, applique par le run de la nuit suivante)
   view_generale.py  mandat_montant : COALESCE(src.prix formate, m.montant)
                     mandants_texte : COALESCE(proprietaires_resume, m.mandants_texte)
   App.tsx:4447      mandat_montant RETIRE de la chaine des HONORAIRES
```

**Pourquoi le 3e n'etait pas optionnel** : en remplissant `mandat_montant`, les deux
premiers auraient fait passer de **87 a 3 310** le nombre de PDF imprimant le prix du
bien dans la case « honoraires d'agence ».

**Eprouve** : SQL prepare par SQLite sans erreur · 4 temoins basculent du faux au juste
(61693 `140 000 -> 365 000` THEVENOT -> TOUBI · 61811 `95 000 -> 71 000` · 39707
`62 000 -> 112 500` · 62055 `69 500 -> 139 500` GRANGE -> MIQUEL, **confirme par l'API
de Hektor elle-meme**) · mandants : 24 244 changent, **97 conservees par le COALESCE,
0 perdue** · honoraires : 87 -> 0 · `npm run build` OK.

⚠ **C'est une marche, pas la destination** : le `COALESCE` vers le bloc proprietaires
de Hektor disparaitra au profit de nos relations (LOT 1).

---

## 1. LA CAUSE RACINE, ETABLIE

### a) Les corps empruntes — ce n'est PAS notre code

Le referentiel mandats de Hektor est **gele au n° 18339 / 30-01-2026**. Ses **trois**
routes s'arretent ensemble (`ListMandat`, `MandatById`, `MandatsByIdAnnonce`) --
documente le 21/07 dans `sync_raw.py` et `refresh_single_annonce.py`, **verifie par
appels reels** (n° 18299 encore servi, n° 18549 vide).

Au-dela de ce numero, deux cas, mesures sur 454 lignes :

```
363  Hektor ne trouve AUCUN enregistrement
     -> pas de montant (champ STOCKE), mais il DERIVE encore les mandants des
        proprietaires de l'annonce -> noms justes, montant VIDE
 88  l'identifiant nu tombe sur un VIEUX mandat (les ids PROTEXA repartent de 1,
     453 des 469 collisionnent) -> Hektor sert le CORPS ENTIER du vieux mandat :
     montant ET mandants d'un AUTRE bien
```

**Un seul appel, sur l'ID ANNONCE** : `GET /Api/Annonce/AnnonceById/?id=<idAnnonce>`,
dont la reponse porte 21 blocs. **Nous n'appelons jamais rien avec un id de mandat.**
La resolution fautive se fait **chez Hektor, avant l'envoi** -- prouve quatre fois :
l'archive brute `raw_api_response` contient deja le mauvais corps ; le miroir le
reproduit a l'identique (454/454) ; le bloc `proprietaires` de la MEME reponse nomme
quelqu'un d'autre (88 cas) ; et `mandat_infofi.prix` de la MEME reponse donne le vrai prix.

⭐ **Hektor se contredit lui-meme** : annonce 61693, un seul document ->
`mandats[]` dit « THEVENOT / 140 000 », `mandat_infofi.prix` dit 365 000,
`proprietaires[]` dit « TOUBI ».

### b) Les mandants manquants — ca, c'est NOTRE code

```sql
-- LE REGISTRE DES ANNONCES (view_generale)
mandants_texte : COALESCE( m.mandants_texte , det.proprietaires_resume )
                                              ^^^ UN RECOURS, et il sauve 255 lignes
```
```python
# LE REGISTRE DES MANDATS (mandat_ledger._poser)
_texte(courante.get("mandants")) or _texte(_du_plat("mandants_texte"))
#       ^^^ le bloc mandats         ^^^ LE MEME bloc, forme plate
#       DEUX recours, et les DEUX puisent au MEME bloc. AUCUN vers les proprietaires.
```

**Chronologie de la faute** : le 21/07 on retire `MandatById` (le gros trou : il
ECRASAIT numero, type, dates et montant par ceux d'un homonyme -- **310 des 392
mandats recents y etaient exposes**). Le 29/09 on cree `app_mandat`, et son commit dit
juste : *« Le registre lit le detail. LA TABLE DOIT LIRE LA MEME CHOSE. »* -- **mais la
VALEUR du registre ne vient pas de la source seule, elle passe par le COALESCE de la
vue.** La table a copie la SOURCE, pas la RECETTE. D'ou 255 lignes plus pauvres.

⭐ **Les deux symptomes de Frederic -- des noms faux et des noms manquants -- sont les
deux faces d'un seul `COALESCE` : mal ordonne dans la vue, absent dans app_mandat.**

---

## 2. LE PERIMETRE REEL — 715 lignes, pas 2 777

```
  457  corps empruntes (montant ET mandants d'un autre bien)      -> A REPARER
  258  nature=VENTE, origine=detail, sans mandant                 -> A REPARER
   29  LOCATION/INCONNUE/GESTION origine=detail                   -> a trancher
2 073  LOCATION / INCONNUE, origine=annonce                       -> RESTENT EXCLUES
                                              (decision de Frederic du 26/08)
   40  personne ne connait leurs mandants                         -> LISTE a corriger
```

⚠ **Correction de Frederic, 06/10** : j'annoncais « 2 320 trous a combler ». **Faux** --
ce sont des LOCATIONS et des natures inconnues lues sur l'index, deja ecartees par sa
decision. Le perimetre est **715**.

---

## 3. ⭐ CE QUI MARCHE DEJA, ET QU'IL NE FAUT PAS « REPARER »

```
les 39 annonces a PLUSIEURS mandats :
   29  mandants DIFFERENTS par mandat   ->  DEJA JUSTE
   10  le meme mandant                  ->  NORMAL (renouvellement)
    0  aucun mandant
```

**`_poser()` lit `courante.get("mandants")`** -- l'entree de CE mandat dans
`mandats_json`, pas les proprietaires du bien. `app_view_generale.mandats_json` porte
l'historique complet : 13 cles par entree (id, numero, type, debut, fin, cloture,
montant, mandants, note, avenants, CartePro, duree_irrevocabilite, taciteReconduction),
et **37 des 39 ont leurs propres mandants par entree**.

Le registre des ANNONCES, lui, n'a pas le probleme : sur les 39, il montre **le plus
recent 36 fois**, **0 numero etranger, 0 melange de date, 39/39 mandants coherents avec
le mandat affiche**.

⚠ **Et j'avais invente un « trieur » pour un probleme qui n'existe pas.** Le risque
« tous les proprietaires du bien » n'existe QUE sur l'intersection :
**48 lignes sur 715** (une ligne en recours, sur une annonce a plusieurs mandats).
Le trieur devient donc une **option mesuree**, pas une piece du chantier.

---

## 4. POURQUOI `app_relation` ET PAS LE BLOC DE L'ANNONCE

**Argument decisif, et c'est celui de Frederic, pas le mien :**

```
le bloc « proprietaires » de l'annonce :  100,0 % d'identifiants HEKTOR (17 297/17 297)
app_relation.app_contact_id            :  100,0 % d'identifiants A NOUS (132 697/132 697)
```

Lire le bloc directement **reintroduirait les identifiants de Hektor** -- exactement le
bug corrige le 30/09 par `93cc01b` -- **et defairait le geste « retirer un mandant »**
(en service depuis le 03/10, `retire_le` + `retire_par`).

⚠ **Mon argument de couverture etait faible et je le retire** : le bloc couvre 98,0 %
des annonces du registre, nos relations 99,9 %. L'ecart est de 459, dont **451 =
annonces dont NOUS n'avons aucun detail** (toutes archivees ; le detail d'une archive
n'est rapatrie qu'a la demande). **Hektor n'oublie pas les proprietaires des biens
vendus** : il les sert encore sur 98 %.

⭐ Et `app_relation` **n'est pas une autre source** : c'est le bloc `proprietaires`,
extrait par `build_contacts_layer.py`, **conserve** (delete-never) et dote de nos
numeros. 132 697 liens contre 50 236 dans le cloud -- *82 386 liens qu'un bien vendu
emportait*.

⭐ **Et le registre des mandats est le plus avance du projet sur l'identite** :
`mandants_json` porte **les deux numeros** (`{"app_contact_id": 10002776,
"hektor_contact_id": "5509", "nom": "..."}`), alors que les trois index d'annonce et
`app_dossiers_current` ne portent **AUCUNE** colonne de contact.

---

## 5. LE PLAN, PAR LOTS

### LOT 0 — le filet, AVANT tout *(code NEUF, ne touche a rien)*
```
0a  un controle qui lance le VRAI push_single_annonce_to_supabase.py sur une annonce
    temoin, a chaque changement de export_app_payload.py
    -> aurait EMPECHE la panne du 05/10 (9 h de silence, 13 echecs, aucune alerte)
    -> lecon `eprouver-c-est-executer-le-code` : ma fonction avait ete « prouvee »
       trois fois, toujours par le chemin qui pose row_factory
0b  une sentinelle : alerte des 2 echecs consecutifs de refresh_console_data
0c  brancher les 3 sentinelles mandat ECRITES ET JAMAIS LANCEES
    (mandat_corps_recopie · mandat_disparu · registre_depuis_app_mandat : 0 occurrence
     dans le pipeline)
```
C'est aussi le **n° 2 et le n° 1** de la note de la session « Biens invisibles ».

### LOT 1 — les mandants du registre des mandats
```
OU  phase2/sync/mandat_ledger.py , _poser()
  ①  SON entree a des mandants ET le corps n'est pas suspect -> on garde  (24 022)
  ②  SINON, et SEULEMENT si nature = VENTE -> NOS relations                  (715)
  ③  si nos relations ne savent pas -> VIDE + sortie en LISTE                 (40)
  ⚠ LOCATION / GESTION / INCONNUE : on ne touche a rien
  OPTION : le trieur sur les 48 lignes de l'intersection (ECARTE, n'AJOUTE jamais)

⚠ DEPLACEMENT DANS LE RUN : aujourd'hui l. 839 app_mandat PUIS l. 922 app_relation
  -> deplacer app_mandat APRES app_relation.
  VERIFIE : rien entre les deux ne lit app_mandat (relation_ledger ne le cite que
            dans ses commentaires). Sans effet de bord.
```

### LOT 2 — le montant et le prix
```
2a  le FRONT lit le prix dans l'index de l'annonce (actif -> archive -> historique)
    mesure : 24 313 / 24 491 trouves = LA COUVERTURE ACTUELLE, 1 seule divergence
    100 % des 24 452 annonces du registre sont dans au moins un index, 0 orpheline
    ⭐ l'ecran fait .select('*') -> aucune requete ne casse
2b  l'export cesse de poser montant et prix dans le registre
2c  les colonnes tombent, local puis Supabase, avec re-GRANT
⛔ JAMAIS 2c avant 2a : un select= nommant une colonne absente fait echouer TOUTE
   la requete en PostgREST (mesure du 06/10)
```

### LOT 3 — la derniere porte ou NOUS utilisons l'identifiant
```
normalize_source.py , upsert_mandats()
   relation_items[mandat_id]  ->  relation_items[(annonce, numero)]
le code le prescrit lui-meme. Sa « limite connue » visait 1 cas en juillet :
il y a 483 identifiants partages aujourd'hui, et 19 lignes dans la zone a risque.
```

### LOT 4 — les archives sans detail
```
452 annonces du registre sans AUCUN detail -- toutes ARCHIVEES
371 lignes sans date de mandat (origine='annonce')
⚠ PAR PETITS LOTS : c'est ce geste qui a fait bannir l'IP
   (memoire `rattrapage-documents-bannissement-ip`)
```

### L'ORDRE
```
LOT 0 -> LOT 1 -> LOT 2a -> LOT 3 -> LOT 2b -> LOT 2c -> LOT 4
```
**LOT 1 avant LOT 2** : tant que `app_mandat` porte de faux mandants, faire lire la vue
depuis lui deplacerait le defaut au lieu de le corriger.

---

## 6. CE QUI RESTE DEHORS

```
⬜  40 lignes dont personne ne connait les mandants
⬜   2 annonces sur 39 ou une entree n'a pas ses mandants
⬜   1 cas HUMAIN : mandat n° 17842 de l'annonce 41629 -- deux CHARBONNIER, deux
    montants (59 000 / 53 000), meme date. Le registre a pris Annette / 53 000,
    rien ne prouve que c'est le bon.
⬜  2 numeros brules chez Hektor : 63073, 63132
⬜  le defaut de Hektor continue : ~60 lignes/mois. MAIS depuis septembre elles
    arrivent en montant VIDE, plus jamais emprunte (41 % en mars -> 0 % en septembre),
    et apres le LOT 1 elles recoivent leurs mandants seules, sans intervention.
⬜  DETTE notee : le cote annonce ne porte AUCUN numero de contact. Pour des mandants
    cliquables depuis la fiche annonce, il faudra y poser l'equivalent de mandants_json.
```

---

## 7. LES CINQ CHIFFRES QUE J'AI ANNONCES PUIS RETIRES

> A ne pas ressortir.

```
« 2 320 trous a combler »        -> des LOCATIONS, deja ecartees. Le perimetre est 715.
« 35 fusions de mandat »         -> mesure sur hektor_mandat qui ACCUMULE. La source
                                    du registre n'en porte que 4, dont 1 douteux.
« 87 % puis 94 % de collision »  -> calcule sur la colonne `famille`, qui est une
                                    HEURISTIQUE sur le libelle de type, pas une lecture.
                                    Refait sur les dates : 453 / 469 = 97 %.
« le numero est par agence »     -> vrai AVANT ~2015 seulement. Au-dessus de 18 000 :
                                    0 doublon de numero.
« famille est un artefact »      -> FAUX. Elle capte une vraie signature de systeme :
                                    HEKTOR = codes SIMPLE/EXCLUSIF/ACCORD,
                                    PROTEXA = phrases francaises. Et la bascule VENTE
                                    est datee : HEKTOR s'arrete 2026-02, PROTEXA
                                    demarre 2026-01.
```

⚠ **Et la lecon de methode, payee trois fois en deux jours** : *mesurer sur la BONNE
source*. `hektor_mandat` accumule, `mandats_json` dit le present, la colonne `famille`
devine. Trois fois j'ai conclu sur la mauvaise.
