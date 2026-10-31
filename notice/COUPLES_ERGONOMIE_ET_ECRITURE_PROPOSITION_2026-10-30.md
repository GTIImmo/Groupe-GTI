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

---

## 7. ✅ DÉCISIONS DE FRÉDÉRIC — 30/10 matin

1. **Deux vraies fiches liées** : OUI.
2. **L'annuaire** : **une ligne par foyer**.
3. « Compléter le conjoint » : **en attente** — il a demandé l'explication de la règle du 11/09 (ci-dessous, §8).
4. **Archiver / supprimer le foyer entier par défaut** : OUI.
5. **E0 par son Chrome, en lecture seule** : OUI (fait, §9). E1 → E5 : pas encore.

## 8. LA RÈGLE DU 11/09, ET POURQUOI « COMPLÉTER LE CONJOINT » N'EST PAS LE MÊME GESTE

La règle (audit §7) a deux morceaux :
- « **une personne, une ligne** » : la fiche vide est masquée quand sa porteuse est connue ;
- **ne jamais écrire `nom` / `prenom` sur la fiche vide CHEZ NOUS SEULEMENT** : la nuit relit Hektor, y trouve la fiche vide, et
  verrait un écart (ou l'effacerait). L'idée rejetée était de **recopier le nom de la porteuse** sur la fiche vide (un champ menteur).

« Compléter le conjoint » est un autre geste : on écrit le **vrai** conjoint, **et on l'envoie à Hektor**. La nuit relit alors chez Hektor
ce que nous y avons écrit : pas d'écart. Le danger que la règle visait (une écriture locale que Hektor ignore) disparaît, à une condition :
que l'envoi à Hektor remplisse **bien la fiche existante** — ce que seuls les essais diront (§9, constat 3).

## 9. E0 — FAIT LE 30/10 08:45-08:50, LECTURE SEULE (31 requêtes, une toutes les 4 s, 0 refus)

Échantillon tiré au hasard dans le miroir (graine 20261030), couples vivants : 15 récents (≥ 02/2026, deux fiches nommées), 10 anciens
(deux fiches nommées), 5 à seconde fiche vide. Comparaison par empreintes (aucun nom n'a quitté la page). Champs : nom, prénom, premier
e-mail, premier téléphone du bloc membre 2 de la première fiche ↔ la seconde fiche du miroir.

- **Récents : 15 sur 15 identiques**, champ par champ (les vides sont vides des deux côtés). Le formulaire porte `M_Mme`.
- **Anciens : 10 sur 10 identiques** — le nom seul est rempli, des deux côtés. ⚠ Le miroir dit « Mr./Mme », le formulaire dit `M_Mme` :
  **« Mr./Mme » est l'ÉTIQUETTE que l'API rend pour la valeur `M_Mme`**, pas une autre valeur. Le défaut n° 5 de l'audit (« Mr./Mme
  inconnu de l'écran ») est donc une simple correspondance d'étiquette.
- **Seconde fiche vide : 5 sur 5, la première fiche n'a PAS de bloc membre 2** (civilité vide ou « M. »). Pour Hektor, la porteuse est
  **une personne seule** ; la fiche vide est une place réservée qui ne pend à aucun formulaire.

Mesuré ensuite dans le miroir (porteuse nommée, deux fiches vivantes) : sur **35 914** paires à seconde fiche vide, **33 660** ont une
porteuse à civilité de personne seule (vide 21 183, « M. » 12 459, « Mme. » 18) ; **2 245** ont la civilité couple sans conjoint saisi.

**Ce qu'E0 établit :**
1. La copie bloc membre 2 → seconde fiche est **tenue sans écart** sur les deux époques : la seconde fiche est bien le conjoint.
2. Notre lecture peut donc se passer du formulaire : **la seconde fiche suffit** pour voir le conjoint (elle est dans le miroir) — pour les quatre
   champs mesurés ; adresse, naissance et commentaire n'ont pas été comparés.
3. **« Compléter le conjoint » n'est pas trivial** pour 33 660 foyers : il faut passer la porteuse en civilité couple et remplir le bloc
   membre 2. Hektor remplit-il alors **la place vide existante**, ou en crée-t-il **une nouvelle** (la vide restant orpheline) ? ⇒ à
   ajouter aux essais : **E6 — sur le couple d'essai, créer une personne seule, puis la passer en couple** et lire les fiches.

## 10. E1 → E6 — FAITS LE 30/10 09:05-09:30 (accord de Frédéric « tu as mon accord pour les tests sur couple »)

Cible : contacts **fictifs** sous « FRANCK GERPHAGNON — Compte formation » (négociateur 2), e-mails `@example.com` (domaine réservé,
jamais livré), aucun téléphone. ~25 lectures, 0 refus. Gestes chez Hektor : 2 créations par l'app, 2 modifications à l'écran, 1
archivage + 1 désarchivage (ordre `archiveContact` du worker), 1 suppression à l'écran, 1 « Transformer en couple ».

- **E1 — créer le couple DEPUIS L'APP** (Propriétaire, structure Couple, civilité laissée vide) : le travail `create_hektor_contact` passe
  en **10 s** ; Hektor fabrique **DEUX fiches consécutives** — 606071 (Un, bloc membre 2 = Deux) et **606072** (Deux, sans bloc). Civilité
  **`M_Mme` sur les deux** (posée par Hektor : notre vide n'a rien écrasé — ⚠ un « M. » choisi à l'écran n'a PAS été essayé). Les e-mails
  sont à leur place. Fil d'Ariane Hektor : « ESSAI COUPLE Un / Deux ».
  ⚠ Chez nous après le rafraîchissement ciblé : **une seule ligne** (20000021 ↔ 606071), lien de couple = elle-même (porteuse) ; **606072 et
  « Deux » ne sont NULLE PART chez nous** (le rafraîchissement ne lit que la première) ; notre civilité vide, puis « M_Mme » brut dans
  `display_name` (« M_Mme Un ESSAI COUPLE ») — **le code s'affiche tel quel dans l'annuaire, aussi sur de vraies fiches**.
  ⚠ La charge porte `send_rgpd_email: true` : Hektor envoie l'e-mail d'activation RGPD au contact (et, côté écran Hektor, l'interrupteur
  « Envoyer l'email d'activation… » est sur OUI par défaut).
- **E2 — modifier le conjoint dans le formulaire de la première** (Madame « Deux » → « DeuxE2 ») : **la seconde fiche suit à l'instant**.
- **E3 — « modifier la seconde fiche »** : à l'écran, Hektor **ne le permet pas** — ouvrir 606072 montre le formulaire du **FOYER ENTIER**
  (Monsieur Un / Madame). Modifier Madame depuis là (« DeuxE3 ») met à jour les deux. ⇒ **chez Hektor, le foyer s'édite d'un bloc ; la
  première fiche fait foi, la seconde est son reflet.** ⚠ Reste NON essayé : modifier 606072 **par notre worker** (il posterait le formulaire
  de 606072 seul, sans bloc membre 2) — **E3-bis**, possible seulement quand 606072 sera chez nous (après un run) : sur un nouveau couple d'essai.
- **E4 — archiver la première** (`archiveContact archive=true`, réponse « Modification archivage ok ») : **la seconde est archivée aussi**
  (recherche Hektor : « aucun résultat parmi les actifs » ; dans les archives, le foyer et ses DEUX membres « archivé »). **Désarchiver la
  première remet les deux en actif.** ⚠ Le geste « Archiver ce contact » de l'APP ouvre un `window.confirm` natif ; je l'ai contourné par
  l'ordre du worker — le chemin de l'app (`app_console_archiver_contact_optimistic`) n'est donc PAS éprouvé ici.
- **E5 — supprimer la première** (menu ⋮ → « Supprimer ce contact » → Oui) : **la seconde part aussi** — plus rien, archives comprises ; les
  formulaires de 606071 et 606072 reviennent vides.
- **E6 — une personne SEULE créée par l'app** (« ESSAI SEUL Un », 606073) : **AUCUNE place vide n'est réservée** (606074 n'existe pas) ; sa
  liste de civilités n'offre que M. / Mme. / Mlle. Son menu ⋮ offre **« Transformer en couple »** → fenêtre « Vous souhaitez transformer ce
  contact seul en couple ? » avec la question **« Le contact est-il déjà existant dans Hektor ? » (Oui / Non)** ⇒ **Hektor sait rattacher une
  fiche EXISTANTE comme conjoint** (piste pour les 33 660 places vides). Avec « Non » : formulaire « Ajouter un nouveau contact » en Couple
  dont **la colonne Madame est PRÉ-REMPLIE d'une copie de Monsieur** (nom, prénom, e-mail identiques — piège de saisie) et une date
  d'**auto-archivage** posée à un an (30-10-2027). Après « Passer à l'étape suivante » : **page blanche**, et **606073 a DISPARU** (ni actif
  ni archivé, aucune fiche 606074-606078). ⛔ **Imprévu : arrêt des essais ici.** Soit le parcours supprime la fiche seule et ne crée le couple
  qu'au bout d'une étape que la page blanche a empêchée, soit autre chose — **à ne JAMAIS confier au worker sans l'avoir compris**.
- Avant sa suppression, le couple d'essai se montrait, côté Hektor, sous la forme « M./MME ESSAI COUPLE » ; dans la liste de recherche, la première est
  « M. ESSAI COUPLE Un » et la seconde « ESSAI COUPLE » sans prénom. Le menu ⋮ d'un couple propose **« Dissocier le couple »** (= notre
  « Séparer ») — non essayé.

**Ce que ça décide pour notre mécanisme (§4) :**
1. **Créer** : notre chemin marche ; il faut **apprendre le numéro de la seconde fiche** au retour (aujourd'hui personne ne le lit : la nuit
   seule la ramènera, et notre carnet ne doit pas l'attendre) — piste : premier+1, **à confirmer par une lecture** (consécutif sur 370/394
   ménages, pas sur tous).
2. **Modifier le conjoint** : écrire **dans le bloc membre 2 de la PREMIÈRE** (E2) — jamais la seconde seule, tant qu'E3-bis n'a pas parlé.
3. **Archiver / supprimer** : un seul ordre sur la première suffit, **le foyer suit** — conforme à ta décision « le foyer entier par défaut ».
   Archiver ou supprimer **un seul** membre n'existe pas chez Hektor : il faudra « Dissocier » d'abord (à essayer).
4. **« Compléter le conjoint »** sur les 33 660 : passe par « Transformer en couple » → « déjà existant : Oui » → la place vide ? **NON essayé,
   et E6 montre que ce parcours peut faire disparaître une fiche** ⇒ essai dédié, sur fiches d'essai, avant toute décision.

**Restes de l'essai, à nettoyer (accord requis — écriture dans notre base) :** nos lignes **20000021** et **20000022** visent des fiches
supprimées chez Hektor (606071, 606073). Chez Hektor : rien ne reste (vérifié par la recherche, archives comprises).

## 11. NETTOYAGE DES FICHES D'ESSAI, ET CE QUE LES ESSAIS CHANGENT À L'ÉCRAN *(30/10, accord « Retire les »)*

**Nettoyage fait** (même chemin que le geste « Supprimer » de l'app) :
- Supabase : les 2 lignes `app_contact_current` 20000021 / 20000022 retirées (sauvegarde dans le dossier de travail de la session,
  `sauvegarde_essais_couple_20000021_22_20261030.json`). Les 2 traces `app_contact_saisie_modif` (contrôle de création, 0 écart) sont
  **gardées**, comme le geste de l'app les garde.
- Local : `delete_local_contact.py --contact-id 2000002x --cible-hektor 60607x` → miroir (fiche, état, réponse brute) et couche locale.
- Contrôle : 0 reste des deux côtés ; témoins positifs (9 contacts nés dans l'app chez Supabase et en local, 71 fiches voisines au miroir).

**Trou trouvé en passant (non mesuré en ampleur)** : un contact supprimé **directement chez Hektor** (pas par l'app) ne disparaît pas
chez nous. La nuit ne relit que les fiches de la liste de Hektor, donc elle ne reçoit jamais le « introuvable » qui marquerait l'absence ;
et un contact né dans l'app (≥ 10 000 000) est protégé de toute suppression par le push (`est_ne_dans_l_app`). Le nettoyage n'a lieu que
par le geste de l'app (`runDeletedContactLocalCleanup` + `cleanupSupabaseContactRows`).

**Ce que E1 → E6 changent au §3 et au §4** :
- **Modifier** : Hektor modifie le foyer d'un bloc par la **première** fiche → dans l'app, modifier la personne 2 = un travail sur la
  fiche 1 avec le bloc `_m2`. (À éprouver : E3-bis, par notre worker.)
- **Archiver / supprimer** : la cascade est faite par Hektor → le défaut « foyer entier » (décision 4) est gratuit. « Archiver M. seul »
  n'existe pas chez Hektor sans « Dissocier » d'abord (non essayé) → **option à retirer du §3.4, sauf décision contraire**.
- **Ajouter un conjoint à une personne seule** : ⛔ ne PAS passer par « Transformer en couple » réponse « Non » (fiche disparue, E6).
  Deux chemins restent à essayer : réponse « Oui », ou écrire le bloc `_m2` dans le formulaire de la fiche seule.
- **Créer** : marche déjà ; il manque d'apprendre le numéro de la seconde fiche au retour (via `_m2` / `refCouple` de la première,
  ne pas supposer « +1 ») et de la ranger chez nous avec le lien.
- **Afficher** : traduire `M_Mme` (et `Mme_M`, `M_M`, `Mme_Mme`) partout où l'app compose un nom.

## 12. CE QUE J'AVAIS RATÉ — LE PROJET AVAIT PRÉVU LA PAIRE *(30/10, question de Frédéric)*

**Le plan existait** : `C.9-couple` (liste, ajoutée le 11/09) et **`C.9-couple-b`** (chapitre CH17 de
`CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md`) : « l'app fabrique la paire du ménage (deux fiches, deux numéros, le lien), derrière
un réglage » — réserver 2 numéros, écrire les 2 fiches et le lien dans la même transaction, ne jamais créer de 3e fiche chez Hektor ;
critère de fin : « 2 lignes aux `app_couple_contact_id` croisés dès le geste, toujours 2 fiches (pas 3) après le retour de Hektor ».
Prérequis : la mesure d'une heure (`C.9-couple-a`, « une fiche ou deux ? ») — **c'est E1, faite le 30/10 : deux fiches**.
Décision restée ouverte : pendant la cohabitation, envoyer le bloc conjoint (Hektor crée la 2e fiche) ou deux fiches déjà liées.
**Aucun code de la paire n'a été écrit** (liste, 07/10).

**Ce que j'ai mal dit au §10/§11** : « la seconde fiche n'arrive pas chez nous, le conjoint n'est rangé nulle part ». Vrai **à
l'instant** seulement. **La nuit l'amène** : le push envoie les contacts « actifs ou éligibles », le lien `refCouple` est porté, la fiche
d'un bien fusionne le ménage (« mandants mariés »). Mesure : **1 609 secondes fiches nommées** dans l'app, **1 380** reliées à leur
porteuse. ⚠ Pas prouvé pour un couple **né dans l'app** : les fiches d'essai ont été retirées avant une nuit.

**La modification** : le worker sait déjà écrire le conjoint par la fiche 1 (`nom_m2`, `prenom_m2`… l. 18502-18514), mais l'écran
« Modifier » traite tout contact en « personne seule » (`contactIdentityInputFromContact`, conjoint vide) : rien n'est effacé chez Hektor
(un champ vide n'est pas envoyé), mais on ne peut pas modifier le conjoint depuis l'app.

**Trouvaille : `app_couple_contact_id` est PÉRIMÉ** — 36 183 liens sur 37 458 portent l'ANCIENNE série (< 10 000 000), d'avant la
renumérotation du 23/09 ; 1 275 seulement sont justes. Aucun code ne le lit aujourd'hui (audit du 29/10) : pas de dégât visible, mais
**rien ne doit s'appuyer dessus avant réparation**.

**Le numéro de la seconde fiche n'est PAS toujours « +1 »** : depuis février 2026, 377 paires sur 392 (miroir). Le worker devra le
**lire et le vérifier** (`refCouple` de la seconde = la première), jamais le supposer.

## 13. « FAIRE COMME HEKTOR » — QUESTIONS DE FRÉDÉRIC DU 30/10 ET RÉPONSE PROPOSÉE *(rien codé)*

Ses questions : « ce ne sont pas forcément des mandants mariés, plutôt des couples » ; « comment verra-t-on qu'il y a une deuxième fiche
si on les réunit » ; « à la création d'un document, on choisira la fiche couple et on aura deux fiches séparées : comment ce sera utilisé » ;
« il faudrait faire comme Hektor ».

- **Le libellé** : « mandants maries » est écrit en dur par la fusion de la fiche d'un bien (`App.tsx:7272`) → à remplacer par
  **« Couple »** (pas forcément mariés, pas forcément mandants). Petit correctif, avec la traduction de `M_Mme`.
- **Comme Hektor** : un foyer = **une page** « M. et Mme NOM », **deux membres dedans**, chaque membre est **une vraie fiche** (la seconde
  est le miroir du membre 2, §10.1 de l'audit). Recherches, biens, RDV, notes = au foyer ; téléphone, e-mail, naissance, consentement,
  signature = à la personne.
- **Voir la seconde fiche** : sur la page du foyer, deux onglets (un par personne, avec son numéro et « ouvrir sa fiche ») ; dans
  l'annuaire, une ligne par foyer avec les deux prénoms ; une seconde fiche vide se dit « Conjoint non renseigné » + « Compléter ».
- **Les documents** : on choisit **le foyer** une fois ; le document met **une ligne par personne** (chacun signe, art. 215 C. civ. pour
  le logement de la famille), chacune décochable. **Déjà en partie dans le code** : `buildMandatDocumentMandants` (`App.tsx:4413`) déplie
  les membres d'un couple — mais une fiche vide y devient un mandant (défaut n° 1 de l'audit, non corrigé). La signature a besoin de
  l'e-mail / téléphone **de chaque personne** : c'est pour ça qu'il faut deux vraies fiches.

## 14. MAQUETTE — ANNUAIRE ET PAGE DU FOYER *(30/10, demande de Frédéric, rien codé)*

Artifact privé : https://claude.ai/artifact/LPHthrJJeW6gaNz8RXufmR — 3 planches, noms fictifs :
1. **l'annuaire** : un couple = une ligne, deux pastilles d'initiales qui se chevauchent, « M. et Mme NOM » + les deux prénoms,
   l'étiquette « Couple · 2 fiches » ; une coordonnée par personne (initiale devant) ; un ancien couple au conjoint jamais saisi =
   pastille pointillée « ? », « Couple · conjoint à compléter », bouton « + Compléter le conjoint » ; filtres « Couples » et
   « Conjoint à compléter » ; une personne seule garde une seule pastille ;
2. **la page du foyer** : nom du foyer, deux onglets (une personne chacun, avec son numéro de fiche et « ouvrir sa fiche seule »),
   bloc « Foyer » (situation, adresse, interlocuteur principal), biens / recherches / activité marqués « commun au foyer », et le choix
   dans un document : le foyer choisi une fois, une case par personne avec son téléphone de signature ;
3. **le téléphone** : la même chose en cartes ; rechercher un prénom retrouve le foyer.
À valider à l'œil par Frédéric avant tout code.

**Reprise du 30/10 au soir (remarques de Frédéric)** : pas de filtres « Couples » / « Conjoint à compléter » ; « Notaires » existe
dans les segments ; et **le design actuel doit être gardé**. La maquette est REFAITE sur le vrai écran : la feuille de style
publiée de l'app (bienvu) et le balisage réel de `ContactsScreen` / `ContactDetailPopupV2`, noms fictifs. Seuls ajouts : une tuile
décalée derrière l'avatar, l'étiquette « Couple · prénoms » (orange « conjoint à compléter » si la seconde fiche est vide), un
téléphone par personne avec son initiale ; sur la fiche, l'étiquette « Couple · mariés », deux onglets (une personne chacun, son
numéro de fiche) qui pilotent les coordonnées, et les rôles par personne dans « Biens & mandats liés ». La planche téléphone est
retirée (elle ne suivait pas le vrai rendu mobile, `MobileLayout`).

**✅ VALIDÉE par Frédéric le 30/10 au soir** (« Oui cela me convient ») : la tuile décalée, l'étiquette « Couple · prénoms »
(orange si le conjoint est à compléter), un téléphone par personne, et sur la fiche l'étiquette « Couple · mariés », les deux onglets
et les rôles par personne.

## 15. LE POINT 2 — CRÉER LA PAIRE : CE QUE L'AUDIT DU 30/10 AU SOIR AJOUTE *(lecture seule, rien codé)*

- **La première fiche ne connaît PAS la seconde.** Chez Hektor, la première porte `refCouple` = elle-même, la seconde porte
  `refCouple` = la première (mesuré sur les paires 606065 → 606070 du miroir). Ni le détail de la première, ni la réponse de
  création (`parseHektorCreatedContactId`) ne donnent le numéro de la seconde. ⇒ le worker doit le **chercher** : lire le détail de
  « première + 1 » et ne l'accepter **que si** son `refCouple` vaut la première (consécutif 377 fois sur 392), sinon les quelques
  suivants, une lecture par seconde.
- **Pourquoi c'est vital** : l'adoption de la nuit (`adopter_les_nes_dans_l_app`) rattache une fiche de Hektor à notre numéro
  **par la case cible** (`hektor_target_id`). Si la ligne de la personne 2 n'a pas sa cible avant la nuit, le registre donne à la
  seconde fiche de Hektor un **nouveau numéro** (série 10 M) : la personne 2 existerait **deux fois** chez nous. ⇒ il faut un
  **second filet** dans la nuit : rattacher une fiche dont le `refCouple` vise une première née dans l'app et dont la personne 2
  attend sa cible.
- **Ce que le worker envoie déjà** pour le conjoint (l. 18502-18516) : nom, prénom, e-mail, portable, adresse, ville, code
  postal. La charge porte `send_rgpd_email: true` (e-mail d'activation de Hektor).

## 16. POINT 2 — PIÈCES A ET B ÉCRITES ET ÉPROUVÉES *(31/10 matin, « go » de Frédéric « Oui vas y »)* — ⛔ RIEN N'EST POSÉ

**A — la base** : `supabase/patch_couple_paire_a_la_creation_2026-10-31.sql` (+ `_INVERSE`, + `_REPETITION`).
- Interrupteur **`couple_nait_complet`, posé ÉTEINT**.
- Fonction neuve `app_contact_creer_conjoint` : couple + nom du conjoint saisi (l'écran l'exige) → un 2e numéro de notre plage, la
  ligne de la personne 2 (nom, prénom, e-mail, portable, adresse, CP, ville du conjoint ; négociateur et agence de la personne 1), et
  le lien **comme la nuit le pose** : personne 1 → elle-même, personne 2 → la personne 1, `couple_role` vide.
- Dans `app_create_contact_optimistic` : un bloc à part après 8a (un échec ne fait jamais tomber la création) et la charge du travail
  emporte `app_identite_m2` seulement s'il y a une personne 2. Gardes : empreinte `95fde328…`, marque, 3 ancres d'une ligne.
- **Non touchée, exprès** : la porte « créer un mandant » (elle envoie toujours une personne seule, l. 20778).
- **Répétition jouée le 31/10, tout annulé : 26 mesures vertes, 0 erreur** — éteint = comme avant (pas de personne 2, pas de lien) ;
  allumé + couple = 2 lignes reliées, nom/mail/téléphone/agence/négociateur justes, case cible vide ; allumé + personne seule = rien ;
  allumé + couple sans nom de conjoint = rien ; mandant intact ; l'inverse redonne l'empreinte d'avant. Contrôle après : 0 reste.
  ⚠ 5 numéros consommés (20000023-27) : un trou dans la série, rien de plus.

**B — le worker** : `rangerSecondeFicheDuCouple` (`Console/console_job_worker.js`, appelée dans `executerCreationContactHektor`
seulement si la charge porte `app_identite_m2`) + `phase2/sync/contact_seconde_fiche_from_api.py`.
- Lit au plus les **3 fiches suivantes** (mesure : 379 secondes fiches sur 393 sont la suivante, 1 deux plus loin), n'accepte que
  celle dont `refCouple` = la première, **arrêt net** au premier refus ou si Hektor ne répond pas ; un 404 passe à la suivante.
- Pose la case cible de la personne 2 **seulement si elle est vide et que personne d'autre ne porte ce numéro** ; sinon rien, et
  c'est écrit au journal (`couple_seconde_fiche`). Jamais d'exception : le travail ne tombe pas.
- **Pas de relecture de la personne 2** dans le travail : trop tôt, elle écrirait le lien avec le numéro de Hektor de la première ;
  la nuit la fait quand le registre connaît les deux paires.
- **Essais** : `phase2/sync/test_contact_seconde_fiche.py` **13/13** (faux Hektor : +1, +2, fiche d'un autre couple, personnes
  seules, 404, refus 429, panne) · `Console/test_couple_seconde_fiche.js` **14/14** (code réel découpé : écriture ciblée, conflit,
  case déjà pourvue, script en panne, garde de l'appel). **Une lecture réelle** (606069 → **606070**, `refCouple` présent dans
  ContactById) : la forme de l'API est prouvée.

**Reste, dans l'ordre** :
1. **Pièce C** (le filet de la nuit, si B rate) — touche le run de nuit : à présenter avant de coder.
2. Frédéric : coller le patch A (après la répétition), pousser, redémarrer le service worker qui porte `create_hektor_contact`
   **file vide** — interrupteur toujours éteint.
3. Allumer + **un couple d'essai réel** (fictif, comme E1, accord requis) → contrôler les 2 lignes, la case cible de la personne 2,
   puis **la nuit** : toujours 2 fiches, aucune 3e, aucun numéro de plus.
⚠ **Non mesuré** : si Hektor envoie l'e-mail d'activation RGPD au conjoint aussi (`send_rgpd_email: true`).

## 17. PIÈCE C — LE FILET DE LA NUIT : PROPOSITION *(31/10, rien codé, attend le « go »)*

**Le trou qu'elle ferme** : si le worker n'a pas trouvé la seconde fiche (Hektor lent, refus, fiche plus loin que 3), la personne 2
reste sans case cible. La même nuit, le registre (`registre_contacts.py`) voit arriver la seconde fiche de Hektor, ne la reconnaît
pas, et lui donne un numéro de la série 10 M : la personne 2 existe deux fois.

**Ce que fait la nuit aujourd'hui, dans l'ordre** (`run_full_pipeline.ps1`) : `normalize_source` (le miroir) → descente de la
correspondance (`descendre_correspondance_contacts.py`, 62 368 paires, lit la vue `app_v_correspondance_identite_cible`) → build
de la couche → registre (adoption des nés dans l'app **par la case cible**, puis numéros neufs) → seconde passe → push.

**La pièce C** : un script neuf, `phase2/identite/rattacher_secondes_fiches.py`, une étape **non bloquante** placée **juste avant
la descente de la correspondance**. Il ne lit **que le miroir et Supabase — aucune requête chez Hektor**.
1. Il demande à Supabase les personnes 2 nées dans l'app **sans case cible** (≥ 20 000 000, liées à une personne 1 qui, elle, a sa cible).
2. Dans le miroir, il cherche la fiche dont le `refCouple` vaut la cible de la personne 1.
3. Il n'écrit la case cible de la personne 2 **que si** : une seule candidate, aucun autre contact ne porte déjà ce numéro, et
   **le nom de famille concorde** (un témoin en plus de Hektor). Même écriture que B, et seulement si la case est vide.
4. Sinon il n'écrit rien, il le **dit** au journal du run et sort en code 1 (l'étape apparaît en échec, le run continue).
La descente ramène alors la paire, le build range la seconde fiche sous **notre** numéro, et le registre l'adopte : plus de 3e fiche.

**Mesure du 31/10** : 9 contacts nés dans l'app, **aucun couple** → la pièce C n'aurait rien à faire ce soir (dormante jusqu'au
premier couple créé interrupteur allumé). Idempotente : si B a réussi, elle ne trouve rien.

**Ce que ça pourrait casser ailleurs** :
- c'est une **modification du run de nuit** (une étape en plus) → accord requis, comme tout geste sur le run ;
- une mauvaise association rattacherait la personne 2 à la fiche d'un autre → trois gardes (lien de Hektor exact, candidate unique,
  nom concordant) ; dans le doute, rien n'est écrit ;
- si elle échoue ou ne tranche pas, la nuit fait **ce qu'elle fait aujourd'hui** (numéro de plus pour la seconde fiche) : la pièce
  C n'aggrave rien, elle ne fait que réparer quand elle est sûre ;
- elle écrit dans Supabase pendant la nuit (le run le fait déjà, avec la même clé) ; en cas de doute, une option `--a-blanc` dit ce
  qu'elle ferait sans rien écrire.
**Essais prévus** : hors ligne (miroir et Supabase factices : cas trouvé, deux candidates, nom différent, déjà pourvu, rien à
faire) ; puis une passe `--a-blanc` sur le vrai miroir (attendu : 0 personne 2 à rattacher).

## 18. PIÈCE C — ÉCRITE, ÉPROUVÉE, BRANCHÉE AU RUN *(31/10, « go » de Frédéric « Oui »)*

- **Script** : `phase2/identite/rattacher_secondes_fiches.py` (option `--a-blanc`). Lit Supabase (personnes 2 nées dans l'app sans
  cible, et la cible de leur personne 1) et le miroir ; aucune requête chez Hektor. N'écrit (case cible vide seulement) que si : une
  seule fiche du miroir désigne la personne 1, nom de famille concordant (accents, tirets, casse neutralisés), numéro porté par
  personne d'autre **ni dans Supabase ni dans le registre local**. « Attendre » (sortie 0, sans alarme) si la personne 1 n'a pas
  encore sa cible ou si la fiche n'est pas encore au miroir ; « DOUTE » (rien d'écrit, sortie 1) sinon ; sortie 2 si lecture impossible.
- **Essai hors ligne** `phase2/identite/test_rattacher_secondes_fiches.py` : **13/13**.
- **Passe à blanc sur les vraies données** : « rien à faire » (attendu : 0 personne 2 en attente, mesuré aussi en SQL).
- **Témoin positif sur deux vrais couples récents** (lecture seule, aucun nom affiché) : pour 606069 il trouve **606070**, pour
  606067 il trouve **606068**, nom concordant — et il **refuse** d'écrire parce que le registre local leur donne déjà une identité
  (10650913, 10650911) : c'est juste, ce sont des couples nés chez Hektor. Avec un nom faux : refus aussi.
- **Branchée** dans `run_full_pipeline.ps1`, étape « phase2 secondes fiches des couples », **après normalize_source, juste avant la
  descente de la correspondance**, non bloquante, 1 essai, clé `phase2.secondes_fiches_couple`. Syntaxe du run vérifiée (0 erreur).
  ⚠ **Elle tournera dès cette nuit** (le run lit ce fichier sur le disque) : dormante, elle dira « rien à faire ».
- ⚠ **La clé de battement n'existe pas encore** : `supabase/patch_couple_piece_c_battement_2026-10-31.sql` (une ligne de
  configuration, `medium`, comme ses voisines) — **à coller par Frédéric**, sinon un « DOUTE » partirait dans le vide.
- ✅ **Clé de battement POSÉE le 31/10** (accord de Frédéric « Colle ») : la ligne `phase2.secondes_fiches_couple` existe dans
  `app_worker_registry` (medium, optional_pipeline_step, active), relue après l'écriture. ⏰ **01/11 au matin** : le journal du run
  doit porter « phase2 secondes fiches des couples » → « rien a faire », code 0, et la clé un battement daté de la nuit.

## 19. POSE DU 31/10 *(Frédéric : « Mais fais le »)*

- ✅ **Patch A POSÉ en base** (`patch_couple_paire_a_la_creation_2026-10-31.sql`), **7 contrôles verts** : interrupteur
  `couple_nait_complet` **ÉTEINT**, bloc présent une fois, fonction neuve muette éteinte et fermée à anon / authenticated, droits de
  la porte inchangés, porte mandant intacte, empreinte après pose = celle de la répétition (`278d5570…`).
- ⛔ **Redémarrage de `HektorConsoleWorkerActions` REFUSÉ par Windows** (« Impossible d'ouvrir le service » : il faut une console
  administrateur). File vérifiée vide juste avant (0 en attente, 0 en cours). Le service tourne toujours sur le code du 29/10 15:27:51,
  **sans la pièce B** — sans conséquence tant que l'interrupteur est éteint (la charge ne porte pas `app_identite_m2`).
  Vérifié aussi : les lignes non commitées de l'autre session (Youtrust, document de mandat) sont des travaux du service
  **Documents**, pas Actions — redémarrer Actions ne les met pas en service.
- **Reste à Frédéric** : redémarrer Actions dans une console administrateur, file vide ; pousser les commits.
- **Ensuite seulement** : allumer l'interrupteur et créer un couple d'essai fictif (accord requis).
- ✅ **Les 4 services redémarrés par Frédéric le 31/10 à 09:35:14-16** (heure des processus, mesurée) : le fichier lu contient la
  pièce B (`rangerSecondeFicheDuCouple` présent). Battements des 4 à 09:36, sans erreur ; file vide (0 en attente, 0 en cours).
  ⚠ Le service **Documents** a chargé AUSSI les lignes non commitées de l'autre session (Youtrust, document de mandat) : elles sont
  désormais en service.
- **Prochaine marche** : allumer `couple_nait_complet` + un couple d'essai fictif (accord requis), puis juger la nuit.
