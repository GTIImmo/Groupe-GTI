# Rapport statut contacts

Controle local de l'extraction ContactById, de la couche contacts phase 2 et de l'etat de push Supabase.

## Synthese

- Contacts listing local : `356870`
- Fiches detail recuperees : `349210`
- Fiches detail restantes : `7660`
- Contacts app eligibles Supabase : `59453`
- Contacts avec recherche active : `4059`
- Dernier run detail : `success` / `2026-11-10T04:36:45Z`

## Donnees completes

```json
{
  "generated_at": "2026-11-10T05:02:35+00:00",
  "hektor": {
    "db_exists": true,
    "contact_state": {
      "total": 356870,
      "detail_synced": 349210,
      "detail_missing": 7660,
      "latest_detail_sync_at": "2026-11-10T02:47:29Z"
    },
    "raw_contact_details": 349275,
    "contact_detail_skip": {
      "total": 7664,
      "by_reason": [
        {
          "reason": "http_404_not_found",
          "count": 7659
        },
        {
          "reason": "http_403_forbidden",
          "count": 5
        }
      ]
    },
    "contact_detail_errors": {
      "total": 9670,
      "not_found": 9456,
      "timeout_or_connect": 29,
      "latest": [
        {
          "created_at": "2026-11-10T02:34:51Z",
          "object_id": "604627",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=604627&version=v2"
        },
        {
          "created_at": "2026-11-10T02:08:07Z",
          "object_id": "423771",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=423771&version=v2"
        },
        {
          "created_at": "2026-11-09T02:34:53Z",
          "object_id": "604627",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=604627&version=v2"
        },
        {
          "created_at": "2026-11-09T02:08:10Z",
          "object_id": "423771",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=423771&version=v2"
        },
        {
          "created_at": "2026-11-08T02:34:54Z",
          "object_id": "604627",
          "error_message": "404 Client Error: Not Found for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=604627&version=v2"
        }
      ]
    },
    "latest_run": {
      "id": 5774,
      "status": "success",
      "started_at": "2026-11-10T04:36:39Z",
      "finished_at": "2026-11-10T04:36:45Z",
      "heartbeat_at": "2026-11-10T04:36:45Z",
      "current_step": "authenticate",
      "current_endpoint": null,
      "current_object_id": null,
      "current_page": null,
      "progress_done": 0,
      "progress_total": 1,
      "progress_unit": "step",
      "notes": "details_synced=0; errors=0; hard_errors=0; not_found=0; selection_mode=missing_or_changed; before_with_detail=349210; after_with_detail=349210",
      "heartbeat_age_minutes": 25
    }
  },
  "phase2": {
    "db_exists": true,
    "contacts_layer": {
      "total": 356934,
      "active": 172749,
      "archived": 184185,
      "eligible_supabase": 59453,
      "with_relation": 109820,
      "with_active_search": 4059,
      "with_any_search": 68295,
      "with_contact_detail": 349275
    },
    "relations_layer": {
      "total": 167965,
      "active_annonce": 81617,
      "transaction": 35047,
      "by_role": [
        {
          "role_contact": "mandant",
          "count": 74248
        },
        {
          "role_contact": "proprietaire",
          "count": 58670
        },
        {
          "role_contact": "acquereur_compromis",
          "count": 13308
        },
        {
          "role_contact": "acquereur_offre",
          "count": 11188
        },
        {
          "role_contact": "acquereur_vente",
          "count": 10551
        }
      ]
    },
    "searches_layer": {
      "total": 77321,
      "active": 4287,
      "archived": 73034
    },
    "duplicates_layer": {
      "groups": 37820,
      "high_or_critical": 24614,
      "suspected_mass_archive_error": 11048
    },
    "supabase_push_state": [
      {
        "table_name": "app_contact_current",
        "rows_marked_pushed": 94929,
        "latest_pushed_at": "2026-11-10T02:51:44+00:00"
      },
      {
        "table_name": "app_contact_relation_current",
        "rows_marked_pushed": 85409,
        "latest_pushed_at": "2026-11-10T02:51:44+00:00"
      },
      {
        "table_name": "app_contact_search_current",
        "rows_marked_pushed": 13267,
        "latest_pushed_at": "2026-11-10T02:51:44+00:00"
      }
    ]
  }
}
```
