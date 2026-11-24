# Ses quatre réponses : les trois patchs à lire avant d'écrire — 24/11 (son 6e mot)

> Son mot : « LES TROIS PATCHS : VAS-Y — SI CE SONT BIEN CEUX-LÀ : les 20 charges de ① ; les 6 suppositions de ④ ; les 2
> corrections de ⑤. ⛔ SI C'EST AUTRE CHOSE, TU ME LES NOMMES AVANT D'ÉCRIRE. Je ne donne pas un accord sur un contenu que je
> n'ai pas lu. »

**Rien n'est écrit.** Les trois patchs de mon message précédent étaient AUTRE CHOSE :
- ①a, les 3 ventes réglées ;
- ①b, les 13 autres Charges ;
- les 6 dates.

④ et ⑤ n'existaient pas encore. Ils sont fabriqués maintenant, et ① est refait avec ta décision ②. Les trois patchs que tu
as nommés sont décrits ci-dessous, ligne par ligne, pour que tu les lises avant ton accord.

Chacun a été joué chez Supabase en **aller-retour à blanc** : le patch, puis son inverse, dans la même transaction. Le retour
est exigé à l'empreinte d'avant, et une erreur voulue annule tout à la fin. Vérifié ensuite : le journal porte ses 46
lignes, et il n'y a ni table de mise de côté, ni sauvegarde, ni colonne neuve. Les suppositions et les chaînes 27195 / 27196
sont intactes, et le carnet est vide.

---

## Patch ① — `supabase/patch_charge_2026-11-24.sql` — les 20 lignes de la Charge, sur le MANDAT

**18 mandats posés**, cases vides. Le carnet et le reflet étaient vides, vérifié chez Supabase. Chaque écriture porte
`origine = classeur` et `ecrit_par = classeur:<ligne>`.
- **Les 5 ventes réglées, en tête (32 000 €) :**
  - 125888d3 acquéreur (47542 / 17840) ;
  - 5YUGE9KA acquéreur (23297 / 17564) ;
  - 78004641 acquéreur (17548 / 17481) ;
  - **cc33cc38 vendeur (46338 / 17322)** et **df0ce30c acquéreur (47174 / 17639)**, les deux mandats que ta décision ②
    tranche.
- **Les 13 autres :**
  - vendeur : 1eec6575, 2b924f5f, 4cbc128d, 55b49232, 5e4c8881, 70740f2f, 729ba8dc, b72db9d5, b7439331, ffcf30e6 ;
  - acquéreur : 54376c72, b43e76f5, f90b0418.
- **2 lignes NOMMÉES au journal, avec leur valeur, sans écriture au carnet :**
  - afd672fa « acquéreur » (annulée), écartée pour cc33cc38 ;
  - 2c2566d7 « vendeur » (annulée), écartée pour df0ce30c.
  - La raison, la tienne : une ligne annulée n'a jamais donné lieu à facture.

**Le reste du patch :**
- le reflet est reposé annonce par annonce, et aucun autre reflet ne bouge ;
- sauvegarde datée du registre des mandats de ces 18 annonces ;
- journal : la ligne d'origine et la place (le mandat, la pièce qui le porte).

**Aller-retour à blanc : VERT.** Empreinte avant 95015873, après b58ba6cb, retour 95015873. Dans l'essai, les textes du
journal étaient raccourcis : l'empreinte ne les lit pas.

## Patch ④ — `supabase/patch_suppositions_2026-11-24.sql` — les 6 suppositions de Hektor

**Ce que portent les 6 chaînes.** Chacune ne porte que **deux suppositions** (entrée 50 + sortie 50). On remplace **les
deux**, et chaque ancienne part passe **entière** dans `app_affaire_repartition_mise_de_cote`, avec son numéro de chaîne. Le
nom est résolu comme le 13/11, par ta règle d'homonymie ; par exemple, « CHAMPAGNAC » devient « Joel CHAMPAGNAC ».
- A07EC3DH (chaîne 1875) : entrée GENTES → **DECHAUD** ; sortie GENTES → GENTES.
- DHXRAK9O (9370) : entrée et sortie « utilisateur supprimé » (0) → **NICOLOSI**.
- 72GQRHVB (6391) : « utilisateur supprimé » (0) → **CAVARD**.
- 7IHI7YTJ (4234) : BLANCHARD → **CHAMPAGNAC**.
- QXDW8EQA (1027) : entrée TRIOLLIER → **DI MARIA** ; sortie TRIOLLIER → TRIOLLIER.
- CS38OO8R (27984) : BALMAYER → **CHAMPAGNAC**.

⚠ **À lire.** Pour A07EC3DH et QXDW8EQA, la sortie nomme déjà la bonne personne : seule l'origine change (une supposition
devient une part du classeur). Je remplace quand même les deux moitiés, pour deux raisons :
- ta règle 6 du 23/11 met l'origine dans l'identité d'une part ;
- une chaîne qui garderait une seule supposition resterait à moitié Hektor.

Si tu préfères ne toucher qu'à l'entrée, je retire ces deux sorties.

**La nuit :** `app_repartition_absorber` saute toute chaîne qui porte une part qui ne vient pas de Hektor. Une fois
remplacées, ces 6 chaînes ne reçoivent plus de supposition.

**La table de mise de côté :** c'est celle que nous avions dessinée le 22/11. Elle naît avec ce patch : elle n'existait pas
encore chez Supabase.

**Aller-retour à blanc : VERT.** Avant 1c741e0f, après 91a61e04, retour 1c741e0f.

## Patch ⑤ — `supabase/patch_corrections_2026-11-24.sql` — les 2 moitiés fausses

- **739a0db1** (chaîne 27196) : l'entrée **COUDERT → HERITIER**. La sortie HERITIER est juste.
- **TR42PT5H** (chaîne 27195) : l'entrée **HERITIER → COUDERT**. La sortie HERITIER est juste.
- Les deux entrées avaient été croisées le 13/11. L'ancienne part de chacune est mise de côté avec son numéro.
- **JRE23R1G n'est pas touchée** : sa chaîne 27133 garde la vente réglée 27142.
- Ces deux lignes sont des annulées. Le patch ne leur donne aucune part nouvelle : il corrige la moitié d'une part qui
  existe déjà, comme tu l'as demandé.

**Aller-retour à blanc : VERT.** Avant e6fc6ff4, après adb3c8f8, retour e6fc6ff4.

---

## Les deux dates antérieures, nommées

Dans le patch des 6 dates (`patch_dates_a_l_unite_2026-11-24.sql`, vert à blanc, **pas dans ton accord**), deux lignes
portent au Sheet une date d'annulation **antérieure à la signature de leur compromis** chez Hektor :
- **S3HOG6UL** (ligne 3864) : Annulée **21/10/2021**. Son compromis 17387 est daté du **03/11/2021**, soit 13 jours après
  l'annulation.
- **6U5DQQ4J** (ligne 3865) : Annulée **21/10/2021**. Son compromis 24450 est daté du **28/10/2021**, soit 7 jours après.

Le 16/11, ta règle de C3 a écarté 106 dates « antérieures » de ce genre. Une annulation antérieure au compromis désigne
souvent la tentative d'avant, c'est-à-dire l'offre. Les 4 autres dates du patch sont postérieures au compromis (TR42PT5H,
R0JRVFDC), ou leur compromis n'a pas de date (U0GQ3KTO, IEYXREWQ).

T2GZOY5O (21/11/2021) entrera au journal de ce patch comme **NOMMÉE en réserve**, avec sa valeur. Je le refabrique quand tu
auras tranché les deux dates.

## ⑥ — on attend la vente : nommées, rendez-vous en janvier

Les 11 factures « Vente fixée » attendent leur vente chez Hektor : la facture se posera dessus par le chemin normal (C8). Les
dates de vente que ton contrôleur a mesurées vont du **23/11/2026 au 20/01/2027**. **À revoir en janvier 2027 :** s'il en
reste une sans vente, je reviens vers toi. c6e5299a (offre refusée, annulée, aucune facture) est nommée : rien à faire.

## a5cb141f — la cause commune : la date vide, mesurée

Ta cause est juste : le compromis 6171 porte « 0000-00-00 » ; une pièce sans date ne se prouve pas, donc ne se chaîne pas.

**Mesure sur les 222 paires de chaînes qu'A2 recopie :**
- **Les chaînages déjà coupés aujourd'hui** (la ligne n'est pas sur la chaîne qui porte ses parts), avec une ligne : **6.
  4 sur 6 ont une pièce à date vide** :
  - a5cb141f (6171) ;
  - I847SPN3 (3699) ;
  - IEYXREWQ (27134) ;
  - 959b7669 (28568).
- Les 2 autres (XCK96Z01, 4PW2L3MG) sont coupés sans date vide, donc pour une autre raison. Je ne l'ai pas encore mesurée.
- **Les témoins :**
  - sur tout le registre, 2,2 % des chaînes portent une pièce à date vide ;
  - dans les coupes que fait la vague, 37 sur 207, soit 18 %, huit fois plus.
- **La conclusion :** une cause commune pour les chaînages déjà coupés, et un facteur très surreprésenté dans les coupes. Mais
  ce n'est pas la cause de tout : 170 coupes de la vague n'ont aucune date vide, ce sont les lignes qui partageaient une
  chaîne.

## La paire jumelle — ta lecture, notée

- O6R10ZQA tient le compromis 20073 : le 21/09/2021 y est déjà posé, et la note le confirme. Rien à écrire.
- T2GZOY5O tient l'offre 20075, qui est refusée et n'a donc pas de date d'annulation. Je ne pose pas son 21/11/2021 : il
  est nommé en réserve, avec sa valeur.
- ⚠ Noté : l'acquéreur « PAOLONE » n'est pas résolu en contact. Les deux copies créées le 16/11 le portent seulement en note.
