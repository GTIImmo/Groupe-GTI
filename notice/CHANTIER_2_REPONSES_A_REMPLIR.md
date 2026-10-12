CHANTIER 2 - LES DROITS DU NEGOCIATEUR - FICHE DE REPONSE
=========================================================
A remplir par Frederic.  Version 2 du 12/10/2026 : AJOUT des consultations
et de la PORTEE (ses biens / son agence / tout le reseau).
Detail et preuves : notice/CHANTIER_2_DROITS_NEGOCIATEUR_2026-10-09.md


MODE D'EMPLOI
-------------
Tout est DEJA PRE-REMPLI avec ma proposition.
Tu ne changes que ce qui ne te convient pas : tu remplaces la lettre entre crochets.
Les lignes "aujourd'hui" sont la pour comparer : NE RIEN Y CHANGER.
Si une ligne ne te parle pas, mets [ ? ] et je t'expliquerai celle-la.


LES DEUX QUESTIONS POSEES SUR CHAQUE LIGNE
------------------------------------------

  QUI ?  (jusqu'ou DESCEND le droit -- c'est une ECHELLE : chaque niveau inclut
          ceux du dessus. L'ADMIN et le MANAGER peuvent TOUJOURS.)

     S  = le NEGOCIATEUR aussi, DE SON PROPRE CHEF        (+ manager + admin)
     D  = le NEGOCIATEUR aussi, mais il DEMANDE et un manager ou un admin valide
          (le manager et l'admin, eux, le font directement -- le circuit existe deja)
     A  = MANAGER + ADMIN seulement, le negociateur ne peut pas, meme en demandant
     X  = ADMIN SEUL, le manager non plus

  JUSQU'OU ?  (sur quels biens / quels contacts)
     B  = ses BIENS / ses CONTACTS seulement        (son portefeuille)
     G  = toute son AGENCE                          (ses collegues de la meme agence)
     R  = tout le RESEAU                            (les 17 agences)

     ⚠ LA PORTEE NE CONCERNE QUE LE NEGOCIATEUR.
     L'admin et le manager voient et touchent TOUT LE RESEAU dans tous les cas
     (c'est ta reponse « manager = idem admin »).

     Exemple : "modifier les champs" en [ S ] + [ B ] veut dire
       - le negociateur modifie SES biens, quand il veut, sans rien demander
       - le manager et l'admin modifient N'IMPORTE QUEL bien du reseau



  Quand la reponse QUI est D, A ou X, la portee concerne le negociateur
  DEMANDEUR : jusqu'ou peut-il demander ce geste.


CE QU'IL FAUT SAVOIR AVANT DE REPONDRE - 5 points mesures le 12/10
------------------------------------------------------------------

1. LE RESEAU, C'EST 17 AGENCES (+ 2 lignes parasites a nettoyer un jour :
   "Agences supprimee" 115 annonces, "Compte formation" 5 annonces).
   De 269 a 1 157 annonces par agence, de 1 a 8 adresses de negociateur chacune.
   Les 3 plus grosses : Saint-Etienne 1 157 · Montbrison 1 110 · Courpiere 1 100.

2. LA PORTEE "AGENCE" N'EXISTE PAS ENCORE.
   Aujourd'hui la base ne connait que deux etats : "mon adresse" ou "tout".
   Il n'y a AUCUNE colonne d'agence dans la fiche d'un compte (app_user_profile).
   -> Si tu reponds G quelque part, il faut AJOUTER cette notion : c'est un petit
      travail en plus (une fonction + le rattachement). Voir question E.
   BONNE NOUVELLE : le rattachement adresse -> agence existe deja dans l'annuaire
   Hektor, et il n'est PAS ambigu (155 adresses ; 24 ont plusieurs agences dans
   l'histoire, mais AUCUNE n'a plusieurs agences ACTIVES en meme temps).

3. ATTENTION AU RAPPROCHEMENT ACQUEREUR - le piege a eviter.
   Les rapprochements sont aujourd'hui visibles SANS AUCUNE LIMITE, et c'est
   METIER : un acquereur de Firminy peut correspondre a un bien d'Issoire.
   -> Si tu cloisonnes la CONSULTATION des annonces a "ses biens" (B), le
      rapprochement ne sert plus a rien pour un negociateur.
   -> VOIR et MODIFIER n'ont pas besoin de la meme portee. On peut tres bien
      VOIR tout le reseau et ne MODIFIER que ses biens.

4. AUJOURD'HUI LE CLOISONNEMENT NE TIENT PAS.
   La limite "ses biens" est un filtre pose par le NAVIGATEUR, pas une serrure
   de la base. Un negociateur connecte peut deja voir toutes les annonces, tous
   les contacts, tout le registre des mandats, et toutes les ventes et commissions
   de ses collegues. Ce n'est PAS un trou public (rien n'est visible sans compte,
   la vitrine et l'espace client ne sont pas concernes).

5. LES COMMISSIONS SONT ATTACHEES AU DROIT "CHANGER LE STATUT".
   C'est volontaire dans le code. Si tu mets S au statut, les repartitions de
   commission s'ouvrent AUSSI, sauf si on les separe (point de travail en plus).


=========================================================
PARTIE 1 - LES 5 QUESTIONS GENERALES
=========================================================

A. PAR QUEL LOT ON COMMENCE ?
   (coche une seule ligne avec un x entre les crochets)

   [x] A1  L4 cloisonner les consultations, PUIS L2, PUIS L3, PUIS L1
           -> ma preference : on ferme les cloisons avant de faire entrer du monde
   [ ] A2  L2 d'abord (ce que le negociateur fait seul) : c'est ce qui debloque l'etape 2
   [ ] A3  L1 d'abord (manager = admin) : le plus petit
   [ ] A4  autre ordre, que j'ecris ici : ...............................................

   Rappel des lots :
     L1 = manager devient l'egal d'un admin        (petit)
     L2 = ce que le negociateur fait seul          (moyen)
     L3 = les demandes qui manquent                (moyen, par type)
     L4 = cloisonner les consultations             (moyen, a eprouver)
     L5 = ajouter la notion d'AGENCE               (petit) -- seulement si tu reponds G


B. LE PRIX D'UNE ANNONCE

   [x] B1  il reste SOUS DEMANDE (c'est ce que dit l'existant : une demande de baisse
           de prix existe expres, et elle refuse si le mandat n'est pas valide)
   [ ] B2  le negociateur le modifie LIBREMENT, comme les autres champs
   [ ] B3  libre a la HAUSSE, sous demande a la BAISSE
   [ ] B4  autre : ......................................................................


C. COMBIEN DE TYPES DE DEMANDE ON AJOUTE D'UN COUP ?

   [ ] C1  les 5 d'un coup : mise sous mandat, archiver, transactions,
           changer de negociateur, supprimer un document
   [x] C2  2 D'ABORD pour eprouver le patron (mise sous mandat + archiver),
           le reste ensuite
   [ ] C3  ma liste a moi : ..............................................................


D. LE CLOISONNEMENT DES CONSULTATIONS (lot L4)

   [x] D1  EN PREMIER, avant de donner le moindre droit d'ecriture
   [ ] D2  juste avant d'ouvrir le pilote
   [ ] D3  on note et on garde pour plus tard (personne n'en profite aujourd'hui)


E. D'OU VIENT L'AGENCE D'UN COMPTE ?  (a remplir seulement si tu reponds G quelque part)

   [x] E1  on la DEDUIT de l'annuaire Hektor (adresse -> agence active)
           -> rien a saisir, ca suit Hektor tout seul ; si Hektor se trompe, nous aussi
   [ ] E2  on l'ECRIT dans la fiche du compte, a la main
           -> tu maitrises, mais il faut la saisir pour chaque compte et la tenir a jour
   [ ] E3  les deux : l'annuaire par defaut, et on peut forcer a la main
   [ ] E4  sans objet, je n'utilise pas G


=========================================================
PARTIE 2 - LES CONSULTATIONS  (qui VOIT quoi)   *** NOUVEAU ***
=========================================================
  Ici une seule question : JUSQU'OU ?   (B = ses biens · G = son agence · R = tout le reseau)
  Il s'agit de ce que voit un NEGOCIATEUR. Admin et manager voient tout, dans tous les cas.

  voir la LISTE DES ANNONCES et leurs fiches
      aujourd'hui : tout le reseau (le filtre navigateur dit "ses biens", mais il ne tient pas)
      jusqu'ou ? [ R ]
      -> je propose R a cause du rapprochement (point 3 plus haut). Si tu mets B ou G,
         il faudra decider ce que devient le rapprochement acquereur.

  voir les CONTACTS et leurs fiches
      aujourd'hui : tout le reseau (meme chose)
      jusqu'ou ? [ R ]

  voir les RECHERCHES ACQUEREUR
      aujourd'hui : ses contacts (regle correcte en base)
      jusqu'ou ? [ R ]

  voir les RAPPROCHEMENTS (bien <-> acquereur)
      aujourd'hui : tout le reseau, SANS AUCUNE LIMITE
      jusqu'ou ? [ R ]

  voir les ARCHIVES (annonces archivees)
      aujourd'hui : tout le reseau, SANS AUCUNE LIMITE
      jusqu'ou ? [ R ]

  voir les VENDUS / CLOS
      aujourd'hui : tout le reseau, SANS AUCUNE LIMITE
      jusqu'ou ? [ R ]

  voir le REGISTRE DES MANDATS
      aujourd'hui : tout le reseau, SANS AUCUNE LIMITE
      jusqu'ou ? [ B ]

  voir les AFFAIRES : offres, compromis, ventes
      aujourd'hui : tout le reseau, SANS AUCUNE LIMITE
      jusqu'ou ? [ B ]

  voir les MONTANTS DE COMMISSION et leur repartition
      aujourd'hui : tout le reseau, SANS AUCUNE LIMITE
      jusqu'ou ? [ B ]
      -> c'est le point le plus sensible : aujourd'hui un negociateur peut voir
         ce que gagnent ses collegues.

  voir les DOCUMENTS d'une annonce
      aujourd'hui : ses biens (regle correcte en base)
      jusqu'ou ? [ B ]

  voir les PHOTOS d'une annonce
      aujourd'hui : ses biens (regle correcte en base)
      jusqu'ou ? [ R ]

  voir les ESTIMATIONS
      aujourd'hui : non mesure separement (suit les annonces)
      jusqu'ou ? [ R ]

  voir les MANDANTS / PROPRIETAIRES d'un bien
      aujourd'hui : ses biens (regle correcte en base)
      jusqu'ou ? [ R ]

  voir l'AGENDA / les RDV
      aujourd'hui : NON MESURE (je dois le verifier)
      jusqu'ou ? [ B ]

  voir les STATISTIQUES par negociateur
      aujourd'hui : l'ecran est reserve a l'admin
      jusqu'ou ? [ B ]

  voir la LISTE DES NEGOCIATEURS (pour choisir, affecter...)
      aujourd'hui : tout le reseau
      jusqu'ou ? [ R ]


=========================================================
PARTIE 3 - LES GESTES, UN PAR UN  (qui ? + jusqu'ou ?)
=========================================================

ANNONCE
-------
  modifier les champs (surface, description, DPE...)
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]
  modifier le PRIX
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ D ]        jusqu'ou ? [ B ]


  changer le statut (sous mandat, offre, compromis, vente, clos)
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  archiver une annonce
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  desarchiver une annonce
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ R ]

  changer le negociateur d'une annonce
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  supprimer une annonce
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  creer un brouillon d'annonce
      aujourd'hui : le negociateur, dans une agence ou il porte deja un bien
      qui ? [ S ]        jusqu'ou ? [ G ]
  marquer "Valide" / "Diffusable"
      aujourd'hui : admin seul (ecran)
      qui ? [ A ]        jusqu'ou ? [ R ]





MANDANT / PROPRIETAIRE
----------------------
  rattacher un mandant a une annonce
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]
  retirer un mandant
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]
  creer un mandant
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]
  modifier un mandant
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]


TRANSACTION ET COMMISSION
-------------------------
  enregistrer une OFFRE
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  enregistrer un COMPROMIS
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  enregistrer une VENTE
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]


  modifier une transaction (montant, date)
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  ecrire une note, des conditions
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  supprimer / abandonner une transaction
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  repartition de commission (la SAISIR)
      aujourd'hui : admin seul, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

      ATTENTION : attachee EXPRES au droit "changer le statut" (point 5 plus haut).


CONTACT ET RECHERCHE
--------------------
  creer un contact
      aujourd'hui : le negociateur, a son nom
      qui ? [ S ]        jusqu'ou ? [ B ]
  modifier un contact
      aujourd'hui : le negociateur, ses contacts
      qui ? [ S ]        jusqu'ou ? [ R ]
  supprimer un contact
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ A ]        jusqu'ou ? [ R ]

  ajouter une recherche acquereur
      aujourd'hui : le negociateur, ses contacts
      qui ? [ S ]        jusqu'ou ? [ R ]
  modifier une recherche acquereur
      aujourd'hui : le negociateur, ses contacts
      qui ? [ S ]        jusqu'ou ? [ R ]
  supprimer une recherche acquereur
      aujourd'hui : le negociateur, ses contacts
      qui ? [ S ]        jusqu'ou ? [ B ]


DOCUMENTS
---------
  remonter un document au cloud ("Preparer")
      aujourd'hui : le negociateur, ses biens
      qui ? [ S ]        jusqu'ou ? [ B ]

  envoyer un document chez Hektor
      aujourd'hui : le negociateur, ses biens
      qui ? [ S ]        jusqu'ou ? [ B ]

  resynchroniser les documents
      aujourd'hui : le negociateur, ses biens
      qui ? [ S ]        jusqu'ou ? [ B ]

  recharger la fiche d'une archive / d'un vendu
      aujourd'hui : le negociateur, ses biens
      qui ? [ S ]        jusqu'ou ? [ R ]

  relancer une signature
      aujourd'hui : le negociateur, ses biens
      qui ? [ S ]        jusqu'ou ? [ B ]

  annuler une procedure de signature
      aujourd'hui : le negociateur, ses biens
      qui ? [ S ]        jusqu'ou ? [ B ]

  supprimer un document chez Hektor
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]
      (geste destructeur : il efface aussi notre copie, serveur ET cloud)

  generer un avis de valeur
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]

  generer le PDF du mandat
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]

  generer le plan cadastral
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]


PHOTOS
------
  ajouter une photo
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]

  resynchroniser les photos
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]

  visite virtuelle (Matterport)
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]


MANDAT
------
  demander un numero de mandat (il vient de PROTEXA via Hektor)
      aujourd'hui : manager + admin, tout le reseau
      qui ? [ S ]        jusqu'ou ? [ B ]


=========================================================
PARTIE 4 - LES ECRANS
=========================================================
  (qui doit VOIR l'ecran)

  ecran "Suivi" : la liste des demandes a traiter
      aujourd'hui : admin seul                 qui ? [ A ] OUI
      Note : une demande de diffusion est EN ATTENTE DEPUIS LE 02/06/2026,
      que personne ne voit.
      Et si un manager y entre : il voit les demandes de [ R ] ?  OUI

  ecran "Sante" : la surveillance du systeme
      aujourd'hui : admin seul                 qui ? [ X ]

  outil "Utilisateurs" : creer et modifier les comptes
      aujourd'hui : admin seul                 qui ? [ A ]
  voir l'avancement de SA PROPRE saisie ("c'est parti chez Hektor ?")
      aujourd'hui : IMPOSSIBLE pour un negociateur
      qui ? [ S ]        jusqu'ou ? [ B ]


=========================================================
PARTIE 5 - LE PILOTE (ta reponse Q3 : tester avant de deployer)
=========================================================

Combien de comptes negociateur d'essai ?
   [x] P1  2 ou 3
   [ ] P2  1 seul
   [ ] P3  nombre que j'ecris : ..........

Lesquels ? (nom ou adresse - il faut que ce soit L'ADRESSE QUI PORTE DES BIENS,
sinon le negociateur ne verra RIEN)/ UTILISE LES COMPTES DEJA SU L’apps
   1 : ..................................................................
   2 : ..................................................................
   3 : ..................................................................

   Rappel mesure : 43 adresses de negociateur portent le parc,
   SEULES 4 d'entre elles ont un compte actif aujourd'hui.
   Les 2 comptes commerciaux actifs portent 125 et 916 annonces.

Dans quelle(s) agence(s) fait-on le pilote ?
   [ ] AG1  une seule petite agence (ex. Saint-Didier 269 annonces, Dunieres 548)
   [x] AG2  une agence moyenne (ex. Firminy 969 annonces, 8 negociateurs)
   [ ] AG3  deux agences differentes, pour eprouver le cloisonnement entre agences
   [ ] AG4  agence(s) que j'ecris : ......................................................

On cree ces comptes :
   [ ] C-c  autre : déjà crée


=========================================================
PARTIE 6 - REMARQUES LIBRES
=========================================================
(tout ce que je n'ai pas prevu, tes doutes, tes questions)
J’aimerais aussi avoir un type Agent commercial avec uniquement accès a ses annonces ses contacts etc… donc bien plus fermé que le compte négociateur
......................................................................
......................................................................
......................................................................
......................................................................
......................................................................


=========================================================
CE QUI EST DEJA TRANCHE - rien a remplir
=========================================================
  - "manager = idem admin pour l'instant"          (ta reponse du 12/10)
  - "tester avant de deployer a tous les comptes"  (ta reponse du 12/10)
  - "cela ne doit surtout pas changer les worker"  -> verifie : AUCUN changement
    worker necessaire, et l'ecriture chez Hektor part bien sous le nom du
    NEGOCIATEUR EN CHARGE DU BIEN, pas sous celui de l'utilisateur de l'app.


=========================================================
CE QUE JE N'AI PAS PU MESURER - a savoir
=========================================================
  - la derniere connexion de chaque compte (la base refuse mes lectures)
  - l'AGENDA / les RDV : je n'ai pas verifie qui voit quoi
  - les ESTIMATIONS : pas mesurees separement des annonces
  - les boutons de demande sont-ils VISIBLES pour un negociateur a l'ecran :
    lu dans le code, jamais vu avec un vrai compte commercial
