# Rapport qualite phase 2

Controles automatises de coherence sur `phase2.sqlite`.

## Metriques

- `vue_generale_total` : 21853 | attente : doit rester stable entre deux runs hors variation source
- `demandes_total` : 21429 | attente : doit rester stable entre deux runs hors variation source
- `missing_titles` : 0 | attente : 0
- `view_generale_without_dossier` : 0 | attente : 0
- `demandes_without_view_generale` : 0 | attente : 0
- `mandat_numero_id_collision` : 3020 | attente : surveiller, indicateur borne a 5000 pour detecter les cas type 59449/44506

## Echantillons

### `sample_mandat_numero_id_collision`

```json
[
  {
    "hektor_annonce_id": "10043",
    "no_dossier": "VM19360",
    "no_mandat": "3955",
    "mandat_id": "3733",
    "hektor_mandat_id": "3955",
    "numero": "3065",
    "mandat_annonce_id": "10434"
  },
  {
    "hektor_annonce_id": "1005",
    "no_dossier": "VA22364",
    "no_mandat": "4758",
    "mandat_id": "208",
    "hektor_mandat_id": "4758",
    "numero": "1772",
    "mandat_annonce_id": "11424"
  },
  {
    "hektor_annonce_id": "10057",
    "no_dossier": "VM19522",
    "no_mandat": "3818",
    "mandat_id": "3737",
    "hektor_mandat_id": "3818",
    "numero": "3616",
    "mandat_annonce_id": "10252"
  },
  {
    "hektor_annonce_id": "10058",
    "no_dossier": "VM19542",
    "no_mandat": "3814",
    "mandat_id": "3738",
    "hektor_mandat_id": "3814",
    "numero": "3637",
    "mandat_annonce_id": "10245"
  },
  {
    "hektor_annonce_id": "10059",
    "no_dossier": "VM19562",
    "no_mandat": "3813",
    "mandat_id": "3739",
    "hektor_mandat_id": "3813",
    "numero": "13775",
    "mandat_annonce_id": null
  },
  {
    "hektor_annonce_id": "10075",
    "no_dossier": "VM19938",
    "no_mandat": "3784",
    "mandat_id": "3745",
    "hektor_mandat_id": "3784",
    "numero": "3685",
    "mandat_annonce_id": "10163"
  },
  {
    "hektor_annonce_id": "10081",
    "no_dossier": "VM20066",
    "no_mandat": "3774",
    "mandat_id": "3746",
    "hektor_mandat_id": "3774",
    "numero": "3786",
    "mandat_annonce_id": "10149"
  },
  {
    "hektor_annonce_id": "10084",
    "no_dossier": "VM20100",
    "no_mandat": "3770",
    "mandat_id": "3748",
    "hektor_mandat_id": "3770",
    "numero": "3950",
    "mandat_annonce_id": null
  },
  {
    "hektor_annonce_id": "10108",
    "no_dossier": "VM20432",
    "no_mandat": "3733",
    "mandat_id": "3759",
    "hektor_mandat_id": "3733",
    "numero": "3955",
    "mandat_annonce_id": "10043"
  },
  {
    "hektor_annonce_id": "1011",
    "no_dossier": "VA22486",
    "no_mandat": "5509",
    "mandat_id": "212",
    "hektor_mandat_id": "5509",
    "numero": "2920",
    "mandat_annonce_id": "13583"
  },
  {
    "hektor_annonce_id": "10113",
    "no_dossier": "VM20516",
    "no_mandat": "3739",
    "mandat_id": "3762",
    "hektor_mandat_id": "3739",
    "numero": "3813",
    "mandat_annonce_id": "10059"
  },
  {
    "hektor_annonce_id": "10115",
    "no_dossier": "VM20536",
    "no_mandat": "3767",
    "mandat_id": "3764",
    "hektor_mandat_id": "3767",
    "numero": "3723",
    "mandat_annonce_id": "10120"
  },
  {
    "hektor_annonce_id": "10129",
    "no_dossier": "VM20604",
    "no_mandat": "3720",
    "mandat_id": "3769",
    "hektor_mandat_id": "3720",
    "numero": "3875",
    "mandat_annonce_id": "10019"
  },
  {
    "hektor_annonce_id": "10149",
    "no_dossier": "VM20878",
    "no_mandat": "3786",
    "mandat_id": "3774",
    "hektor_mandat_id": "3786",
    "numero": "3681",
    "mandat_annonce_id": "10165"
  },
  {
    "hektor_annonce_id": "10153",
    "no_dossier": "VM20918",
    "no_mandat": "3695",
    "mandat_id": "3777",
    "hektor_mandat_id": "3695",
    "numero": "3964",
    "mandat_annonce_id": "9961"
  }
]
```
