# Rapport analyse ImmoSign / Hektor

Date : 2026-05-18

## Synthèse

Le flux de signature électronique ImmoSign n'est pas le même flux que l'ajout classique de document déjà présent dans l'application.

Il y a deux mécanismes séparés :

1. Ajout d'un document dans Hektor, déjà géré par le worker existant :
   - `UploadedDocument_uploadForm`
   - `upload_uploadeddoc.php`
   - `UploadedDocument_list`
   - `UploadedDocument_delete`

2. Signature électronique ImmoSign :
   - module JS `labs_immoSign.js`
   - routes `ImmoSign-*`
   - ouverture d'une pop-up de procédure via `ImmoSign-Procedures-create`
   - suivi, annulation, relance et récupération des fichiers via d'autres commandes `ImmoSign-*`

La commande la plus importante identifiée pour ouvrir la procédure de signature est :

```http
POST /admin/xmlrpc.php
```

avec les paramètres :

```text
mode=ImmoSign-Procedures-create
document_id={ID_DOCUMENT}
document_type={TYPE_DOCUMENT}
```

C'est très probablement la commande appelée par le picto de signature, celui qui ressemble à une empreinte digitale, car la fonction JavaScript Hektor correspondante s'appelle :

```javascript
editProcedure(documentId, documentType)
```

et elle ouvre une pop-up Hektor via `powerFuelPopinGetInner`.

## Ce qui existe déjà dans notre application

Le worker document existant se trouve dans :

```text
Console/console_job_worker.js
```

La fonction concernée est :

```javascript
handleUploadDocumentToHektor(job)
```

Elle fait actuellement :

```http
GET /admin/xmlrpc.php?mode=UploadedDocument_uploadForm&type=bien&id_foreign={ID_BIEN}&public={0|2}&publicKey={privee|partage}&idContentDiv={listDocUpload_privee|listDocUpload_partage}
```

puis :

```http
POST /admin/upload_uploadeddoc.php
```

avec :

```text
type=bien
id_foreign={ID_BIEN}
subType=0
subId=0
public={0|2}
Filedata={PDF}
```

Conclusion : ce worker ne doit pas être remplacé. Il faut l'étendre ou ajouter un nouveau type de job dans la même famille `documents`.

## Ce que montre la page Documents Hektor

Dans la capture locale :

```text
Console/exports/upload_form_59624_2026-05-14T16-53-48-373Z/chargeannonce_Documents.html
```

Hektor affiche bien une zone ImmoSign séparée :

```html
<div class="listDocsContainer" id="list_ImmoSign">
  <img src="/external/img/admin/pix.gif" onload="openLab('labs_immoSign.js',null, 'modules')"/>
</div>
```

La page charge aussi un bundle documents/signature :

```html
openLab('labsCompiler.js.php&jfiles=documents_biens|signature|templateDocument|ModeloNonFnaim&folders=documents|biens|templateDocument|modelo')
```

Et elle pose des champs cachés importants :

```html
<input type="hidden" value="59624" id="idObjetSignature"/>
<input type="hidden" value="annonce" id="typeObjetSignature"/>
<input type="hidden" id="referentContactId" name="referentContactId" value="59624"/>
<input type="hidden" value="" id="authKey"/>
```

Ces champs indiquent que le contexte de signature est rattaché à l'annonce Hektor.

## Bouton "Ajouter un document Immosign"

Le bouton visible dans Hektor :

```html
<button type="button" id="goToBibliothequeDocument-modal-immosign-documents">
  <span>Ajouter un document Immosign</span>
</button>
```

déclenche :

```javascript
loadConfigDocType(true);
```

Interprétation : ce bouton ne fait pas un upload PDF simple. Il ouvre la bibliothèque / génération de document ImmoSign.

## Commandes ImmoSign identifiées

### Créer / ouvrir une procédure de signature

```http
POST /admin/xmlrpc.php
```

```text
mode=ImmoSign-Procedures-create
document_id={ID_DOCUMENT}
document_type={TYPE_DOCUMENT}
```

Fonction Hektor :

```javascript
editProcedure(documentId, documentType)
```

Effet : ouvre la pop-up permettant de préparer la procédure de signature.

### Annuler une procédure

```http
POST /admin/xmlrpc.php
```

```text
mode=ImmoSign-deleteProcedure
procedureId={ID_PROCEDURE}
```

### Relancer les signataires

```http
POST /admin/xmlrpc.php
```

```text
mode=ImmoSign-remindProcedureSignatories
procedureId={ID_PROCEDURE}
```

### Retenter la récupération du document signé

```http
GET/POST /admin/xmlrpc.php
```

```text
mode=ImmoSign-retryDocumentRetrieval
procedureId={ID_PROCEDURE}
force=true
```

### Télécharger le ZIP de procédure

```http
GET /admin/xmlrpc.php?mode=ImmoSign-downloadProcedureZip&procedureId={ID_PROCEDURE}
```

### Télécharger le dossier de preuve

```http
GET /admin/xmlrpc.php?mode=ImmoSign-downloadProofsByProcedure&procedureId={ID_PROCEDURE}
```

### Vérifier l'état du module ImmoSign

Cette commande est appelée au chargement Hektor :

```http
GET /admin/xmlrpc.php?mode=ImmoSign-checkModuleSignatureTransformed
```

Si elle échoue, Hektor affiche une pop-up demandant de compléter les informations du module de signature.

### Initialiser / acheter des crédits signature

```http
POST /admin/xmlrpc.php
```

```text
mode=ImmoSign-initModule
module-type=signature
```

Puis, si besoin :

```text
mode=ImmoSign-commander-commander
```

Codes d'erreur repérés :

```text
800 = plus assez de crédits signature sur le module
801 = module parent sans crédit
900 = utilisateur non propriétaire de la procédure
```

## Commandes ImmoSign documents identifiées

Ces commandes concernent la génération / gestion des documents ImmoSign, pas directement l'envoi de signature :

```text
ImmoSign-Documents-generateImmoSignDoc
ImmoSign-Documents-goStepGenDocumentImmoSign
ImmoSign-Documents-saveDocumentImmoSignOnEditorFinish
ImmoSign-Documents-continueDocument
ImmoSign-Documents-deleteImmoSignDocument
ImmoSign-Documents-duplicateDocument
ImmoSign-Documents-printImmoSignDocument
ImmoSign-Documents-previewDocument
ImmoSign-Documents-downloadImmoSignDocument
ImmoSign-Documents-getImmoSignModels
ImmoSign-Documents-documentsBibliotheque
```

Ces routes montrent qu'Hektor distingue fortement :

- les documents uploadés classiques ;
- les documents générés par Hektor ;
- les documents ImmoSign.

## Point critique encore non confirmé

La commande qui ouvre la pop-up de signature est identifiée :

```text
ImmoSign-Procedures-create
```

Mais la commande finale qui valide l'envoi après remplissage de la pop-up n'a pas encore été capturée dans nos exports.

Il faut donc éviter d'automatiser l'envoi réel sans une capture contrôlée, parce que cette étape peut :

- consommer des crédits ImmoSign ;
- envoyer des emails / SMS aux mandants ;
- créer une procédure juridiquement engageante.

## Hypothèse d'intégration dans notre app

Le bon flux cible serait :

1. Générer le mandat PDF depuis l'application.
2. Ajouter le PDF dans Hektor via le worker existant `upload_document_to_hektor`.
3. Synchroniser les documents Hektor pour retrouver l'identifiant du document créé.
4. Créer un job complémentaire dans la même famille `documents`, par exemple :

```text
create_immosign_signature_procedure
```

5. Ce job appellerait :

```text
mode=ImmoSign-Procedures-create
document_id={ID_DOCUMENT}
document_type={TYPE_DOCUMENT}
```

6. Récupérer ou piloter la pop-up pour renseigner les signataires.
7. Capturer puis reproduire la commande finale d'envoi.
8. Synchroniser le statut ImmoSign dans notre base.

## Stockage recommandé côté application

Ne pas mélanger le statut ImmoSign avec le simple statut d'upload.

Options :

1. Ajouter un bloc `immosign` dans `app_console_document.metadata_json`.
2. Ou créer une table dédiée, plus propre :

```text
app_console_document_signature
```

Champs recommandés :

```text
id
console_document_id
hektor_document_id
immosign_document_type
immosign_procedure_id
status
sent_at
signed_at
cancelled_at
last_sync_at
signatories_json
raw_hektor_json
created_at
updated_at
```

## Contraintes repérées

Hektor contient des messages qui indiquent des règles métier importantes :

```text
Le document ajouté ne peut pas être signé (il dépasse 2Mo)
merci d'ajouter un signataire.
merci d'ajouter un document valide.
Votre document est corrompu, cela peut provenir d'un document mal uploadé ou d'une ancienne version de document type.
```

Donc, avant signature, notre app devra vérifier :

- taille du PDF inférieure à 2 Mo ;
- document PDF valide ;
- au moins un mandant signataire ;
- email / téléphone des signataires si ImmoSign les exige ;
- statut du module ImmoSign actif ;
- crédits disponibles.

## Conclusion

La commande principale à retenir est :

```text
POST xmlrpc.php
mode=ImmoSign-Procedures-create
document_id={ID_DOCUMENT}
document_type={TYPE_DOCUMENT}
```

Elle ouvre la procédure de signature électronique. Le worker document actuel n'a pas été écrasé et ne doit pas l'être : il doit rester responsable de l'ajout de document. La signature doit venir comme étape supplémentaire.

Avant d'implémenter l'envoi automatique, il reste une seule capture indispensable : cliquer sur le picto de signature sur un vrai document test, remplir la pop-up sans envoyer à de vrais clients, puis capturer la requête finale qui valide l'envoi.
