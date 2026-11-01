# AUDIT — LES ANCIENS NEGOCIATEURS DANS LA REPARTITION, ET LES 4 EMPLACEMENTS

**01/11/2026.** Demande de Frederic, en trois temps : *« ils ne sont pas dans mon
listing des negociateurs chez Hektor, comment faire alors ? »* · *« il faut ajouter la
possibilite de mettre deux commerciaux a l'entree et deux en sortie, donc 4 »* · *« la
repartition n'est pas envoyee a Hektor sauf erreur ? »* Puis, apres l'audit : *« on a
bien un registre des negociateurs actif et inactif, pourquoi ne pas les ajouter en
inactif avec les 200 autres ? »* et enfin la precision qui tranche tout : ⭐⭐ *« le but
n'est pas de pouvoir CHOISIR ces negociateurs mais juste faire APPARAITRE leurs noms »*.

> LECTURE SEULE pour tout l'audit : `select` sur Supabase, greps, un GET sur le Sheet,
> une lecture `mode=ro` de `data/hektor.sqlite`. Une seule ecriture : 16 lignes de JSX
> (commit `cc84413`).

---

## 1. LES 4 EMPLACEMENTS EXISTENT DEJA — depuis le 14/09/2026

`App.tsx` : `(['entree','sortie']).map(cote => ([1,2]).map(rang => ...))`, et son
commentaire dit *« QUATRE EMPLACEMENTS, deux par cote »*. Rien a developper.

⚠ **Mais ils ne servent presque pas** : `rang = 2` ne porte que **15 lignes, sur
10 chaines**, et il y a **20 saisies humaines** (`origine = 'saisie'`) sur
16 106 lignes. Le reste est la conversion automatique.

⛔ **Ce qui reste impossible, c'est TROIS personnes du MEME cote** — ce que demandent
les 13 lignes du classeur. Trois verrous, a lever ensemble : le
`CHECK rang = ANY (ARRAY[1,2])`, la cle primaire `(app_chaine_id, cote, rang)`, et le
RPC `app_repartition_commission_set` (`rang in ('1','2')`). **Non tranche.**

## 2. LA REPARTITION NE PART PAS CHEZ HEKTOR — confirme, trois preuves

1. l'ecran le dit a l'utilisateur : *« elle reste dans l'app et n'est pas transmise a
   Hektor »* ;
2. `console_job_worker.js` ne pose **aucun** type de travail pour
   `app_repartition_commission_set` ;
3. la decision est ecrite dans `api.ts:6430` : la page de Hektor ne propose que les
   actifs **de l'agence du bien**, or **26,6 % des compromis** ont l'acquereur suivi
   par une autre agence.

⭐ **Et c'est ce qui rend les anciens faciles** : `hektor_user_id` est un
`TEXT NOT NULL` **sans aucune cle etrangere**, et le RPC n'exige que « non vide ».

## 3. LES QUATRE TAS DE LA REPARTITION — 16 106 lignes, 8 049 chaines

```
27 actifs de l'annuaire          5 699 lignes   proposables a l'ecran
113 INACTIFS de l'annuaire       9 043 lignes   Jean VALLA (322 dossiers), Joel
                                                CHAMPAGNAC (299), Morgane SANGUIN
                                                (220), Aline VALETTE (91)...
5 NON-PERSONNES                  1 364 lignes   id 0 et 24 = « Cet utilisateur a ete
                                                supprime » (1 210 lignes / 605
                                                dossiers) ; Groupe GTI ANNONAY (17),
                                                Firminy (19), Ambert (23)
les 14 anciens du CLASSEUR           0 ligne    aucun numero, nulle part
```

⭐⭐ **113 des 118 « non proposables » SONT deja des negociateurs inactifs.** La
question *« pourquoi ne pas les ajouter en inactif »* est donc sans objet pour eux :
ils y sont. Le seul defaut etait que la modale ne savait pas les afficher.

## 4. POURQUOI LES 14 N'ONT PAS DE NUMERO — les dates le disent

Leurs **25 lignes** au classeur vont d'**octobre 2017 a septembre 2025** : 1 en 2017,
7 en 2018, 3 en 2019, 3 en 2020, 3 en 2021, 3 en 2022, 3 en 2023, 1 en 2024, 1 en 2025
(FRANCHINI Marjorie, offre du 17/07/2025, annulee le 23/09/2025).

⛔ **Toutes anterieures a la migration vers Hektor (~01/03/2026).** Hektor ne les a
jamais connus. **Pour etre inactif, il faut d'abord avoir existe.**
➡ Un inactif = un nom **et** un numero. Les 14 = un nom, sans numero.

## 5. ⛔ L'ANNUAIRE EST RECONSTRUIT **ET PURGE** CHAQUE NUIT

`phase2/sync/push_hektor_directory_to_supabase.py` (lance par `run_full_pipeline.ps1`,
lui-meme par le run quotidien) finit par `delete_missing` sur
`app_hektor_negotiator_agency_directory`, cle `hektor_negociateur_id` : **toute ligne
absente de la source est SUPPRIMEE**. Temoin du run du 01/11, 05:59:47 :
`negotiator_agencies_upserted: 219, active: 30, inactive: 189`. Et les 219 lignes
portent le meme `active_refreshed_at`, 04:59:53.
➡ **Une ligne ajoutee a la main dans Supabase vit moins de 24 h.**

⭐ **La source, elle, n'est JAMAIS purgee** : `data/hektor.sqlite`, table
`hektor_negociateur`, upsert pur (`normalize_source.py` / `upsert_negos`) ;
`prune_annonce_scope` ne la touche pas. **Preuve : 25 de ses lignes n'ont pas bouge
depuis le 19/05/2026**, 4 depuis septembre — ce sont justement des negociateurs que
Hektor ne renvoie plus. C'est de la que viennent les 189 inactifs.
➡ Si un jour il faut y poser quelqu'un, c'est **la**, avec un numero **hors plage
Hektor** (ses numeros vont de 1 a 225, `hektor_user_id` jusqu'a 268).

## 6. LES DROITS : 189 SUR 189 N'OUVRENT RIEN — ma reserve etait trop prudente

J'avais ecrit *« ne pas creer de faux negociateurs, l'annuaire sert aux DROITS »*.
Mesure : **189 inactifs sur 189 n'ont aucun droit NEGO. Zero exception.** Double
verrou : les patchs de droits (`patch_console_contact_*`) exigent **en plus** une
presence dans `app_user_directory` avec `user_type = 'NEGO'` (49 lignes, 30 NEGO, table
purgee elle aussi), et `backend/app/services/supabase_admin.py` filtre `is_active`
**deux fois** (requete + verification Python).

**Ce que ca pourrait casser ailleurs — mesure, pas suppose :**

- `app_mes_chaines_nommees` est la **seule** fonction qui croise repartition et
  annuaire, et elle part de l'**e-mail de l'utilisateur connecte** : un ancien n'a pas
  de compte, donc elle ne bouge pas ;
- `loadHektorNegotiatorOptions` lit l'annuaire entier mais **ecarte les inactifs ligne
  par ligne** (`if (row.is_active !== true) return null`) ;
- les deux autres lectures du front sont ciblees (par numero ou e-mail, `limit 1`) ;
- `app_repartition_absorber`, `app_repartition_purger_orphelines`,
  `app_repartition_commission_set` et `app_v_repartition_orpheline` ne joignent pas
  l'annuaire ;
- le worker prefere toujours une identite **active** quand un e-mail en rend plusieurs
  (`choisirLigneAnnuaire`, C.15 du 28/08).

## 7. LE CORRECTIF POSE — `cc84413`, 16 lignes de JSX

⭐ **`nom_au_moment` est rempli sur 16 106 lignes / 16 106. Zero trou**, y compris sur
les 10 407 lignes non proposables. Et la **fiche du dossier l'affichait deja**
(`App.tsx:30488` : `txt(l.nomAuMoment) || 'Utilisateur ' + l.hektorUserId`), tout comme
le nouvel ecran du registre (`RegistreTransactionsScreen.tsx:72`).

**Seule la modale mentait.** Mesure dans un vrai navigateur, avant / apres :

```
AVANT   value stockee 235, options = les actifs seuls
        -> affiche « (aucune option) », value relue = ''   (la part restait a cote)
APRES   une <option value="235" disabled>Jean VALLA · ancien</option>
        -> affiche « Jean VALLA · ancien », desactivee, value conservee « 235 »
```

⚠ **La donnee n'etait PAS perdue a l'enregistrement** : c'est l'etat React qui part au
RPC, pas la valeur du menu. C'etait un mensonge d'**affichage**. Mais le risque
d'**ecraser** un ancien en croyant la case vide etait reel, **sur 5 204 dossiers sur
8 049**.

⛔ **Et c'est pourquoi on N'OUVRE PAS la liste aux inactifs** (ma recommandation de la
veille, retiree) : ca les rendrait **choisissables**, contraire a sa demande.

`npm run build` vert. **Pousse le 01/11 (`057fdb2..4d2cfb6`) et EN LIGNE, prouve** :
le bundle servi par Vercel (`index-DwDQLXUU.js`, 2 489 614 octets) contient bien
`« · ancien »` (1 occurrence), temoin positif `« Repartition de la commission »`
present lui aussi.

⚠⚠ **ET UN FAUX ROUGE A FAILLI ME TROMPER** : ma premiere verification faisait
`grep -c '\xc2\xb7 ancien'` — `grep` ne developpe PAS `\xNN`, il cherchait donc le
texte litteral. Elle a repondu « 0 occurrence » sur un bundle qui contenait la chaine.
➡ **Un rouge issu d'une lecture douteuse n'est pas plus un fait qu'un vert**
(cf. `lecture-ratee-n-est-jamais-un-vert`). Remesure en JavaScript, avec temoin positif.

## 8. CE QUI RESTE

- ⬜ **le 3e rang** (13 lignes du classeur) : les trois verrous du §1, a trancher ;
- ⬜ **le texte des 605 dossiers** : « Cet utilisateur a ete supprime » s'affiche tel
  quel. Un seul mot a changer s'il prefere autre chose ;
- ⬜ **les 14 anciens** : rien a faire aujourd'hui (aucune ligne). Leur nom n'existera
  qu'au rattrapage du classeur (phase A), avec un numero de notre plage + le nom.
  ⛔ **Sans toucher l'annuaire** ;
- ⬜ **le controle a l'oeil** : la modale est derriere la connexion. A voir dans son
  Chrome, sur un dossier de Jean VALLA, comme le 21/10.
