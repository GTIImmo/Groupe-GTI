# Protocole d'essai — le garde-fou du numéro de mandat

**29/09/2026.** Préparé à la demande de Frédéric : *« teste avant de me proposer »*.
**Rien n'a été exécuté.** Ce document décrit l'essai ; il demande un accord pour tourner.

---

## Ce qu'on veut prouver, et pourquoi ça n'a jamais été prouvé

La note du 18/05 promet :

> *« Si aucun mandant n'est détecté, le job passe en erreur **sans consommer de numéro**. »*

**Cette promesse n'a jamais été éprouvée.** Le worker n'a tourné que **3 fois**
*(28/07 → 28/08, 3 réussites, 0 échec, 28 s de moyenne)* — et les trois fois avec un
mandant. **Le chemin d'échec n'a jamais été emprunté.**

Or c'est lui qui protège la ressource la plus rare du système : **un numéro de mandat
consommé ne se rend pas.**

---

## Pourquoi l'essai est sûr — et à quelle condition il cesse de l'être

La porte a **trois sources** *(`console_job_worker.js`, L4-b' du 22/09)*, et elle ne lève
qu'après les avoir toutes trouvées vides :

```
1. nos numeros de mandants, traduits vers Hektor       (ciblesHektorContacts)
2. la liste « prospects » de la console                (fetchHektorProspectsList)
3. l'API des proprietaires -- NON FILTREE PAR AGENCE   (lireProprietairesViaApi)
```

⚠⚠ **Si l'une des trois répond, la porte s'ouvre et `valideStep1` consomme un numéro.**
L'essai n'est donc sûr que sur une annonce **vide des trois côtés**.

**Les cibles retenues** — mesurées le 29/09, sans relation, sans numéro de mandat, et
**déjà marquées pour suppression** dans la mémoire projet :

```
63146   « ESSAI C9 -- ne pas diffuser »      Tence   Estimation
63147   « ESSAI C9 bis -- ne pas diffuser »  Tence   Estimation   (app_dossier_id 10 000 000)
```

---

## Les témoins, relevés AVANT

`phase2/checks/essai_garde_fou_mandat.py` — lecture seule, relevé du 29/09 :

```
plus grand numero PROTEXA : 18904      <- LE TEMOIN. Il n'augmente QUE si un numero est consomme
mandats dans le miroir    : 24999
mandats sur les cibles    : aucun
```

---

## Le déroulé

```
1. RELEVER      python phase2/checks/essai_garde_fou_mandat.py        (deja fait)

2. CREER LE TRAVAIL   ⛔ ECRITURE EN PRODUCTION -- accord de Frederic
   RPC app_console_create_mandat_auto_number_job
       target_app_dossier_id   = 7589129        (annonce 63146)
       target_hektor_annonce_id= '63146'
       mandat_payload          = { mandant_contact_ids: [] }   <- VIDE, c'est le sujet
   -> le front fait exactement cela quand on clique le bouton

3. LAISSER LE WORKER LE PRENDRE                  ~30 s

4. LIRE LE JOURNAL DU TRAVAIL     app_console_job_log
```

### Ce qui prouve quoi

| ce qu'on lit dans le journal | verdict |
|---|---|
| **aucune ligne `hektor_mandat_step1_number`** | ✅ **la porte a tenu — rien n'a été consommé** |
| le travail est en `error`, motif *« Aucun mandant Hektor rattaché »* | ✅ le refus est explicite et lisible par l'utilisateur |
| une ligne `hektor_mandat_step1_number` existe | ⛔ **la porte a cédé** — un numéro a été brûlé, et il faut trouver **laquelle des trois sources a répondu** |

⚠ **Le témoin `18904` ne bougera pas tout de suite** : le miroir ne se met à jour qu'au
run de nuit. **La preuve immédiate est dans le journal du travail**, pas dans le miroir.
Le relevé du lendemain sert de confirmation.

---

## Ce que l'essai coûte, honnêtement

```
3 appels de lecture chez Hektor   (ouvrir l'onglet, ouvrir l'assistant, lister les types)
                                   -- ils ne consomment rien, la note du 18/05 le dit :
                                      le numero est consomme A LA VALIDATION
1 ligne dans app_console_job       un travail en erreur, sur une annonce d'essai
0 numero de mandat                 SI la porte tient. C'est precisement ce qu'on mesure.
```

---

## Ce que l'essai ne dit pas

Il prouve **le refus**. Il ne prouve pas le **succès** — pour ça il faudrait consommer un
vrai numéro, et il n'existe aucun mode d'essai chez PROTEXA. Le succès, lui, est déjà
attesté par les **3 travaux réussis** de juillet-août.
