# LA LISTE DES CASES À CRÉER — 09/11/2026

**Demandé par Frédéric** : *« Donne moi la liste des cases. »*

**LECTURE SEULE.** Rien n'a été créé. Cette liste est ce qu'il faut qu'il valide.

---

# 0. LA RÉPONSE EN HAUT DE PAGE

```
UNE TABLE A NOUS, 7 CASES   les 7 champs de suivi du classeur
TROIS COLONNES              date_annulation_app . motif_annulation_app
                            numero_mandat_app
----------------------------------------------------------------------
SOIT 10 CASES EN TOUT, et le patch de la table est DEJA ECRIT (ce matin).
```

⛔⛔ **ET UNE CORRECTION DE CE MATIN, QUI COMPTE.** J'ai écrit que
`app_registre_champ_app` suffisait et qu'il n'y avait **aucune table à créer**.
**C'est faux**, et je l'ai mesuré ce soir en ouvrant enfin ses contraintes.

---

# 1. ⛔ POURQUOI `app_registre_champ_app` NE CONVIENT PAS

Mesuré en base ce soir — ce que je n'avais pas fait ce matin :

```
CHECK (objet = ANY (ARRAY['societe','agence','personne']))   <- « dossier » est REFUSE
objet_id   bigint                                            <- ni D2026-0431 ni un UUID
PRIMARY KEY (objet, objet_id, champ)
RLS        lecture reservee a is_app_admin()
ET QUATRE FONCTIONS la lisent :
    app_negociateur_registre_maintenir   <- tourne CHAQUE NUIT
    app_registre_poser
    app_registre_ecrire_champ
    app_registre_rendre
```

➡ **Cette table appartient au registre des négociateurs, agences et personnes.**
Pour y ranger les champs du classeur, il faudrait élargir son CHECK, changer le type
de sa clé, et **toucher quatre fonctions dont une qui tourne la nuit** — pour un besoin
qui n'a rien à voir avec elle.

⚠ **Et `app_affaire_champ_app` ne convient pas non plus**, pour deux raisons mesurées :
sa clé est `(app_affaire_id, champ)`, donc **par transaction et non par dossier** ; et
c'est le carnet dont le ménage efface les affaires mortes *(`ETATS_MORTS`)* — une date
d'annulation y serait **effacée par le ménage lui-même**.

✅ **Donc le patch que j'avais écrit ce matin,
`supabase/patch_affaire_suivi_2026-11-09.sql`, est la bonne réponse** — et il l'était
depuis le début. Mon « ne pas l'appliquer » était l'erreur.

⭐ **Et sa clé est déjà la bonne** : `id_unique`, la ligne du classeur, gelée et
immuable. Pas `app_chaine_id`, que la règle du 28/10 interdit.

---

# 2. LISTE A — LES 7 CHAMPS DE SUIVI
### une seule table, `app_affaire_suivi`, une ligne par ligne du classeur

```
col  nom au classeur       rempli au classeur      la case chez nous           type
---  -------------------   ---------------------   -------------------------   ----------
Y    Vente Reglee          3 265 des lignes relie  date_vente_reglee           date
AA   Numero de facture     3 242                   numero_facture              text
F    En attente de         3 089 . 944 distinctes  en_attente_de               text
G    COMMENTAIRES          4 120 . 2 598 distinct  commentaires                text
AH   Avis a envoyer        2 255                   avis_a_envoyer              text
AI   Commentaire Avis        392                   avis_commentaire            text
AJ   Avis envoye           2 401                   avis_envoye                 text
```

⚠ **Lire ces volumes avec leur dénominateur.** Y et AA sont comptés sur les 3 985
lignes du rapport des écarts ; les cinq autres sur le classeur entier (4 773 lignes
gelées). **Seules les 4 679 lignes reliées sont rattrapables** — voir le § 5.

⭐ **Les sept sont toutes en « tout »**, donc le classeur fait foi. Et comme nous
n'avons **aucune case en face**, il n'y a aucun conflit à arbitrer : c'est du
remplissage pur. Rien de chez nous n'est écrasé.

⬜ **Ce qu'il reste à faire sur ce patch** : les volumes de F, G, AH, AI, AJ viennent
des audits du 02/11, **pas d'une mesure du jour**. Ils sont à reprendre au moment du
remplissage, et le patch porte déjà ses deux contrôles pour ça *(⑩ « 1 ligne du
classeur = 1 chaîne » et son témoin inverse ⑪)*.

---

# 3. LISTE B — L'ANNULATION
### deux colonnes sur `app_affaire_ledger`, une par transaction

```
col  nom au classeur    rempli      la case chez nous         type
---  ----------------   ---------   -----------------------   ------
Z    Annulee            896 dates   date_annulation_app       text
                        100 % lis.
—    (pas au classeur)      —       motif_annulation_app      text
```

⭐ **Pourquoi `text` et non `date`** : la colonne voisine `date` du registre est en
`text`, et Hektor y met `0000-00-00`. Une colonne `date` refuserait cette valeur et
ferait tomber le run. Le projet a déjà payé cette leçon.

⭐ **Pourquoi `motif_annulation_app` alors que le classeur ne le porte pas** : c'est sa
décision du 09/11 — *« un message pour prévenir que le dossier va être annulé, on
demande la raison et la date d'annulation »*. La raison n'existe nulle part aujourd'hui.

⛔ **LES DEUX ENTRENT DANS `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` AVANT D'ÊTRE
REMPLIES** — c'est la leçon du 07/09, et elle portait précisément sur une annulation
effacée par un `--push`. Le suffixe `_app` dit exactement ça.

---

# 4. LISTE C — LE NUMÉRO DE MANDAT
### une colonne, et c'est le plus petit poste

```
col  nom au classeur   rempli     la case chez nous      type
---  ---------------   --------   --------------------   ------
C    Mandat            33 vides   numero_mandat_app      text
                       chez nous
```

⛔ **Pourquoi elle est indispensable** : `numero_mandat` est de **classe C** — elle
appartient à Hektor et le run la relit chaque nuit. **Une écriture y est effacée au run
suivant.** C'est le préalable n° 3 du 29/10, et il n'a jamais été fait. Mesure de ce
soir : `numero_mandat_app` **n'existe pas**.

⚠ C'est **28 cases** au rapport des écarts, **33** au décompte du 02/11. Les deux
chiffres ne se recoupent pas ; ce n'est pas bloquant à ce volume, mais je ne les crois
ni l'un ni l'autre tant que l'écart n'est pas expliqué.

---

# 5. ⭐ DEUX TROUVAILLES DE CE SOIR, EN MESURANT CETTE LISTE

## ✅ La réserve « 4 679 contre 4 688 » est FERMÉE

Elle était ouverte depuis ce matin. Mesure :

```
app_classeur_ligne_id   (le gel des ID)    4 773 lignes
app_classeur_lien       (lignes reliees)   4 688 lignes distinctes
lignes gelees NON reliees                     94
```

Les **9 lignes de l'écart sont 4780 à 4788** — neuf lignes **consécutives, à la fin du
classeur**, toutes des offres, toutes reliées avec la confiance « sûre ».

➡ **Ce sont neuf lignes NEUVES ajoutées au classeur depuis le gel des identifiants.**
Le relieur les a trouvées ; le gel, plus ancien, ne les connaît pas.

⬜ **Conséquence directe sur cette liste** : la clé de `app_affaire_suivi` est
`id_unique`. Ces neuf lignes **n'en ont pas**. Il faut donc **repasser le gel des
lignes avant le remplissage**, sinon le rattrapage les laisse de côté en silence.

## ✅ Zéro lien réellement cassé

La vue `app_v_classeur_lien_casse` en montre cinq, mais elle porte elle-même le
diagnostic : *« Hektor ne porte plus cette transaction, mais NOUS la gardons : le lien
tient »*. C'est le DELETE-NEVER qui fonctionne, pas une casse.

---

# 6. LE RÉCAPITULATIF — ce qu'il valide, et ce que ça débloque

```
A   une table, app_affaire_suivi, 7 cases     -> debloque Y AA F G AH AI AJ
      patch DEJA ECRIT ce matin (294 lignes)     dont 6 507 cases au rapport
B   deux colonnes _app sur le registre        -> debloque Z (896 dates)
      date_annulation_app . motif_annulation_app
C   une colonne, numero_mandat_app            -> debloque C (28 a 33 cases)
----------------------------------------------------------------------------
10 CASES. Elles font tomber les NEUF champs du § 4 bis, c'est-a-dire
6 535 des 10 240 cases du rattrapage.
```

⛔ **Chacune est une écriture en base de production, donc chacune attend son accord.**
Et pour les trois colonnes `_app`, l'ordre est le même que pour l'étiquette : la
colonne, **puis** la liste du push côté local, **puis** le remplissage.
