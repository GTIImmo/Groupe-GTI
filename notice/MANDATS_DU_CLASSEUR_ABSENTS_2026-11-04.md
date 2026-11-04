# Les mandats que le classeur connait et que le registre n a pas -- 04/11/2026

## ⛔⛔ LIRE CECI AVANT D OUVRIR UN CHANTIER : LE SUJET EST PROBABLEMENT DEJA TRANCHE

**A4bis le disait deja le 31/10**, section « C : Mandat » :

> « Les 134 ecarts ne s'ecrasent pas : sur un **mandat de recherche**, le classeur
> porte le **numero de recherche** et nous celui de **vente**. **Les deux sont justes.** »

**Et ma mesure du 04/11 qui semblait contredire cela etait FAUSSE.** J'avais annonce
« 87 de ces numeros sont dans le miroir local mais pas au registre, donc l'importeur
les perd ». C'etait un **faux positif de recherche textuelle** : je cherchais le numero
entre guillemets dans tout le blob `mandats_json`, et il matchait n'importe quel autre
champ (un montant, un identifiant).

⭐ **La verification par annonce le prouve** : pour le numero 11935, l'annonce trouvee
(30128) porte en realite le mandat **7087** -- au miroir **et** au registre, identiques.
Idem 12257 -> 16446, 12566 -> 2574, 13187 -> 3483. **Le miroir et le registre concordent
parfaitement : l'importeur ne perd rien.**

➡ **Ces 107 numeros ne sont donc pas des mandats manquants** : ce sont tres probablement
des numeros d'une AUTRE serie (recherche), exactement ce que A4bis decrivait.
⬜ Ce qui resterait a verifier, si on rouvrait le sujet : que ces 107 numeros
correspondent bien a des numeros de recherche, en les croisant avec
`app_contact_mandat_recherche_current` (32 lignes) et le classeur colonne par colonne.

⚠ **Les 23 numeros au-dela de 18339** (la frontiere ou l'API de Hektor s'est figee le
30/01/2026) restent le seul trou connu et reel -- c'est celui que le rattrapage de
fevrier traitait (`phase2/sync/manual_mandat_corrections.py`, 77 annonces reparees).

---

## La liste brute, telle que mesuree (a lire avec la reserve ci-dessus)

**115 lignes**, **107 numeros distincts**.

```
NON TROUVÉ  ID CY25FQQD      Vente réglée        NON TROUVÉ      charge -
NON TROUVÉ  ID TCZZFOYK      Vente réglée        NON TROUVÉ      charge -
NON TROUVÉ  ID I3TFR2KG      Vente réglée        NON TROUVÉ      charge -
NON TROUVÉ  ID IBEZYB57      Vente réglée        NON TROUVÉ      charge -
NON TROUVÉ  ID ZTRJRM6C      Vente réglée        NON TROUVÉ      charge -
NON TROUVÉ  ID S7FC8DAB      Vente réglée        NON TROUVÉ      charge -
3982      ID SPS89VR6      Vente réglée        - Tence -       charge -
11935     ID AFRUYH2Y      Vente réglée        - Annonay -     charge -
12257     ID ODIWQYZ7      Vente réglée        NON TROUVÉ      charge -
12566     ID 58I5AO17      Vente réglée        NON TROUVÉ      charge -
13187     ID HJCCRM5I      Vente réglée        NON TROUVÉ      charge -
13254     ID 2R10IRMW      Annulée             NON TROUVÉ      charge -
13428     ID LLQHD7MG      Vente réglée        NON TROUVÉ      charge -
13438     ID JV7S9HGE      Vente réglée        - Unieux -      charge -
13499     ID 50OUISUB      Annulée             - Estivareille  charge -
13607     ID CBF8PNY9      Vente réglée        - Firminy -     charge -
13654     ID O8BY6AC8      Annulée             NON TROUVÉ      charge -
13779     ID 0108T49T      Vente réglée        - Saint-Pierre  charge -
13859     ID 96E9XLK6      Vente réglée        constructible   charge -
13882     ID XJ94X1RN      Vente réglée        - Bertignat -   charge -
13905     ID SNDD1833      Vente réglée        - Saint-Bonnet  charge -
13920     ID 9W3RJP5Z      Vente réglée        - Ambert -      charge -
13923     ID G6P1S0QJ      Vente réglée        - Marsac-en-Li  charge -
13933     ID R08KB192      Vente réglée        - Bellevue-la-  charge -
14044     ID 5IMC8F4X      Vente réglée        - Courpière -   charge -
14075     ID JL6I6JDG      Annulée             - Arlanc -      charge -
14080     ID S8BKB6FL      Vente réglée        - Ambert -      charge -
14154     ID VVGMC0QW      Vente réglée        - Saint-Pierre  charge -
14194     ID 1TH5OEUJ      Vente réglée        - Cistrières -  charge -
14195     ID 5LUGIH2H      Vente réglée        constructible   charge -
14204     ID 17S58J78      Vente réglée        constructible   charge -
14242     ID VUWL9WH4      Vente réglée        - Riotord -     charge -
14262     ID PC7VF7HB      Vente réglée        - Cunlhat -     charge -
14313     ID OK1APVUR      Vente réglée        - La Chaise-Di  charge -
14418     ID XQGPK8LV      Annulée             Annonay         charge Acquéreur
14432     ID EHR9GJI2      Vente réglée        NON TROUVÉ      charge -
14476     ID X9S2R604      Vente réglée        - Vollore-Vill  charge -
14524     ID W404YVFF      Vente réglée        NON TROUVÉ      charge -
14619     ID 4O60KJCU      Vente réglée        - Saint-Just-S  charge -
14667     ID TEJLIEID      Vente réglée        NON TROUVÉ      charge -
14668     ID 8N3EMC5I      Vente réglée        non constructi  charge -
14714     ID 3IB0HTMD      Vente réglée        - Tence -       charge -
14717     ID GBW57LF7      Vente réglée        - Chomelix -    charge -
14797     ID KZHL7K47      Vente prévue        Ambert          charge Acquéreur
14936     ID EE2HRQCW      Vente réglée        - Parentignat   charge -
14994     ID QJU46KKK      Vente réglée        de ville - Amb  charge -
15080     ID 7P1JJ2PP      Vente réglée        - Craponne-sur  charge -
15087     ID RU9MP1SI      Vente réglée        NON TROUVÉ      charge -
15132     ID DWKNZ4M4      Vente réglée        - Issoire -     charge -
15191     ID 02D98HM6      Vente réglée        - Satillieu -   charge -
15385     ID OEYQTJ9I      Vente réglée        - Courpière -   charge -
15386     ID D5VZQMCV      Vente réglée        - Tence -       charge -
15459     ID V3FO5NDA      Annulée             - Chenereilles  charge -
15490     ID NVRWUFA0      Vente réglée        - Ceilloux -    charge -
15512     ID 7BPVD7K4      Vente réglée        - Issoire -     charge -
15512     ID TCB4ZNQO      Annulée             - Issoire -     charge -
15598     ID P8Z5MBIG      Annulée             - Ardes -       charge -
15690     ID 79O9K71M      Annulée             - Félines -     charge -
15729     ID VRBZSLP2      Vente réglée        de ville - Sai  charge -
15734     ID 1JGNAII6      Annulée             - Félines -     charge -
15758     ID 33O2BWCL      Vente réglée        de ville - Amb  charge -
15768     ID LR3ONCV9      Annulée             - Firminy -     charge -
15822     ID KAYC29B7      Annulée             NON TROUVÉ      charge -
15823     ID S8NROICE      Vente réglée        NON TROUVÉ      charge -
15877     ID KA2RTLHJ      Vente réglée        - Le Chambon-F  charge -
15920     ID SOF45TS3      Annulée             - Chenereilles  charge -
15952     ID WWSM4TI0      Vente réglée        NON TROUVÉ      charge -
15979     ID JXT6ZZ10      Vente réglée        - Tence -       charge -
16097     ID DHXRAK9O      Vente réglée        NON TROUVÉ      charge -
16123     ID 2GS9PIHU      Vente réglée        de ville - Amb  charge -
16139     ID 7IHI7YTJ      Vente réglée        - Saint-Romain  charge -
16149     ID H4WHY23T      Vente réglée        - Saint-Germai  charge -
16164     ID XWR4O58X      Vente réglée        de ville - Vol  charge -
16231     ID 72GQRHVB      Vente réglée        NON TROUVÉ      charge -
16263     ID 6FQO29C8      Vente réglée        - Chenereilles  charge -
16355     ID WG029IGN      Annulée             de maître - Vo  charge -
16463     ID 4AC7NNBT      Vente réglée        - Issoire -     charge -
16503     ID MDOXOBIC      Vente réglée        NON TROUVÉ      charge -
16503     ID DXSH7AWE      Vente réglée        NON TROUVÉ      charge -
16503     ID PVRG1SNH      Vente réglée        NON TROUVÉ      charge -
16513     ID B33WWDW5      Vente réglée        - Allègre -     charge -
16620     ID KI7NY0Q5      Vente réglée        NON TROUVÉ      charge -
16782     ID A5RW8ZVO      Annulée             de ville - Cou  charge -
16900     ID KAHSA1U3      Vente réglée        - Félines -     charge -
16936     ID H2JZ0S63      Vente réglée        constructible   charge -
17081     ID 9O6NKRIJ      Annulée             - Courpière -   charge Acquéreur
17217     ID KBZR2ND6      Vente réglée        17107- Sauvess  charge Acquéreur
17230     ID SCFSQH5A      Vente réglée        -               charge Acquéreur
17296     ID 729ba8dc      Annulée             St Martin des   charge Vendeur
17381     ID I2771YD1      Vente réglée        NON TROUVÉ      charge Acquéreur
18127     ID 2b924f5f      Annulée             Courpière       charge Vendeur
18143     ID 4cbc128d      Annulée             Lamontgie       charge Vendeur
18404     ID 6e1e24ce      Vente réglée        St Julien d'An  charge Vendeur
21963     ID CRWGXG9R      Annulée             NON TROUVÉ      charge -
22042     ID W4TALJI0      Annulée             NON TROUVÉ      charge Vendeur
24247     ID JEK94D31      Annulée             NON TROUVÉ      charge Vendeur
27874     ID 7W7XUBPO      Vente réglée        NON TROUVÉ      charge Vendeur
31741     ID 0TQS6SHY      Vente réglée        NON TROUVÉ      charge -
41206     ID Y9A2L3X4      Vente réglée        NON TROUVÉ      charge -
42490     ID HJQM9CRZ      Vente réglée        NON TROUVÉ      charge -
45633     ID 1ZYS3OG0      Vente réglée        NON TROUVÉ      charge -
47006     ID 57VFEXTC      Vente réglée        NON TROUVÉ      charge -
54111     ID ESMCO1NC      Vente réglée        NON TROUVÉ      charge -
54311     ID 5X4GNIBD      Vente réglée        NON TROUVÉ      charge -
57084     ID VV6I262Q      Vente réglée        NON TROUVÉ      charge -
58006     ID EY8R7TMA      Vente réglée        NON TROUVÉ      charge -
60411     ID IBO7OTAU      Vente réglée        NON TROUVÉ      charge -
64245     ID D7P0NX8X      Vente réglée        NON TROUVÉ      charge -
66284     ID E1K0MH1G      Vente réglée        NON TROUVÉ      charge -
73058     ID FFYVCQJ7      Vente réglée        NON TROUVÉ      charge -
78006     ID YZUOUQQ0      Vente réglée        NON TROUVÉ      charge -
80761     ID POSIDJ3P      Vente réglée        NON TROUVÉ      charge -
91892     ID SD9PLJVY      Vente réglée        NON TROUVÉ      charge -
92560     ID JZ9693S0      Annulée             NON TROUVÉ      charge -
96219     ID NYEXY2LL      Annulée             NON TROUVÉ      charge -
```
