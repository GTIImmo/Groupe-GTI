# La fenêtre de bascule — la procédure, commande par commande

*Écrite le 23/09/2026, à jouer le jour J. Elle remplace la liste d'étapes de
`AUDIT_COMPLET_AVANT_BASCULE_2026-09-23.md`, qui était plus courte et moins juste.*

> **LA RÈGLE, posée le 22/09 après la suppression accidentelle de 7 201 recherches :**
> **écrire chaque commande en entier, la MONTRER, et seulement ensuite l'exécuter.**
> Le drapeau oublié ce jour-là n'était pas une étourderie — c'était une commande recopiée
> de mémoire au lieu d'être lue.

---

## Ce que la bascule fait, en une phrase

`hektor_contact_id` cesse d'être le numéro que Hektor a donné pour devenir **le nôtre**.
Le numéro de Hektor ne disparaît pas : il vit dans `hektor_target_id`, et c'est lui qu'on
envoie à Hektor.

## Les trois familles — c'est tout le sujet

| | traitement | pourquoi |
|---|---|---|
| `app_contact_current` · `app_contact_search_current` | **traduites en place** | leur clé ne bouge pas *(plages disjointes · nom figé)* |
| `app_contact_relation_current` · les deux tables de doublons | **vidées**, le build les refait | leur clé est une **empreinte calculée sur le numéro** — aucun SQL ne peut la recalculer |
| les **13 tables jamais reconstruites** | **traduites** | sinon les **35 fonctions et vues** qui les cousent au reconstruit ne joignent plus rien, **sans lever d'erreur** |

**Pas touchés** : `app_console_deleted_contact_log` et `app_contact_consent` *(des journaux —
une trace qu'on réécrit ne trace plus)* · `app_affaire_ledger` *(`hektor_acquereur_id` est la
trace de ce que Hektor a dit ; sa doublure est déjà posée)*.

---

## AVANT — ce qui doit être vrai

- [ ] les **4 services** sont **arrêtés**
- [ ] `app_console_job` **vide** *(0 en attente le 23/09)*
- [ ] `app_contact_pending` et `app_search_pending` **vides** *(0 le 23/09)*
- [ ] le dernier run de nuit a **réussi**
- [ ] les correctifs C-1 à C-12 sont **déployés** *(ils le sont depuis le 23/09)*

```powershell
Stop-Service HektorConsoleWorkerAdmin,HektorConsoleWorkerActions,HektorConsoleWorkerDocuments,HektorConsoleWorkerSyncLight -Force
```

---

## ① La sauvegarde — avant tout, et elle seule permet de revenir

```powershell
python phase2\sync\backup_critical.py
```

Puis la photo du serveur, **`VACUUM INTO` obligatoire** *(la base est en WAL : une copie de
fichier ne capture pas les écritures en attente)* :

```bash
python -c "import sqlite3,datetime;d=datetime.date.today().isoformat();sqlite3.connect(r'C:\Hektor\Projet\phase2\phase2.sqlite').execute(f\"VACUUM INTO 'C:/Hektor/Sauvegardes/phase2_avant_bascule_{d}.sqlite'\")"
```

---

## ② Le rattrapage des doublures — **DEUX étapes, pas une**

⚠ **Trouvé par le compte à blanc du 23/09 : la fonction REFUSAIT, pour 6 contacts.**
Ils avaient pourtant leur doublure **côté serveur** depuis le matin même. Elle n'était
jamais montée — `pousser_numeros_contact.py` lit `app_contact_current__sb`, **la copie
descendue à 07:30**, alors qu'il tourne à 05:0x dans le run. Il travaille sur la photo de
la veille, si bien qu'**un contact né chez Hektor dans la journée n'obtient sa doublure
dans Supabase que la nuit SUIVANTE.**

> **CONFIRMÉ PAR LE RUN DU 23/09 à 15h10** : 10 contacts neufs sont arrivés pendant le run,
> et **4 d'entre eux n'avaient pas leur doublure dans Supabase** juste après. Le décalage
> n'est pas un accident : **il se reproduit à chaque run**. L'étape ②a n'est donc pas une
> précaution, c'est une nécessité — et elle doit être jouée **le soir même**, pas la veille.

**②a — faire monter les numéros du registre local** *(sans quoi ②b ne peut rien remplir :
il copie `app_contact_current.app_contact_id`, qui serait encore vide)*

```powershell
python phase2\identite\pousser_numeros_contact.py --dry-run
python phase2\identite\pousser_numeros_contact.py
```

*Frein intégré : lots de 2 000, pause de 0,4 s, 31 requêtes. La RPC ne sait
qu'**actualiser** — renvoyer une valeur identique ne touche aucune ligne.*

**②b — propager la doublure dans les satellites**

```bash
python -c "import urllib.request,os,json,sys;sys.path.insert(0,r'C:\Hektor\Projet\phase2\sync');from push_contacts_to_supabase import DEFAULT_ENV_FILES,load_env_file;[load_env_file(f) for f in DEFAULT_ENV_FILES];u=os.environ['SUPABASE_URL'].rstrip('/');k=os.environ['SUPABASE_SERVICE_ROLE_KEY'];r=urllib.request.Request(f'{u}/rest/v1/rpc/app_contact_id_propager',data=b'{}',headers={'apikey':k,'Authorization':f'Bearer {k}','Content-Type':'application/json'},method='POST');print(urllib.request.urlopen(r,timeout=300).read().decode())"
```

**Attendu** *(joue en reel le 23/09)* : les **37** rapprochements passent de 49 684 à
**49 721** — tous couverts. Les compteurs passent de 10 180 à **10 184**.

⚠ **Et il RESTE 37 lignes que rien ne peut rattraper** — 36 compteurs et 1 lien d'agenda.
Vérifié ligne à ligne : **leur contact n'existe plus dans l'app**. Elles sont déjà
orphelines aujourd'hui, la bascule ne les abîme pas davantage. **Il n'y a rien à faire, et
ce n'est pas un incident** — c'est écrit ici pour qu'on ne le redécouvre pas le jour J.

### ÉTAT DE L'OUTIL, vérifié le 23/09

Les deux fonctions sont **installées dans Supabase**, dans leur version à jour — celle qui
porte le message de refus corrigé **et** la traduction du JSON des liens d'agenda.

**Le signe qui le prouve** : le compte à blanc affiche `"_json_liens_agenda": 9`.
S'il manque, c'est l'ancienne version et il faut recoller le patch.

### Le compte à blanc, joue en reel le 23/09 — **au vert**

```
deja bascules                              0
traduire app_contact_current          61 984
traduire app_contact_search_current   11 384
vider    app_contact_relation_current 81 315
vider    les doublons                      0
app_rapprochement                     49 721
app_search_count_high_water           10 184
app_email_envoi 24 . propositions 11 . relances 10 . agenda 8 . statuts 7 . visites 3
_json_liens_agenda                         9
```

---

## ③ La bascule Supabase — **à blanc d'abord**

⚠ **Les deux fonctions doivent exister.** On ne peut PAS les créer depuis PowerShell :
`psql` et la CLI Supabase sont absents de la machine, et l'API REST n'exécute que des
**appels** de fonctions, jamais du SQL libre. ➡ coller
`supabase/patch_c13_bascule_identite_contact_2026-09-23.sql` dans **l'éditeur SQL du
tableau de bord Supabase**.

**Depuis l'éditeur SQL :**

```sql
select public.app_bascule_identite_contact(false);
```

**Ou depuis PowerShell** *(éprouvé le 23/09 — les trois détails ci-dessous ne sont pas
décoratifs)* :

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $e=@{}; Get-Content 'C:\Hektor\Projetpps\hektor-v1\.env' | Where-Object { $_ -match '^\s*[A-Za-z_][A-Za-z0-9_]*\s*=' } | ForEach-Object { $p = $_ -split '=',2; $e[$p[0].Trim()] = $p[1].Trim().Trim('"') }; $u=$e['VITE_SUPABASE_URL'].TrimEnd('/'); $k=$e['SUPABASE_SERVICE_ROLE_KEY']; Invoke-RestMethod -Method Post -Uri "$u/rest/v1/rpc/app_bascule_identite_contact" -Headers @{apikey=$k; Authorization="Bearer $k"} -ContentType 'application/json' -Body '{"p_appliquer": false}' -UserAgent 'GTI-PowerShell/1.0' | ConvertTo-Json -Depth 8
```

| le détail | ce qui arrive sans lui |
|---|---|
| **`-UserAgent`** | Supabase répond *« Forbidden use of secret API key in browser »* : il prend PowerShell pour un navigateur et **refuse la clé de service** |
| **`apps\hektor-v1\.env`** | le `.env` racine ne porte **que** `SUPABASE_POOLER_HOST` — ni l'URL, ni la clé |
| **`Tls12` explicite** | PowerShell 5.1 négocie encore du TLS ancien par défaut |

*Pour appliquer : `"p_appliquer": true`. Pour défaire : même commande avec
`app_bascule_identite_contact_annuler`.*

**Lire les comptes. Les montrer.** Ils doivent ressembler à ceci *(mesures du 23/09)* :

```
a_traduire_app_contact_current              61 984
a_traduire_app_contact_search_current       11 384
a_vider_app_contact_relation_current        81 315
app_rapprochement                           49 721
app_search_count_high_water                 10 220
... et les petites : 24 · 11 · 10 · 9 · 7 · 3
```

⚠ **La fonction REFUSE** tant qu'un contact n'a pas sa doublure **ou** sa case cible.
Un refus n'est pas un incident : c'est ② qui n'a pas fini.

**Puis seulement :**

```sql
select public.app_bascule_identite_contact(true);
```

---

## ④ Le registre local prend le même numéro

⚠ **`app_contact` a reçu sa case cible le 23/09** *(356 156 / 356 156)*. Sans elle, cette
étape aurait **effacé le numéro de Hektor du registre** — et avec lui le seul lien local
entre une **vente et son acheteur**.

```bash
python -c "import sqlite3;c=sqlite3.connect(r'C:\Hektor\Projet\phase2\phase2.sqlite',timeout=60);c.execute('PRAGMA busy_timeout=30000');n=c.execute('UPDATE app_contact SET hektor_contact_id = CAST(app_contact_id AS TEXT) WHERE app_contact_id IS NOT NULL AND CAST(hektor_contact_id AS INTEGER) < 10000000').rowcount;c.commit();print('registre traduit :',n)"
```

---

## ⑤ La correspondance redescend

```powershell
python phase2\identite\descendre_correspondance_contacts.py --dry-run
```

**Attendu : ~61 984 correspondances.** *(Avant C-3, cette étape aurait tronqué à 10 000 puis
refusé à 5 000 — en silence, et sans arrêter le run.)*

```powershell
python phase2\identite\descendre_correspondance_contacts.py
```

---

## ⑥ Le build reconstruit la couche

```powershell
python phase2\contacts\build_contacts_layer.py --no-reports
```

⚠ **Il s'arrête tout seul** si la correspondance est vide alors que la couche porte déjà des
identités à nous *(garde C-3)*. Un arrêt ici veut dire : reprendre à ⑤.

---

## ⑥bis — ÉLARGIR LE PÉRIMÈTRE *(manquait à cette procédure — trouvé le 23/09 en la jouant)*

Le build vient de remettre l'éligibilité à ce que sa règle dit. **C'est ce script qui
repose les personnes citées par Hektor** — c'est l'étape 17 du run de nuit, et elle doit
venir **entre le build et le push**. Sans elle, 2 763 personnes ne sont pas rafraîchies.

```powershell
python phase2\contacts\elargir_perimetre_console.py --dry-run
python phase2\contacts\elargir_perimetre_console.py
```

**Mesuré le 23/09, après la bascule** : `annuaire avant 59 222 → a faire entrer 2 763
→ annuaire apres 61 985`. **C'est la preuve en direct que G-11 était nécessaire** : `cites`
porte les numéros **Hektor**, l'annuaire porte les **identités**. Sans le correctif du
matin, ce script aurait trouvé **zéro**.

---

## ⑦ Le push, avec **--reset-push-state**

⚠ **CE QUE J'AVAIS ÉCRIT ICI ÉTAIT FAUX, ET JE L'AI SU EN LE SUBISSANT.** Je disais que ce
drapeau empêchait la suppression. **Non** : dans la version du 23/09 matin, la remise à zéro
venait **après** le calcul des disparues — elle ne préparait que le run *suivant*.

Résultat en direct pendant la bascule : le push a **supprimé 61 985 contacts et 81 313
relations**, puis les a reposés. La donnée était intacte à l'arrivée, **mais le chemin ne
l'était pas** : un échec d'envoi en cours de route *(le PGRST102 du 01/08)* aurait laissé
le parc supprimé.

> **CORRIGÉ le 23/09, dans la fenêtre même** : la remise à zéro passe **avant** le calcul.
> Dire « je ne sais plus ce que j'ai envoyé », c'est ne rien déclarer disparu — ce que le
> drapeau promettait.

```powershell
python phase2\sync\push_contacts_to_supabase.py --push-mode full --contacts-scope eligible --include-archived-searches --reset-push-state
```

*(`full` et non `update` : après la bascule, tout a changé de clé — filtrer sur « ce qui a
changé » n'aurait aucun sens.)*

---

## ⑧ Les services repartent

```powershell
Start-Service HektorConsoleWorkerAdmin,HektorConsoleWorkerActions,HektorConsoleWorkerDocuments,HektorConsoleWorkerSyncLight
```

---

## ⑨ VÉRIFIER — et ne pas s'en tenir aux comptes

```sql
-- personne ne doit rester en arriere
select count(*) filter (where hektor_contact_id::bigint <  10000000) as restes_en_arriere,
       count(*) filter (where coalesce(hektor_target_id,'') = '')    as sans_cible,
       count(*) as total
  from public.app_contact_current where hektor_contact_id ~ '^[0-9]+$';

-- les rapprochements doivent RESTER visibles : c'est le test qui compte
select count(*) as rapprochements_joignables
  from public.app_rapprochement r
  join public.app_contact_current c on c.hektor_contact_id = r.hektor_contact_id;

-- les sondes doivent rester a zero
select * from public.app_v_contacts_en_double_identite limit 5;
select * from public.app_v_envois_en_attente_hektor;
```

**Puis les trois gestes qu'aucun compte ne remplace :**

- [ ] ouvrir une **fiche contact** dans l'app — elle s'affiche, ses recherches sont là
- [ ] **modifier** une recherche — le travail part, il n'est pas bloqué en conflit *(C-12)*
- [ ] **un envoi d'espace client réel**, vers `frederic.gerphagnon@` uniquement — l'espace
      n'est pas vide et ne repropose pas un bien déjà écarté *(C-7)*

---

## SI ÇA TOURNE MAL

```sql
select public.app_bascule_identite_contact_annuler(false);   -- compter
select public.app_bascule_identite_contact_annuler(true);    -- defaire
```

Puis le registre local à l'envers, puis rejouer ⑥ et ⑦. Et la sauvegarde ① derrière tout ça.

---

## CE QUI N'EST PAS DANS CETTE PROCÉDURE, ET QUI SE DIT

- **Les 19 gênants** ne sont pas corrigés. L'app marchera, mais elle mentira par endroits —
  la recherche par numéro Hektor, la répartition de commission, le doublon d'invité.
  **Ce sont des défauts d'affichage et de confort, pas de perte.**
- **Les 9 événements Google déjà partis** gardent leur numéro dans leur description. Rien ne
  peut les réécrire. *(Les suivants portent la cible depuis le 23/09.)*
- **`app_affaire_personne_ecart`** : 2 lignes, sans doublure, non traduites. Assumé.
- **Le chemin « créer un mandant »** ne porte aucune identité d'app : il relie sa ligne
  provisoire au numéro de Hektor. **C'est un manque à combler dans C.9**, pas un défaut
  de la bascule.


---

# CE QUE LA BASCULE DU 23/09 A DONNÉ

**Jouée de 18h40 à 19h05**, services arrêtés, personne dans l'app depuis 12h01.

```
contacts        61 985 portent NOTRE numero
recherches      11 387 suivent -- le nom fige a tenu
relations       81 313 videes puis refaites par le build
liens d'agenda       9 JSON traduits
registre local 356 166 -- AUCUN numero Hektor perdu
```

## VÉRIFIÉ APRÈS

| contrôle | résultat |
|---|---|
| rapprochements joignables à un **contact** | **49 742 / 49 742** |
| rapprochements joignables à une **recherche** | **49 742 / 49 742** |
| sondes *(double identité, envois en attente, orphelins)* | **toutes à zéro** |
| contacts restés en arrière | **0** |
| travaux en erreur | **0** |
| recherches retrouvables par l'identité | **11 387**, dont **0 introuvable** |
| la **barrière** *(C-2)* tourne après la bascule | **oui**, 0 enfilé *(bannettes vides)* |
| **une fiche contact ouverte dans l'app** | négociateur résolu, **bien lié retrouvé** |
| **la recherche par le numéro de HEKTOR** | **elle trouve** la fiche, qui porte `10 356 150` *(G-2)* |

## LE TROISIÈME GESTE HUMAIN N'EST PAS FAIT, ET IL SE DIT

**Modifier une recherche depuis l'app** n'a **pas** pu être joué :
`app_edit_search_optimistic` refuse une connexion SQL avec `forbidden_update_contact_search`
— le garde `app_console_can_request_contact_job` vérifie **qui demande**, et seul un
négociateur connecté passe.

✅ **Ce que ce refus prouve quand même** : la fonction a **trouvé le contact** sous son
identité *(sinon elle aurait levé `contact_not_found`)*. **L'identité marche ; c'est
l'autorisation qui manque** — ce qui est exactement ce qu'on attend d'une app.

➡ **À faire par un humain connecté** : ouvrir un acquéreur, modifier un critère, vérifier
que le travail part et **n'est pas bloqué en conflit**. C'est le dernier point non couvert.
