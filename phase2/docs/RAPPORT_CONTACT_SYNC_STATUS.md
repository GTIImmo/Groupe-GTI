# Rapport statut contacts

Controle local de l'extraction ContactById, de la couche contacts phase 2 et de l'etat de push Supabase.

## Synthese

- Contacts listing local : `355912`
- Fiches detail recuperees : `348252`
- Fiches detail restantes : `7660`
- Contacts app eligibles Supabase : `58723`
- Contacts avec recherche active : `3921`
- Dernier run detail : `success` / `2026-09-11T04:22:55Z`

## Donnees completes

```json
{
  "generated_at": "2026-09-11T04:42:04+00:00",
  "hektor": {
    "db_exists": true,
    "contact_state": {
      "total": 355912,
      "detail_synced": 348252,
      "detail_missing": 7660,
      "latest_detail_sync_at": "2026-09-11T04:22:54Z"
    },
    "raw_contact_details": 348252,
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
      "total": 9558,
      "not_found": 9430,
      "timeout_or_connect": 29,
      "latest": [
        {
          "created_at": "2026-09-11T02:39:04Z",
          "object_id": "604627",
          "error_message": "403 Client Error: Forbidden for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=604627&version=v2"
        },
        {
          "created_at": "2026-09-11T02:10:57Z",
          "object_id": "423771",
          "error_message": "403 Client Error: Forbidden for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=423771&version=v2"
        },
        {
          "created_at": "2026-09-10T02:39:05Z",
          "object_id": "604627",
          "error_message": "403 Client Error: Forbidden for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=604627&version=v2"
        },
        {
          "created_at": "2026-09-10T02:10:58Z",
          "object_id": "423771",
          "error_message": "403 Client Error: Forbidden for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=423771&version=v2"
        },
        {
          "created_at": "2026-09-09T02:39:04Z",
          "object_id": "604627",
          "error_message": "403 Client Error: Forbidden for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=604627&version=v2"
        }
      ]
    },
    "latest_run": {
      "id": 3962,
      "status": "success",
      "started_at": "2026-09-11T04:22:12Z",
      "finished_at": "2026-09-11T04:22:55Z",
      "heartbeat_at": "2026-09-11T04:22:55Z",
      "current_step": "contact_detail_batch",
      "current_endpoint": "contact_detail",
      "current_object_id": null,
      "current_page": null,
      "progress_done": 37,
      "progress_total": 37,
      "progress_unit": "objects",
      "notes": "details_synced=37; errors=0; hard_errors=0; not_found=0; selection_mode=missing_or_changed; before_with_detail=348229; after_with_detail=348252",
      "heartbeat_age_minutes": 19
    }
  },
  "phase2": {
    "db_exists": true,
    "contacts_layer": {
      "total": 355978,
      "active": 171886,
      "archived": 184092,
      "eligible_supabase": 58723,
      "with_relation": 109231,
      "with_active_search": 3921,
      "with_any_search": 68021,
      "with_contact_detail": 348252
    },
    "relations_layer": {
      "total": 165942,
      "active_annonce": 79826,
      "transaction": 33453,
      "by_role": [
        {
          "role_contact": "mandant",
          "count": 74080
        },
        {
          "role_contact": "proprietaire",
          "count": 58409
        },
        {
          "role_contact": "acquereur_compromis",
          "count": 13256
        },
        {
          "role_contact": "acquereur_offre",
          "count": 11121
        },
        {
          "role_contact": "acquereur_vente",
          "count": 9076
        }
      ]
    },
    "searches_layer": {
      "total": 77009,
      "active": 4127,
      "archived": 72882
    },
    "duplicates_layer": {
      "groups": 37282,
      "high_or_critical": 24243,
      "suspected_mass_archive_error": 10896
    },
    "supabase_push_state": [
      {
        "table_name": "app_contact_current",
        "rows_marked_pushed": 58709,
        "latest_pushed_at": "2026-09-11T02:47:27+00:00"
      },
      {
        "table_name": "app_contact_relation_current",
        "rows_marked_pushed": 79828,
        "latest_pushed_at": "2026-09-11T02:47:18+00:00"
      },
      {
        "table_name": "app_contact_search_current",
        "rows_marked_pushed": 11006,
        "latest_pushed_at": "2026-09-11T02:47:27+00:00"
      }
    ]
  }
}
```
