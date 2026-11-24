# Recrutement — le modèle d'e-mail de premier contact (BROUILLON, à relire)

> **R7.1 du chantier** (`notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md`, §14).
> **Décision D5** : j'écris un brouillon ; ⏸ **Frédéric le relit avant le premier envoi**. Rien n'est branché :
> aujourd'hui, « Écrire un e-mail » ouvre la messagerie de l'administrateur, vide, et l'envoi se note dans le fil.
> Écrit le 24/11/2026.

## Ce que ce texte doit tenir (règles déjà écrites dans la note du chantier)

- **Article 14 du RGPD** : la personne n'a pas donné ses coordonnées elle-même, donc on l'informe **au plus tard au
  premier contact** — qui traite ses données, pourquoi, sur quelle base, d'où elles viennent, quoi exactement,
  combien de temps, qui les voit, ses droits, la CNIL (note §4, point 2 ; affaire KASPR).
- **Un message lié à sa profession** (prospection entre professionnels, base « intérêt légitime ») et **un moyen
  simple de refuser** (note §5 et §10).
- **Dire d'où vient la coordonnée** : la source exacte de SA fiche (le réseau, ou le registre public).
- **Les durées réelles** du chantier : effacement à **3 ans** sans échange ; copies de sauvegarde gardées **un an
  au plus** (6 sauvegardes de deux mois = un an ; copies quotidiennes 90 jours ; image du serveur 14 jours).
- ⛔ Aucun nom de personne de GTI n'est écrit dans ce document : l'expéditeur est une case à remplir.

## Les cases

- `{prenom}` : le prénom de la personne (la valeur corrigée par nous si elle existe).
- `{agence_proche}` : notre agence la plus proche d'elle.
- `{source}` : d'où vient sa coordonnée, selon sa fiche :
  - fiche d'un réseau → « l'annuaire public des conseillers {nom du réseau} » ;
  - fiche du registre → « l'annuaire public des entreprises (registre national) » ;
  - fiche ajoutée à la main → ce n'est PAS ce modèle (voir plus bas).
- `{lien_source}` : l'adresse de sa fiche publique, quand elle existe.
- ⏸ **À remplir par Frédéric** : `[EXPÉDITEUR]` (prénom, nom, fonction, téléphone), `[CE QUE GTI PROPOSE]`,
  `[ADRESSE POSTALE DE GTI]`, `[ADRESSE DE CONTACT POUR LES DONNÉES]`.

---

## Le modèle

**Objet :** Une proposition de collaboration près de chez vous — GTI Immobilier

Bonjour {prenom},

Je suis [EXPÉDITEUR], chez GTI Immobilier, un groupe de 17 agences dans la Loire, la Haute-Loire, le Puy-de-Dôme
et l'Ardèche. Nous cherchons des agents commerciaux autour de notre agence de {agence_proche}, et votre parcours
dans l'immobilier nous a donné envie de vous écrire.

[CE QUE GTI PROPOSE — deux ou trois phrases : l'accompagnement, les outils, la rémunération.]

Si l'idée vous intéresse, je vous propose un échange de vingt minutes, au téléphone ou à l'agence de
{agence_proche}, au moment qui vous convient. Et si ce n'est pas le moment, une simple réponse suffit.

Bien cordialement,
[EXPÉDITEUR]

---

**Pourquoi vous recevez ce message, et ce que nous savons de vous**

- Nous avons trouvé vos coordonnées professionnelles sur {source} ({lien_source}), où elles sont affichées
  publiquement.
- Nous gardons seulement : vos nom et prénom, votre commune, votre réseau, les coordonnées professionnelles
  affichées et, s'il existe, votre numéro SIREN avec les informations publiques du registre des entreprises.
- Responsable : GTI Immobilier, [ADRESSE POSTALE DE GTI]. But : vous proposer une collaboration comme agent
  commercial. Base : notre intérêt légitime à recruter dans notre métier.
- Seuls les responsables du recrutement chez GTI y ont accès. Elles sont hébergées chez nos prestataires
  techniques (base de données et serveur), qui n'en font rien d'autre. Rien n'est vendu ni transmis à qui que ce soit.
- Sans échange avec vous, tout est effacé au bout de trois ans (et de nos copies de sauvegarde un an après au plus).
- À tout moment, vous pouvez voir ces informations, les faire corriger ou effacer, ou refuser tout nouveau
  contact : **répondez simplement « Ne plus me contacter »**, ou écrivez à [ADRESSE DE CONTACT POUR LES DONNÉES].
  Vous pouvez aussi vous adresser à la CNIL (cnil.fr).

---

## La version orale (au premier appel)

À dire **dès le début de l'appel**, avant la proposition — c'est le même devoir d'information :

> « Bonjour {prenom}, [EXPÉDITEUR] de GTI Immobilier. Je vous appelle parce que nous recrutons des agents
> commerciaux autour de {agence_proche}. J'ai trouvé votre numéro sur {source}. Si vous préférez que nous ne
> vous recontactions pas, dites-le-moi, et c'est noté tout de suite. Vous avez deux minutes ? »

Puis, dans l'écran : cocher « C'est fait, la personne est informée » ; et si elle refuse, « Retirer » →
« Ne plus jamais la contacter » (elle ne reviendra plus à aucune collecte).

## Quand elle a donné ses coordonnées elle-même (ajoutée à la main)

Recommandée par un de nos agents, candidature reçue, rencontrée : **pas de bloc d'information à joindre** pour la
source (elle la connaît). Le même texte, sans la partie « Pourquoi vous recevez ce message » — mais la ligne
« répondez simplement « Ne plus me contacter » » reste, par courtoisie.

## ⚠ Une promesse du texte n'est pas encore tenue par le code

« Tout est effacé au bout de trois ans » : **la purge des 3 ans (R5.3) n'est PAS codée** (reportée par Frédéric le
24/11). Le texte peut partir ainsi — la plus ancienne fiche date du 20/11/2026, la première purge tombe en
novembre 2029 —, mais **R5.3 devient alors un engagement**, à faire bien avant cette date. Les autres
affirmations sont vraies aujourd'hui : accès aux administrateurs seuls (D3), liste « ne plus contacter » lue par
chaque collecte (R2, prouvé), copies gardées un an au plus (6 sauvegardes, 90 quotidiennes, image de 14 jours).

## ⏸ Ce que Frédéric décide avant le premier envoi

1. **Le texte** : le ton, l'objet, et le paragraphe [CE QUE GTI PROPOSE].
2. **L'expéditeur** et **l'adresse de contact pour les données** (une adresse qui est lue : la demande doit être
   traitée, puis portée dans l'écran par « Retirer »).
3. **Le refus par réponse** suffit-il, ou faut-il un **lien de désinscription** ? Un lien demande une petite page
   publique (elle n'existe pas) ; la réponse « Ne plus me contacter » marche dès aujourd'hui.
4. **L'avis de son conseil** sur ce bloc d'information (question déjà posée dans la note, §6) : je n'ai pas
   d'avis juridique à donner, seulement les règles que la note a déjà fixées.
5. **Comment l'envoyer** : soit la messagerie de l'administrateur s'ouvre avec ce texte déjà rempli (simple, rien
   ne part sans lui) ; soit un envoi depuis l'app par Workspace (D5, plus tard). Dans les deux cas, c'est lui
   qui clique (note §15 : jamais un automate).
