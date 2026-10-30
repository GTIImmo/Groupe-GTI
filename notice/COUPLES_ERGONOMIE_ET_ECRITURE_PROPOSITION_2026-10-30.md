# PROPOSITION — LES COUPLES DANS L'APP : ESSAIS, ÉCRAN, ÉCRITURE CHEZ NOUS *(30/10/2026)*

> **Demande de Frédéric (30/10)** : *« Il faut faire des tests et analyse ; ensuite je veux avoir une ergonomie claire dans mon app pour
> les couples car actuellement rien n'est prévu pour cela ; propose-moi une logique ergonomique pour les couples, leur modification,
> création, etc. ; et pour finir ce mécanisme doit écrire chez nous immédiatement comme le contact ; audite et explique-moi. »*
>
> **Rien n'est codé, rien n'est écrit chez Hektor ni en base.** Cette note est une PROPOSITION à valider point par point.
> Elle s'appuie sur `notice/AUDIT_COUPLES_CONJOINTS_MENAGES_2026-10-29.md` (§1-9 l'audit, §10 ce que fait Hektor, vu dans son écran).

---

## 0. LE PRINCIPE, EN UNE PHRASE

**Un couple = un FOYER de deux PERSONNES.** Chaque personne est un vrai contact chez nous (son numéro, son téléphone, son e-mail, sa
signature) ; le foyer est un lien entre elles, écrit **chez nous au clic**, que Hektor **confirme** ensuite. C'est le modèle que Hektor
utilise lui-même depuis février 2026 (deux fiches nommées, liées), et c'est celui que tout notre code sait déjà lire.

---

## 1. CE QUE L'AUDIT DU MÉCANISME « CONTACT » A ÉTABLI *(ce sur quoi on s'appuie)*

**La création d'un contact écrit déjà chez nous à l'instant** (L4-b du 21/09 + 8a du 21/10) :
- `app_create_contact_optimistic` (`supabase/patch_l4b_contact_nait_dans_app_2026-09-21.sql:78-138`) tire **notre numéro** (plage
  ≥ 20 000 000, `app_contact_identite_seq`), écrit **la ligne** dans `app_contact_current` (nom, prénom, e-mail, téléphone, négociateur,
  agence), une ligne provisoire (le jeton), puis **un seul travail** `create_hektor_contact` qui emporte `app_identite`.
- 8a (`patch_8a_contact_nait_complet_2026-10-21.sql`, interrupteur `contact_nait_complet` **allumé**) complète la ligne avec 9 champs
  (civilité, téléphone 2, adresse, CP, ville, naissance, lieu, situation, commentaires).
- Au retour, le worker range **le numéro de Hektor** dans la case cible de NOTRE ligne, sans toucher à son identité ; la nuit **adopte**
  la ligne (`adopter_les_nes_dans_l_app()`, b9e58b8) ; le contrôle au retour (8a6) compare ce qui est parti à ce qui revient.

**La modification aussi** : `app_edit_contact_optimistic` (`patch_contact_optimistic_overlay_2026-06-26.sql`) écrit **12 colonnes tout
de suite** (« écrire la colonne EST l'affichage instantané »), pose un travail avec un délai de regroupement, et 8a-B
(`patch_8a5_contact_retour_controle_2026-10-22.sql`) garde ce qui est parti (`app_contact_saisie_modif`) pour juger le retour.

**Ce qui manque pour un couple** (audit du 29/10) : un seul numéro tiré, une seule ligne, le conjoint **seulement** dans la charge du
travail, aucun lien de foyer posé, et la nuit recalcule `couple_role` et le lien **depuis Hektor seul** — elle effacerait un lien que
nous aurions posé avant que Hektor l'ait fait.

---

## 2. LES ESSAIS À FAIRE CHEZ HEKTOR *(avant de coder — ⛔ chacun avec son accord)*

**But** : savoir exactement ce que Hektor fabrique et ce qui fait foi, pour que notre mécanisme lui envoie la bonne chose et sache
retrouver la seconde fiche. **Cible** : un couple **fictif** (« ESSAI COUPLE »), créé à ton nom, supprimé à la fin. **Lectures** : par la
fiche et le formulaire d'édition (comme le 30/10), ~1,5 s entre deux, **≈ 30 lectures en tout**, arrêt net au premier refus.

- **E1 — créer le couple DEPUIS L'APP** (notre vrai chemin, écran « Nouveau contact » → Structure « couple »). On lit : combien de fiches,
  leurs numéros (consécutifs ?), le lien de foyer des deux, la **civilité** posée (notre « M. » écrase-t-il « M./Mme » ?), le bloc
  membre 2 de la première, les champs de la seconde, la **ville du conjoint** (gardée ou perdue sans son identifiant), et **comment
  retrouver le numéro de la seconde** (le worker ne reçoit que celui de la première).
- **E2 — modifier le CONJOINT dans le formulaire de la première** (bloc membre 2), geste fait à la main dans Hektor : la seconde fiche
  suit-elle ?
- **E3 — modifier la SECONDE FICHE directement** : le bloc membre 2 de la première suit-il ? ⇒ E2 + E3 disent **laquelle fait foi**.
- **E4 — archiver la première** : la seconde est-elle archivée ? Puis désarchiver.
- **E5 — supprimer la première** (le nettoyage) : la seconde part-elle ? Sinon la supprimer aussi, et vérifier qu'il ne reste rien.
- **E0 (gratuit, sans écrire)** — sur ~30 ménages réels, comparer le bloc membre 2 et la seconde fiche : s'il n'y a **jamais** d'écart, la
  copie est tenue en continu ; s'il y en a, on saura dans quel sens elle casse. Lecture seule, comme le 30/10.

⚠ Les essais écrivent chez Hektor : **E1 par l'app, E2-E5 à la main dans l'écran de Hektor** (par toi, ou par moi dans ton Chrome **avec
ton accord geste par geste**). Le run de nuit verra le couple d'essai s'il n'est pas supprimé avant 05:00.

---

## 3. L'ÉCRAN — LA LOGIQUE PROPOSÉE *(à valider point par point)*

### 3.1 Créer
- « Nouveau contact » → trois choix en tête : **Une personne · Un couple · Une société** (au lieu du menu « Structure » caché).
- **Un couple** → **deux cartes côte à côte, « Personne 1 » et « Personne 2 »**, chacune avec civilité (M. / Mme), prénom, nom, mobile,
  e-mail, naissance. Les mêmes champs, la même place : rien de spécial à apprendre.
- **Sous les cartes, le foyer** : situation (marié · pacsé · en concubinage · autre), **adresse commune** (une case « même adresse »,
  cochée par défaut ; décochée, la personne 2 a la sienne), et **l'interlocuteur principal** (Personne 1 par défaut).
- **La composition se déduit** : M. + Mme → « M. et Mme » (Hektor `M_Mme`) ; Mme + M. → `Mme_M` ; deux M. → `M_M` ; deux Mme → `Mme_Mme`.
  L'utilisateur ne voit jamais ces codes.
- **Le nom du foyer s'affiche en direct** : « M. et Mme DURAND » si le même nom, sinon « M. DURAND et Mme MARTIN ».
- **Contrôles** : la personne 2 doit avoir **au moins un nom** ; si un **prénom** manque, l'écran prévient sans bloquer : *« sans
  prénom, cette personne ne pourra pas signer »* (règle de la signature du 26/10). Recherche de doublons sur **les deux** personnes.

### 3.2 Voir
- **La fiche d'un contact en couple** : en tête, **le nom du foyer** ; juste dessous, **deux onglets « Personne 1 · Personne 2 »** ; le
  bloc d'identité (téléphone, e-mail, adresse, naissance) est celui de l'onglet choisi. Tout le reste de la fiche (recherches, biens,
  RDV, notes) est celui **du foyer** — les deux personnes le partagent.
- **Un bloc « Foyer »** dans la colonne de gauche : l'autre personne, sa situation, un lien « ouvrir sa fiche ».
- **L'annuaire** : une ligne par foyer, « M. et Mme DURAND — Paul & Marie », trouvable par **le nom, le prénom ou le téléphone de
  l'une ou l'autre**. *(Question à trancher : une ligne par foyer, ou une ligne par personne avec un badge « en couple » — voir §6.)*
- **Les anciens foyers à seconde fiche vide** (133 000 dans Hektor, 12 115 dans l'app) : le bloc Foyer dit **« Conjoint non
  renseigné »** avec un bouton **« Compléter le conjoint »** — on remplit enfin la place qui existe déjà, **en gardant son numéro**.
- **Les orphelines** (2 398, porteuse disparue) : affichées **« Conjoint (fiche sans nom) »**, plus « Contact <n> ».

### 3.3 Modifier
- « Modifier » sur la fiche ouvre **les deux cartes**, comme à la création : on corrige l'une ou l'autre personne, ou le foyer.
- **Sur une personne seule : « Ajouter un conjoint »** → la carte Personne 2 apparaît ; la fiche devient un foyer.
- **« Séparer le couple »** (rare : séparation, erreur) → deux personnes seules ; **rien n'est supprimé**, les biens et recherches restent
  à l'interlocuteur principal, et l'écran le dit avant de valider.
- **« Changer l'interlocuteur principal »** → un clic.

### 3.4 Archiver, supprimer
- Sur une personne en couple, la fenêtre propose : **« Archiver M. DURAND seulement »** ou **« Archiver tout le foyer »** (défaut : tout le
  foyer). Même logique pour supprimer (admin, comme aujourd'hui).
- Ce que fait Hektor de la seconde fiche se saura par E4 / E5 : l'écran s'y alignera.

### 3.5 Les biens, les transactions, la signature
- **Ajouter un mandant / propriétaire / acquéreur** : choisir un foyer ajoute **les deux personnes**, chacune décochable (« seul
  M. DURAND est propriétaire »).
- **Le document de mandat et la signature** : **une ligne par personne nommée**, jamais la fiche vide (corrige le défaut n° 1 de l'audit) ;
  le conjoint **par défaut** (D22) ; une personne sans prénom **bloque** la signature avec le bouton « Compléter le conjoint ».

### 3.6 Le téléphone
- Les mêmes gestes en forme compacte (`MobileLayout` et la forme compacte de l'annuaire) : les deux cartes l'une sous l'autre, le bloc
  Foyer replié. *(Règle : contrôler AUSSI le téléphone.)*

---

## 4. L'ÉCRITURE CHEZ NOUS, IMMÉDIATE *(comme le contact — 8a)*

**Un carnet du foyer, à nous** — table neuve `app_contact_foyer` *(nom à valider)* : `foyer_id` (= le numéro de la personne 1),
`app_contact_id`, `rang` (1 ou 2), `composition` (M_Mme…), `situation`, `principal`, `cree_par`, `cree_le`, `origine` (« app » ou
« hektor »), `retire_le`. **La nuit ne l'écrase JAMAIS** (même règle que le carnet des liens) : le lien de Hektor (`refCouple`) devient
une **confirmation**, comparée au carnet, et un écart est **dit** (sentinelle), jamais corrigé en silence.

**Créer un couple** — une fonction neuve `app_create_couple_optimistic` *(ou une branche de la fonction existante, à décider)* :
1. tire **deux numéros** de notre plage (≥ 20 000 000), un par personne ;
2. écrit **les deux lignes** dans `app_contact_current`, chacune **complète** (les 9 champs de 8a pour chacune) ;
3. écrit **le foyer** dans le carnet, **et** le lien dans `app_contact_current` (`hektor_couple_contact_id` / `app_couple_contact_id` =
   la personne 1) pour que l'écran les fusionne **à la seconde** ;
4. pose **un seul travail** `create_hektor_contact` en statut 2, avec le bloc membre 2 **et les deux numéros** (`app_identite`,
   `app_identite_m2`) ;
5. au retour, le worker range le numéro de Hektor **des deux** fiches dans leur case cible (la façon de trouver le second se saura par
   E1) ; puis le **contrôle au retour** juge les deux.
⇒ **Le couple existe chez nous, complet, avant même que Hektor ait répondu** — et le jour de la coupure, rien ne change pour l'écran.

**Modifier** — `app_edit_contact_optimistic` sert déjà pour chaque personne (écrit tout de suite). En plus : les gestes du foyer
(ajouter / compléter le conjoint, séparer, changer le principal) écrivent **le carnet à l'instant**, puis partent chez Hektor par le
chemin que E2 / E3 auront désigné (bloc membre 2 de la première, ou la seconde fiche).

**Compléter un ancien foyer** — écrit le nom, prénom… **sur la seconde fiche qui existe**, numéro gardé (règle n° 1 « un numéro ne se perd
jamais »). ⚠ Cela lève la règle du 11/09 « ne jamais écrire nom / prénom sur la fiche muette » — qui visait le fait de **recopier le nom
de la porteuse**, pas de saisir le vrai conjoint. **À confirmer par toi.**

**Prudence de mise en service** : tout derrière un interrupteur (`couple_nait_complet`, éteint), additif, aucune fonction existante
retouchée sans garde d'empreinte, essai dans une transaction annulée puis un vrai couple d'essai, comme 8a.

**Ce que ça pourrait casser ailleurs** :
- la nuit (`build_contacts_layer.py`) recalcule `couple_role` et le lien : il faudra qu'elle **lise le carnet** au lieu de l'écraser ;
- `SANS_FICHE_DE_MENAGE` et la fusion `couple:<refCouple>` de la fiche d'un bien : ils doivent reconnaître les foyers nés chez nous ;
- les types de contact, la table des parties, le registre des mandats (trois détections différentes de « la fiche vide », §5 n° 7) ;
- la signature (D22) et le document de mandat ;
- le dédoublonnage des contacts.

---

## 5. L'ORDRE PROPOSÉ

1. **E0** (lecture seule, gratuit) — tout de suite si tu veux.
2. **E1 → E5** chez Hektor, avec ton accord, en une séance d'une heure.
3. **La maquette** des écrans du §3, à valider à l'œil (méthode des refontes : maquette d'abord).
4. **Le carnet du foyer + la création** (§4), derrière son interrupteur, éprouvés comme 8a.
5. **Les gestes du foyer** (modifier, compléter, séparer, archiver).
6. **Les biens / la signature / le document de mandat** (§3.5).

## 6. CE QUI SE DÉCIDE PAR TOI

1. Le principe « un foyer de deux personnes, deux vraies fiches » (§0) — ou un simple bloc conjoint sur une fiche.
2. L'annuaire : **une ligne par foyer** (recommandé, c'est ce que montre Hektor) ou une ligne par personne avec un badge.
3. « Compléter le conjoint » sur les anciennes fiches vides, en écrivant sur la seconde fiche (§4).
4. Archiver / supprimer : le foyer entier par défaut ?
5. Le feu vert pour E0, puis pour E1 → E5.
