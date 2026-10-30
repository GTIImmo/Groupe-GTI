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
