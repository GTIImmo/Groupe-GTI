# Rapport qualite phase 2

Controles automatises de coherence sur `phase2.sqlite`.

## Metriques

- `vue_generale_total` : 56666 | attente : doit rester stable entre deux runs hors variation source
- `demandes_total` : 21866 | attente : doit rester stable entre deux runs hors variation source
- `missing_titles` : 0 | attente : 0
- `view_generale_without_dossier` : 0 | attente : 0
- `demandes_without_view_generale` : 0 | attente : 0
- `mandat_numero_id_collision` : 5000 | attente : surveiller, indicateur borne a 5000 pour detecter les cas type 59449/44506

## Echantillons

### `sample_mandat_numero_id_collision`

```json
[
  {
    "hektor_annonce_id": "10",
    "no_dossier": "VA1958",
    "no_mandat": "16707",
    "mandat_id": "5",
    "hektor_mandat_id": "16707",
    "numero": "17131",
    "mandat_annonce_id": "41349"
  },
  {
    "hektor_annonce_id": "1000",
    "no_dossier": "VA22182",
    "no_mandat": "4992",
    "mandat_id": "202",
    "hektor_mandat_id": "4992",
    "numero": "3701",
    "mandat_annonce_id": "11933"
  },
  {
    "hektor_annonce_id": "10000",
    "no_dossier": "VM18570",
    "no_mandat": "3910",
    "mandat_id": "3714",
    "hektor_mandat_id": "3910",
    "numero": "3214",
    "mandat_annonce_id": "10378"
  },
  {
    "hektor_annonce_id": "10003",
    "no_dossier": "EM18604",
    "no_mandat": "3914",
    "mandat_id": "10003:3715",
    "hektor_mandat_id": "3914",
    "numero": "3181",
    "mandat_annonce_id": "10383"
  },
  {
    "hektor_annonce_id": "10006",
    "no_dossier": "VM18708",
    "no_mandat": "3901",
    "mandat_id": "3716",
    "hektor_mandat_id": "3901",
    "numero": "3257",
    "mandat_annonce_id": "10367"
  },
  {
    "hektor_annonce_id": "10007",
    "no_dossier": "VM18748",
    "no_mandat": "3909",
    "mandat_id": "3717",
    "hektor_mandat_id": "3909",
    "numero": "3223",
    "mandat_annonce_id": "10377"
  },
  {
    "hektor_annonce_id": "10009",
    "no_dossier": "VM18814",
    "no_mandat": "3888",
    "mandat_id": "3718",
    "hektor_mandat_id": "3888",
    "numero": "3336",
    "mandat_annonce_id": "10352"
  },
  {
    "hektor_annonce_id": "1001",
    "no_dossier": "VA22208",
    "no_mandat": "4956",
    "mandat_id": "203",
    "hektor_mandat_id": "4956",
    "numero": "3525",
    "mandat_annonce_id": "11876"
  },
  {
    "hektor_annonce_id": "10014",
    "no_dossier": "VM19066",
    "no_mandat": "3867",
    "mandat_id": "3719",
    "hektor_mandat_id": "3867",
    "numero": "3450",
    "mandat_annonce_id": "10312"
  },
  {
    "hektor_annonce_id": "10017",
    "no_dossier": "VM19068",
    "no_mandat": "3873",
    "mandat_id": "3722",
    "hektor_mandat_id": "3873",
    "numero": "3430",
    "mandat_annonce_id": "10330"
  },
  {
    "hektor_annonce_id": "10018",
    "no_dossier": "VM19002",
    "no_mandat": "3902",
    "mandat_id": "3721",
    "hektor_mandat_id": "3902",
    "numero": "3247",
    "mandat_annonce_id": "10368"
  },
  {
    "hektor_annonce_id": "10019",
    "no_dossier": "VM19050",
    "no_mandat": "3875",
    "mandat_id": "3720",
    "hektor_mandat_id": "3875",
    "numero": "3425",
    "mandat_annonce_id": "10332"
  },
  {
    "hektor_annonce_id": "1002",
    "no_dossier": "VA22238",
    "no_mandat": "4924",
    "mandat_id": "204",
    "hektor_mandat_id": "4924",
    "numero": "17770",
    "mandat_annonce_id": "11810"
  },
  {
    "hektor_annonce_id": "10025",
    "no_dossier": "VM19106",
    "no_mandat": "3860",
    "mandat_id": "3723",
    "hektor_mandat_id": "3860",
    "numero": "3478",
    "mandat_annonce_id": "10303"
  },
  {
    "hektor_annonce_id": "10028",
    "no_dossier": "VM19158",
    "no_mandat": "3855",
    "mandat_id": "3724",
    "hektor_mandat_id": "3855",
    "numero": "3473",
    "mandat_annonce_id": "10297"
  }
]
```
