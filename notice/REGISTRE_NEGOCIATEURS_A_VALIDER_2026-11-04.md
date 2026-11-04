# Registre des négociateurs — la liste à valider (essai du 04/11/2026, rien n'est posé)

> Ce que donnerait le remplissage de l'étape 1 (`supabase/patch_registre_negociateurs_2026-11-04.sql`), mesuré par un
> essai en tables temporaires sur les données du 04/11. Les numéros 1000xxx sont ceux de l'essai : ils peuvent changer à la
> pose (ils se suivent dans l'ordre de création). Audit : `AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md`.
>
> **Lecture** : `n15/u39` = fiche Hektor n° de négociateur 15 / n° d'utilisateur 39, suivie de son agence ; ✓ = fiche
> active chez Hektor ; † = Hektor ne la liste plus (elle n'existe plus que chez nous) ; « compte u8 » = un compte
> utilisateur de Hektor sans fiche de négociateur (secrétaire, agence) ; « répartition u23 » = un numéro qui n'existe plus
> que dans la répartition des honoraires.

## En chiffres

- **187 personnes**, **241 fiches ou comptes** : 167 négociateurs (33 actifs), 18 agences (14 actives), 2 « utilisateur
  supprimé ».
- Toutes les 219 fiches de l'annuaire ont leur place ; tous les numéros d'utilisateur de la répartition aussi.
- 5 comptes de l'app sont reliés à leur personne (Frédéric, Franck, Pauline GIRINON, Emmanuelle PEREIRA, Mélanie LEGRAND) ;
  le compte d'essai `codex.test@` et le compte commercial inactif `sashagerphagnon@gmail.com` n'ont pas de personne.

## ① À valider par toi

**Secrétaires qui ont aussi des fiches de négociateur** — je les ai rangées « négociateur » ; faut-il « secrétaire » ?
- Pauline GIRINON — p.girinon@ — 2 comptes de secrétaire (u8, et u3 sous l'adresse sashagerphagnon@gmail.com, **réunie par le nom**) ; fiches n14 Issoire †, n16 Monistrol †, n22 Firminy †, n53 Craponne †
- Caroline GERPHAGNON — compte secrétaire u5 ; fiche n24 Firminy †
- Delphine BLANCHARD — compte secrétaire u6 ; fiches n21 Firminy †, n60 Saint-Étienne †, n88 Le Puy †
- Franck GERPHAGNON — franck.gerphagnon@gmail.com — compte secrétaire u7 ; fiches n1 Compte formation ✓, n19 Firminy † ; son compte de l'app (adresse @gti-immobilier.fr) relié

**Fiches sans e-mail, rattachées par le nom** (récentes : n° 212 à 223) :
- Alexandra GUEROULT n222 Montbrison · Charlène PARANIER n212 Saint-Just-Saint-Rambert · Cyril MASSARDIER n217 Firminy
- Daniel ADDEZI n223 Saint-Étienne · Fabien LASHERMES n215 Firminy · Fabrice DELOMBRE n218 Saint-Just-Saint-Rambert
- Frédéric MONNE n219 Yssingeaux · hélène FAURE n213 Firminy · Luigi VINCI n214 Firminy · Odile DUCERF n216 Montbrison
- Tharah KLAU n221 Le Puy-en-Velay

**E-mail partagé avec une agence** — gardé, mais il ne servira JAMAIS à rattacher seul une nouvelle fiche :
- Hélène DEFOUR (craponne@), Nicole VURPILLOT (monistrol@), Stephane PIOCHEL (dunieres@), Anne VALANCOGNE (veauche@)
- Annette BERARD, Daniel KRUG, Eddy BARD, Franck BELLERI, Hannah WEATHERLY, Jérome CHABANNES, Maud ROBIN, Mylène KRIGER,
  Roger CHANTELOUBE, Stéphanie CHAZOT, Sylvain FERRARA (adresses « gtiimmobilier.… » wanadoo / orange), Serge RAGAZZON
  (gti.immobilier@orange.fr)
- Frédéric GERPHAGNON : son adresse est aussi celle du compte Hektor « Compte Formation »

**Utilisateurs supprimés chez Hektor** (on ne sait plus qui) :
- « Utilisateur supprimé n° 0 » — 460 dossiers de 2011 à 2024 · « Utilisateur supprimé n° 24 » — 145 dossiers de 2006 à 2012

## ② Les agences (une personne par agence ; jamais réunies par l'e-mail)

- Ambert — n12 ; + « répartition u23 » († ; 4 dossiers 2015-2021)
- Annonay — compte u17 ; n79 · Brioude — compte u18 · Courpière — compte u9 ; n74 · Craponne-sur-Arzon — compte u11
- Dunières — compte u15 · **Firminy — compte u19 ; n25 ; n220 « gti immobilier » ; n224 « Négo GTI »**
- Issoire — n98 · Le Puy-en-Velay — n99 · Monistrol-sur-Loire — compte u21 ; n83 · Montbrison — compte u20 ; n82 ; n86
- Saint-Bonnet-le-Château — compte u13 · Saint-Didier-en-Velay — compte u12 · Saint-Étienne — n2
- Saint-Just-Saint-Rambert — compte u10 ; n75 · Tence — compte u16 · Yssingeaux — compte u14
- **Compte Formation** — compte u1 (⚠ sous l'adresse frederic.gerphagnon@)

## ③ Les 33 négociateurs actifs, avec toutes leurs fiches

- Alice RONDEAU n8 Ambert ✓ · Arnaud VALLA n47 Yssingeaux ✓ · Céline HERITIER n38 Tence, n56 Courpière ✓
- Christèle GENTES n7 Le Puy ✓, n65 Firminy †, n80 Brioude † · Christine BRAVARD n55 Courpière ✓ · Claire RIBBES n15 Issoire ✓
- Clarisse SAPET n45 Yssingeaux ✓ · Claudie FERNANDEZ n48 Saint-Bonnet ✓, n61 Saint-Étienne †, n77 Craponne †
- Corinne REYNAUD n90 Annonay ✓ · Dylan JOURGET n17 Monistrol ✓, n62 Saint-Didier, n73 Firminy, n78 Craponne
- Elodie POUGET n13 Issoire ✓ · Emmanuelle PEREIRA n26 Firminy ✓, n51 Craponne, n84 Monistrol (+ compte de l'app)
- Guillaume PERRET n91 Monistrol ✓, n96 Monistrol · Lionel FLANDIN n49 Saint-Bonnet ✓ · Lucca MEJEAN n225 Le Puy ✓
- Lucille FORLICO n4 Saint-Étienne ✓, n63 Firminy † · Marion BILLIG DURAND n52 Craponne ✓, n39 Tence †, n89 Le Puy †
- Mélanie LEGRAND n5 Saint-Étienne ✓, n76 Saint-Just (+ compte de l'app) · Nadege PEYRARD n44 Dunières ✓, n36 Tence, n68 Firminy
- Nicolas BOUCHET n46 Yssingeaux ✓, n59 Tence †, n87 Le Puy † · Nicolas COUDERT n57 Courpière ✓, n34 Tence †, n58 Yssingeaux †
- Nicolas RAYNAUD n50 Saint-Didier ✓, n37 Tence † · Olivier POMBAR n27 Brioude ✓, n43 Tence †
- Sandrine DELAVAUD n9 Ambert ✓, n93 Tence † · Simon DECHAUD n6 Le Puy ✓, n64 Firminy †, n81 Brioude †
- Stephanie JEOFFROY n18 Montbrison ✓, n40 Tence, n85 Montbrison · Stéphanie MARTINEZ n30 Annonay ✓, n35 Tence, n67 Firminy
- Sylvie TEYSSONNIER n41 Tence ✓ · Tatiana CROIZIER n54 Saint-Just ✓
- (+ Pauline GIRINON, Caroline GERPHAGNON, Delphine BLANCHARD, Franck GERPHAGNON : ① ci-dessus)

## ④ Les anciens (aucune fiche active) — 134 personnes, toutes gardées

Ceux qui ont plusieurs fiches ou qui ne sont plus chez Hektor :
- Aline VALETTE n42 Tence † · Baptiste BRUEL n11 Ambert † · Frédéric GERPHAGNON n20 Firminy † (+ compte de l'app)
- Frédérique JORAND n10 Ambert, n32 Tence · Hugo LABBE n29 Annonay, n33 Tence, n66 Firminy
- Vincent-Lucas GONZALEZ n23 Firminy, n95 Saint-Étienne, n97 Monistrol † · Cyril LACHAIZE n3 Saint-Étienne · Pierrick MARTINEZ n31 Annonay
- Manel ARFAOUI DE RAFFIN n198 †, Jérome CHABANNES n165 †, Monique CHABRIER n190 †, Eléonore GRASSO n179 † (Le Puy)
- les 11 fiches sans e-mail (①) et les 17 à e-mail partagé (①)

Les autres anciens ont une seule fiche, toujours listée par Hektor (inactive) — de Adeline CHEVROLAIS (n180) à Vivien BERGER
(n28), Jean VALLA (n192), Joel CHAMPAGNAC (n195), Morgane SANGUIN (n156)… La liste complète sortira du registre une fois
posé (une requête), dans le même format.
