# SPEC — LA CHARGE DES HONORAIRES, DU MANDAT À LA TRANSACTION

**02/11/2026.** Demande de Frédéric : *« lorsqu'on édite un mandat pour signature
le choix de la charge des honoraires doit être mémorisé dans le registre des
mandats »*, et *« à la saisie de la modale offre ou compromis … il faudrait que
la charge de la commission se pré-remplisse mais reste modifiable comme les
autres champs »*.

⛔ **AUCUN CODE N'EST POSÉ** *(« oui mais ne code rien »)*. Ce document est
l'audit et l'explication. Le « vas-y » reste à donner, pièce par pièce s'il le
souhaite.

---

## § 0. LA RÉPONSE

```
C'EST POSSIBLE, ET ON N'INVENTE RIEN : LE CHEMIN EXISTE DEJA, EPROUVE DEPUIS
LE 13/10, POUR LA DATE DE CLOTURE DU MANDAT. On le recopie.

⚠ MAIS IL FAIT CINQ PIECES, PAS UNE -- et la cinquieme est celle qu'on
  oublierait : LA LIGNE DU REGISTRE EST DETRUITE PUIS REFAITE A CHAQUE PUSH.
  Une colonne « _app » repart a NULL chaque nuit si rien ne la repose.

⛔ PLUS DEUX LISTES BLANCHES EN DUR, sans lesquelles la valeur est JETEE
  EN SILENCE.
```

---

## § 1. L'AUDIT — où le choix est fait, et où il meurt

### Où il est fait

```
App.tsx:5735   un menu « Charge des honoraires » : Acquereur / Mandant
App.tsx:4056   le type : honorairesCharge: 'acquereur' | 'mandant' | ''
App.tsx:5435   il est OBLIGATOIRE pour valider l'onglet « prix » de la modale
App.tsx:4595   il entre dans le payload du document : honoraires.charge
App.tsx:5545   generatePdf() -> createGenerateMandatPdfJob({ html, payload, ... })
App.tsx:4803   et il coche la case du contrat :
               « La totalite des honoraires sera a la charge du :
                 [ ] MANDANT   [ ] ACQUEREUR »
```

### Où il meurt

⛔ **Nulle part il n'est enregistré.** Vérifié sur `information_schema` le 02/11 :
la base de production n'a **aucune** colonne de charge sur un mandat. Le payload
sert à fabriquer un PDF, puis il disparaît avec la modale.

### Et son défaut est faux 9 fois sur 10

```
App.tsx:4560   honorairesCharge: rawHonoraires ? 'acquereur' : ''
```
Dès qu'il y a des honoraires, le code écrit « acquereur » — **personne ne l'a
dit**. Or le classeur mesure 894 « Vendeur » contre 61 « Acquéreur », soit
**93,6 % de vendeur**. ⚠ Et c'est **l'inverse** du défaut de la transaction
(`useState('vendeur')`, App.tsx:14003) : la même app propose deux réponses
contraires à la même question.

### Et Hektor n'a rien à dire

```
hektor_mandat      17 cles, AUCUNE charge, AUCUN honoraire, AUCUN taux
hektor_compromis   16 cles : des MONTANTS, jamais qui paie
hektor_vente       19 cles : idem
```
⭐ C'est ce qui rend ce champ **légitime chez nous** — voir § 2.3.

---

## § 2. LE PATRON À RECOPIER — `mandat_date_cloture`, posé le 13/10

### 2.1 Ses cinq pièces

```
1  LA COLONNE SEPAREE   app_mandat_register_current.mandat_date_cloture_app
2  LA VUE REFAITE       COALESCE(notre valeur, celle de Hektor) -> 71 -> 73 colonnes
                        ⭐ « refaite DEPUIS ELLE-MEME, jamais recopiee a la main »
3  LES AUTRES LECTEURS  app_generate_mandat_echu_alerts lit LA TABLE, pas la vue
4  LA RE-POSE           Console/reposer_cloture_mandat.js -> rpc
                        app_reposer_cloture_mandat_app(), appelee depuis
                        push_single_annonce_to_supabase.py:710
5  LA RPC DE SAISIE     app_set_mandat_cloture_optimistic(text, text, text)
```

### 2.2 ⭐⭐⭐ LA LEÇON QU'IL PORTE, et c'est la plus importante

Commentaire de `Console/reposer_cloture_mandat.js`, l. 14 :

> « La ligne de registre qui AFFICHE notre date de clôture est **DÉTRUITE PUIS
> REFAITE à chaque push** : le run (`push_upgrade_to_supabase.py`, delete +
> insert), le worker (`push_single_annonce_to_supabase.py`, delete + upsert).
> Notre colonne repart donc à NULL **les deux fois**. Le carnet
> `app_mandat_champ_app`, lui, n'est jamais touché : **c'est lui qui fait foi, et
> c'est de lui qu'on repose.** »

```
LE CARNET FAIT FOI.         app_mandat_champ_app -- jamais detruit
LA COLONNE EST UN REFLET.   elle meurt a chaque push, et on la REPOSE
```

⛔ **Sans la pièce 4, la charge disparaîtrait de l'écran chaque nuit** sans que
personne comprenne pourquoi — et la modale ne pourrait plus la pré-remplir.

### 2.3 ⭐ Et le critère de décision est déjà écrit, il désigne la charge

`magasin_mandat_app.py:58`, bien avant ce chantier :

> « UN SEUL pour l'instant, et c'est **délibéré** : sur 24 939 mandats, Hektor ne
> porte une date de clôture que 94 fois (0,4 %). C'est **le seul champ du mandat
> où il n'a rien à dire** — donc le seul qu'on puisse confier à l'app sans
> risquer de la figer sur une valeur périmée. »

```
                        ce que HEKTOR en porte     candidat ?
mandat_date_cloture     94 / 24 939  = 0,4 %       OUI, et c'est fait
LA CHARGE               0 / 24 939   = 0,0 %       OUI, et c'est MIEUX
date_debut, date_fin,
type, montant           ~100 %                     non, et c'est juste
```

### 2.4 ⚠ Et la cause racine que le patron a fermée — à ne pas rouvrir

> « Aujourd'hui le worker écrit NOTRE date dans **LA COLONNE DE HEKTOR**, puis
> `magasin_mandat_app.py` relit ce même registre comme « ce que dit l'app ».
> **NOUS RELISIONS NOTRE PROPRE ÉCRITURE COMME SI ELLE FAISAIT AUTORITÉ** : c'est
> pour ça que 4 lignes du carnet portaient une valeur qui n'était la décision de
> personne. La colonne séparée ferme la boucle. »

⛔ **Donc : une colonne à nous, un suffixe `_app`, jamais la colonne de Hektor.**
Ici le risque est nul (Hektor n'a aucune colonne de charge) mais la règle de
nommage reste : `mandat_charge_honoraires_app`.

---

## § 3. LES SEPT PIÈCES PROPOSÉES, DANS L'ORDRE

⚠ **L'ordre n'est pas libre** : une colonne demandée à Supabase avant d'exister
rend un 400, et le 16/10 ce genre d'inversion a fait **tomber toute l'étape
`affaire_ledger` du run**.

```
A  LA COLONNE          app_mandat_register_current.mandat_charge_honoraires_app
   ou                  (patch Supabase, a coller par Frederic)
   risque              nul : colonne neuve, ecrite par personne

B  LA VUE              app_registre_mandats_current, REFAITE DEPUIS ELLE-MEME
   ou                  (meme patch)
   risque              ⚠ elle passe de 73 a 74 colonnes. Le front nomme ses
                       colonnes une par une -> rien ne casse, mais rien ne la
                       voit non plus avant la piece F

C  LES DEUX LISTES     magasin_mandat_app.py:64   CHAMPS_SUIVIS
   BLANCHES            contrat_autorite.py:92     CHAMPS_APP_MANDAT
   ⛔⛔ sans C          la valeur est ECRITE puis IGNOREE, sans aucune erreur
                       (garde explicite a magasin_mandat_app.py:277)

D  LA RE-POSE          app_reposer_charge_mandat_app(), sur le patron de
                       app_reposer_cloture_mandat_app()
   ou                  patch Supabase + l'appel apres le push
   ⛔ sans D            la colonne repart a NULL a CHAQUE push, donc chaque nuit

E  LA RPC DE SAISIE    app_set_mandat_charge_optimistic(), patron
                       app_set_mandat_cloture_optimistic
   ou                  patch Supabase
   ⭐ elle garde        l'AUTEUR (ecrit_par) -- voir § 4.2, c'est un vrai sujet

F  LE FRONT, cote      generatePdf() appelle la RPC APRES createGenerateMandat-
   MANDAT              PdfJob, dans son propre try/catch
   ou                  App.tsx ~5545
   ⭐ patron            l'appel de ecrireAffaireCommission apres le geste de
                       statut : « APRES, ET JAMAIS DANS LA CHARGE »

G  LE FRONT, cote      la modale de statut pre-remplit statusChangeChargeCommission
   TRANSACTION         depuis le dossier, A LA CREATION SEULEMENT, et leve le
                       drapeau (comme la reprise depuis l'offre, App.tsx:17753)
   ou                  App.tsx ~17745 (le meme effet qui reprend deja de l'offre)
   ⭐ le select         RESTE MODIFIABLE : il l'est deja, et le toucher leve le
                       drapeau, donc la modification part normalement
```

### ⭐ L'ordre de précédence à la création d'une offre, proposé

```
1. ce que l'utilisateur a choisi dans la modale        (il sait mieux)
2. la charge de l'OFFRE de la meme chaine              (existe deja, l. 17753)
3. LA CHARGE DU MANDAT                                 (piece G, NEUF)
4. « vendeur » par defaut                              (existe deja, 93,6 % juste)
```

---

## § 4. ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS

### 4.1 La vue passe de 73 à 74 colonnes

Le front **nomme ses colonnes une par une** (`affaireLedgerSelect` et ses
cousins), donc une colonne de plus ne casse rien. ⚠ **Mais l'inverse est le
piège déjà payé DEUX FOIS le 13/10** : une colonne qui existe en base et qu'on
oublie d'ajouter à la liste du front **n'est jamais vue, sans aucune erreur**.

⬜ **À mesurer avant de coller B** : la liste complète des lecteurs de la vue et
de la table. Le patron du 13/10 avait trouvé **un** autre consommateur
(`app_generate_mandat_echu_alerts`) et la pièce 3 existait pour lui. Je n'ai
**pas** refait cette mesure pour la charge.

### 4.2 ⚠⚠ Le worker efface l'auteur — déjà noté le 21/10, jamais traité

`app_mandat_champ_app.ecrit_par` valait `frederic.gerphagnon@…` sur la ligne du
14/10 et vaut **NULL** après l'essai du 21/10 : deux chemins écrivent ce carnet,
et **le worker écrit sans utilisateur, donc il écrase la trace de l'humain**.

⭐ **Conséquence directe pour la pièce F** : il faut écrire **depuis le front**
(la RPC, avec le jeton de l'utilisateur), **pas depuis le worker**. Sinon la
charge serait mémorisée sans qu'on sache jamais qui l'a choisie — et c'est de
l'argent.

### 4.3 ⚠ Le vocabulaire : `mandant` contre `vendeur`

```
le document de mandat   'acquereur' | 'mandant'
la transaction          'vendeur'   | 'acquereur'   (contrainte stricte)
le classeur             'Vendeur'   | 'Acquereur'
```
Il faut **traduire à l'écriture**. ⚠ Et notre « Mandant » est **pollué depuis le
17/07** (l'acheteur y est rangé à tort) : la traduction doit se faire sur **le
mot du menu**, jamais en relisant un rôle de contact.

### 4.4 ⚠ Un mandat peut être généré plusieurs fois

La même modale sert au **mandat** et à l'**avenant** (`docMode === 'avenant'`).
⬜ **À trancher** (§ 6) : un avenant doit-il écraser la charge mémorisée ?

### 4.5 ⛔ Ce qui ne change pas, et doit le rester

```
rien ne part chez Hektor      il n'a aucune destination pour ce champ
le run n'est pas touche        sauf l'appel de re-pose (piece D)
le worker n'est pas touche     l'ecriture vient du front (§ 4.2)
aucune colonne retiree         ni renommee
les droits et les politiques   inchanges
la modale de statut            le select reste modifiable, et la regle de
                               modification (drapeau) reste INTACTE
```

---

## § 5. LE RETOUR ARRIÈRE

Chaque patch Supabase va par trois, comme le patron du 13/10 : le **patch**, son
**INVERSE**, sa **RÉPÉTITION** (les contrôles, rejouables). Et chaque bloc
vérifie **son empreinte** avant d'écrire, et **s'arrête** si quelqu'un est passé
avant.

```
A, B   l'INVERSE refait la vue a 73 colonnes et retire la colonne
C      deux lignes a retirer dans deux fichiers Python
D      l'INVERSE supprime la fonction et l'appel
E      l'INVERSE supprime la fonction
F, G   du front : git revert du commit
```
⭐ **Et les donnees déjà saisies survivraient à un retour arrière complet** :
elles vivent au **carnet** (`app_mandat_champ_app`), que l'inverse ne touche pas.
C'est le bénéfice de la leçon du § 2.2.

---

## § 6. COMMENT ON VÉRIFIERA — et les témoins

```
T1  TEMOIN POSITIF   un mandat d'essai genere avec « Mandant » -> une ligne
                     champ='charge_commission', valeur='vendeur', ecrit_par
                     RENSEIGNE (c'est le § 4.2 qu'on controle la)
T2  TEMOIN INVERSE   un mandat genere avec « Acquereur » -> 'acquereur'.
                     ⛔ Les DEUX valeurs, sinon on ne prouve rien (c'est
                     exactement l'erreur qui a laisse 8 « acquereur » et
                     0 « vendeur » passer inapercus pendant 17 jours)
T3  LA RE-POSE       pousser l'annonce d'essai, puis relire la colonne du
                     registre : elle doit ETRE ENCORE LA (piece D)
T4  LA NUIT          le lendemain matin, meme controle. ⛔ C'est le seul
                     controle qui juge vraiment la piece D
T5  LA REPRISE       creer une offre sur ce bien SANS toucher le select :
                     la charge du mandat doit arriver, et s'ECRIRE
                     (c'est le correctif 2a82417 qui la fait partir)
T6  LA MODIFICATION  rouvrir l'offre et envoyer sans rien toucher :
                     la valeur NE DOIT PAS BOUGER (la regle de P5, gardee)
T7  LE TEMOIN DU     une offre sur un bien SANS charge au mandat -> le defaut
    DEFAUT           « vendeur » s'applique, et s'ecrit
```

⛔ **Tout sur le bien d'essai, jamais sur une vraie affaire** — et avec son
accord à chaque écriture chez Hektor.

---

## § 7. ⬜ LES QUATRE DÉCISIONS QUI LUI REVIENNENT

```
① LE MOMENT : on memorise a la GENERATION du document, ou seulement quand la
  SIGNATURE est demandee ? Un document peut etre genere puis jete.
  ⭐ Ma recommandation : A LA GENERATION. C'est la que le choix est fait, et
  une charge memorisee sur un mandat non signe ne fait de mal a personne --
  alors qu'un choix perdu, oui.

② L'AVENANT : un avenant ecrase-t-il la charge memorisee ?
  ⭐ Ma recommandation : OUI, il l'ecrase -- un avenant est une decision plus
  recente. Mais en gardant la trace (le carnet porte deja ecrit_le).

③ LE DEFAUT DU DOCUMENT : corrige-t-on App.tsx:4560 au passage ?
  ⭐ Ma recommandation : OUI, et dans le meme geste -- « vendeur » par defaut
  des deux cotes. Aujourd'hui le document propose « acquereur », faux 9 fois
  sur 10, et personne ne l'a choisi.

④ LE PERIMETRE : les sept pieces d'un coup, ou par paliers ?
  ⭐ Ma recommandation : DEUX PALIERS.
     palier 1  A + B + C + D + E + F   -> le mandat MEMORISE (et survit a la nuit)
     palier 2  G                       -> la transaction PRE-REMPLIT
  Le palier 1 est utile seul : il arrete la perte. Le palier 2 n'a de sens
  qu'apres, puisqu'il lit ce que le palier 1 ecrit.
```

---

## § 8. PROVENANCE

```
le code        apps/hektor-v1/src/App.tsx, src/lib/api.ts
               phase2/identite/magasin_mandat_app.py, contrat_autorite.py
               Console/reposer_cloture_mandat.js
               phase2/sync/push_single_annonce_to_supabase.py
le patron      supabase/patch_chantier3_3c_cloture_mandat_app_2026-10-13.sql
               (+ son INVERSE et sa REPETITION)
la base        SUPABASE EN DIRECT (dwaqxfrinihnychuoptk), 02/11, lecture seule
Hektor         data/hektor.sqlite, raw_json deballes, 02/11
le classeur    cache local du 01/11 18:47, sans appel reseau
l'historique   git log -S, et notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md
               (F5 l. 1601/1619, le tableau l. 1851, P5 l. 1880)
```

⬜ **CE QUE JE N'AI PAS MESURÉ, et que je ne suppose pas** : la liste complète des
lecteurs de `app_registre_mandats_current` et de sa table (§ 4.1), et si le **run**
appelle la re-pose comme le fait le worker (je n'ai trouvé l'appel qu'à
`push_single_annonce_to_supabase.py:710`).
