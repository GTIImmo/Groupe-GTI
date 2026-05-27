# Rapport statut contacts

Controle local de l'extraction ContactById, de la couche contacts phase 2 et de l'etat de push Supabase.

## Synthese

- Contacts listing local : `354380`
- Fiches detail recuperees : `82966`
- Fiches detail restantes : `271414`
- Contacts app eligibles Supabase : `56700`
- Contacts avec recherche active : `3074`
- Dernier run detail : `success_with_errors` / `2026-05-27T09:39:49Z`

## Donnees completes

```json
{
  "generated_at": "2026-05-27T13:21:42+00:00",
  "hektor": {
    "db_exists": true,
    "contact_state": {
      "total": 354380,
      "detail_synced": 82966,
      "detail_missing": 271414,
      "latest_detail_sync_at": "2026-05-27T09:39:49Z"
    },
    "raw_contact_details": 82966,
    "contact_detail_skip": {
      "total": 4272,
      "by_reason": [
        {
          "reason": "http_404_not_found",
          "count": 4272
        }
      ]
    },
    "contact_detail_errors": {
      "total": 5015,
      "not_found": 4998,
      "timeout_or_connect": 14,
      "latest": [
        {
          "created_at": "2026-05-27T09:38:50Z",
          "object_id": "484007",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=484007&version=v2"
        },
        {
          "created_at": "2026-05-27T09:38:15Z",
          "object_id": "483853",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=483853&version=v2"
        },
        {
          "created_at": "2026-05-27T09:38:15Z",
          "object_id": "483848",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=483848&version=v2"
        },
        {
          "created_at": "2026-05-27T09:37:50Z",
          "object_id": "483728",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=483728&version=v2"
        },
        {
          "created_at": "2026-05-27T09:37:50Z",
          "object_id": "483727",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=483727&version=v2"
        }
      ]
    },
    "latest_run": {
      "id": 207,
      "status": "success_with_errors",
      "started_at": "2026-05-27T09:13:16Z",
      "finished_at": "2026-05-27T09:39:49Z",
      "heartbeat_at": "2026-05-27T09:39:49Z",
      "current_step": "contact_detail_batch",
      "current_endpoint": "contact_detail",
      "current_object_id": null,
      "current_page": null,
      "progress_done": 2000,
      "progress_total": 2000,
      "progress_unit": "objects",
      "notes": "details_synced=1959; errors=41; before_with_detail=81007; after_with_detail=82966",
      "heartbeat_age_minutes": 221
    }
  },
  "phase2": {
    "db_exists": true,
    "contacts_layer": {
      "total": 354353,
      "active": 216039,
      "archived": 138314,
      "eligible_supabase": 56700,
      "with_relation": 105817,
      "with_active_search": 3074,
      "with_any_search": 17462,
      "with_contact_detail": 82939
    },
    "relations_layer": {
      "total": 157353,
      "active_annonce": 77010,
      "transaction": 32803,
      "by_role": [
        {
          "role_contact": "proprietaire",
          "count": 123428
        },
        {
          "role_contact": "acquereur_compromis",
          "count": 13041
        },
        {
          "role_contact": "acquereur_offre",
          "count": 10872
        },
        {
          "role_contact": "acquereur_vente",
          "count": 8890
        },
        {
          "role_contact": "mandant",
          "count": 1122
        }
      ]
    },
    "searches_layer": {
      "total": 19545,
      "active": 3227,
      "archived": 16318
    },
    "duplicates_layer": {
      "groups": 36454,
      "high_or_critical": 24797,
      "suspected_mass_archive_error": 13750
    },
    "supabase_push_state": [
      {
        "table_name": "app_contact_current",
        "rows_marked_pushed": 233324,
        "latest_pushed_at": "2026-05-27T12:56:29+00:00"
      },
      {
        "table_name": "app_contact_relation_current",
        "rows_marked_pushed": 77010,
        "latest_pushed_at": "2026-05-27T12:32:55+00:00"
      },
      {
        "table_name": "app_contact_search_current",
        "rows_marked_pushed": 3227,
        "latest_pushed_at": "2026-05-27T11:07:12+00:00"
      }
    ]
  }
}
```
