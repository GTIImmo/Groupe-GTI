# Rapport statut contacts

Controle local de l'extraction ContactById, de la couche contacts phase 2 et de l'etat de push Supabase.

## Synthese

- Contacts listing local : `354577`
- Fiches detail recuperees : `346918`
- Fiches detail restantes : `7659`
- Contacts app eligibles Supabase : `57173`
- Contacts avec recherche active : `3588`
- Dernier run detail : `success` / `2026-06-06T06:11:04Z`

## Donnees completes

```json
{
  "generated_at": "2026-06-06T06:21:47+00:00",
  "hektor": {
    "db_exists": true,
    "contact_state": {
      "total": 354577,
      "detail_synced": 346918,
      "detail_missing": 7659,
      "latest_detail_sync_at": "2026-06-05T21:47:39Z"
    },
    "raw_contact_details": 346918,
    "contact_detail_skip": {
      "total": 7659,
      "by_reason": [
        {
          "reason": "http_404_not_found",
          "count": 7657
        },
        {
          "reason": "http_403_forbidden",
          "count": 2
        }
      ]
    },
    "contact_detail_errors": {
      "total": 8408,
      "not_found": 8383,
      "timeout_or_connect": 15,
      "latest": [
        {
          "created_at": "2026-06-04T17:14:51Z",
          "object_id": "483095",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=483095&version=v2"
        },
        {
          "created_at": "2026-06-04T17:14:49Z",
          "object_id": "41239",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=41239&version=v2"
        },
        {
          "created_at": "2026-06-04T17:14:49Z",
          "object_id": "41238",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=41238&version=v2"
        },
        {
          "created_at": "2026-06-04T17:14:42Z",
          "object_id": "27689",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=27689&version=v2"
        },
        {
          "created_at": "2026-06-04T17:14:42Z",
          "object_id": "27688",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=27688&version=v2"
        }
      ]
    },
    "latest_run": {
      "id": 287,
      "status": "success",
      "started_at": "2026-06-06T06:10:55Z",
      "finished_at": "2026-06-06T06:11:04Z",
      "heartbeat_at": "2026-06-06T06:11:04Z",
      "current_step": "authenticate",
      "current_endpoint": null,
      "current_object_id": null,
      "current_page": null,
      "progress_done": 0,
      "progress_total": 1,
      "progress_unit": "step",
      "notes": "details_synced=0; errors=0; hard_errors=0; not_found=0; selection_mode=missing_or_changed; before_with_detail=346918; after_with_detail=346918",
      "heartbeat_age_minutes": 10
    }
  },
  "phase2": {
    "db_exists": true,
    "contacts_layer": {
      "total": 354577,
      "active": 170494,
      "archived": 184083,
      "eligible_supabase": 57173,
      "with_relation": 108793,
      "with_active_search": 3588,
      "with_any_search": 67637,
      "with_contact_detail": 346918
    },
    "relations_layer": {
      "total": 164769,
      "active_annonce": 77031,
      "transaction": 32856,
      "by_role": [
        {
          "role_contact": "proprietaire",
          "count": 85310
        },
        {
          "role_contact": "mandant",
          "count": 46603
        },
        {
          "role_contact": "acquereur_compromis",
          "count": 13058
        },
        {
          "role_contact": "acquereur_offre",
          "count": 10892
        },
        {
          "role_contact": "acquereur_vente",
          "count": 8906
        }
      ]
    },
    "searches_layer": {
      "total": 76585,
      "active": 3770,
      "archived": 72815
    },
    "duplicates_layer": {
      "groups": 36582,
      "high_or_critical": 23758,
      "suspected_mass_archive_error": 10713
    },
    "supabase_push_state": [
      {
        "table_name": "app_contact_current",
        "rows_marked_pushed": 191927,
        "latest_pushed_at": "2026-06-05T22:00:03+00:00"
      },
      {
        "table_name": "app_contact_relation_current",
        "rows_marked_pushed": 77031,
        "latest_pushed_at": "2026-06-05T22:00:03+00:00"
      },
      {
        "table_name": "app_contact_search_current",
        "rows_marked_pushed": 3770,
        "latest_pushed_at": "2026-06-05T17:08:38+00:00"
      }
    ]
  }
}
```
