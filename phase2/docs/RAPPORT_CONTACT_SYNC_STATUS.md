# Rapport statut contacts

Controle local de l'extraction ContactById, de la couche contacts phase 2 et de l'etat de push Supabase.

## Synthese

- Contacts listing local : `354965`
- Fiches detail recuperees : `347306`
- Fiches detail restantes : `7659`
- Contacts app eligibles Supabase : `57297`
- Contacts avec recherche active : `3632`
- Dernier run detail : `success` / `2026-07-10T04:03:38Z`

## Donnees completes

```json
{
  "generated_at": "2026-07-10T04:10:56+00:00",
  "hektor": {
    "db_exists": true,
    "contact_state": {
      "total": 354965,
      "detail_synced": 347306,
      "detail_missing": 7659,
      "latest_detail_sync_at": "2026-07-10T04:03:37Z"
    },
    "raw_contact_details": 347306,
    "contact_detail_skip": {
      "total": 7660,
      "by_reason": [
        {
          "reason": "http_404_not_found",
          "count": 7657
        },
        {
          "reason": "http_403_forbidden",
          "count": 3
        }
      ]
    },
    "contact_detail_errors": {
      "total": 8442,
      "not_found": 8384,
      "timeout_or_connect": 28,
      "latest": [
        {
          "created_at": "2026-07-10T01:06:59Z",
          "object_id": "423771",
          "error_message": "403 Client Error: Forbidden for url: https://groupe-gti-immobilier.la-boite-immo.com/Api/Contact/ContactById?id=423771&version=v2"
        },
        {
          "created_at": "2026-07-09T01:19:05Z",
          "object_id": "602355",
          "error_message": "GET /Api/Contact/ContactById did not return valid JSON after 1 attempts: GET /Api/Contact/ContactById failed after 1 attempts: HTTPSConnectionPool(host='groupe-gti-immobilier.la-boite-immo.com', port=443): Max retries ex"
        },
        {
          "created_at": "2026-07-09T01:18:44Z",
          "object_id": "602345",
          "error_message": "GET /Api/Contact/ContactById did not return valid JSON after 1 attempts: GET /Api/Contact/ContactById failed after 1 attempts: HTTPSConnectionPool(host='groupe-gti-immobilier.la-boite-immo.com', port=443): Max retries ex"
        },
        {
          "created_at": "2026-07-09T01:18:23Z",
          "object_id": "602344",
          "error_message": "GET /Api/Contact/ContactById did not return valid JSON after 1 attempts: GET /Api/Contact/ContactById failed after 1 attempts: ('Connection aborted.', ConnectionResetError(10054, 'Une connexion existante a d\u00fb \u00eatre ferm\u00e9e"
        },
        {
          "created_at": "2026-07-09T01:12:20Z",
          "object_id": "409298",
          "error_message": "GET /Api/Contact/ContactById did not return valid JSON after 1 attempts: GET /Api/Contact/ContactById failed after 1 attempts: HTTPSConnectionPool(host='groupe-gti-immobilier.la-boite-immo.com', port=443): Max retries ex"
        }
      ]
    },
    "latest_run": {
      "id": 1844,
      "status": "success",
      "started_at": "2026-07-10T04:03:29Z",
      "finished_at": "2026-07-10T04:03:38Z",
      "heartbeat_at": "2026-07-10T04:03:38Z",
      "current_step": "contact_detail_batch",
      "current_endpoint": "contact_detail",
      "current_object_id": null,
      "current_page": null,
      "progress_done": 19,
      "progress_total": 19,
      "progress_unit": "objects",
      "notes": "details_synced=19; errors=0; hard_errors=0; not_found=0; selection_mode=missing_or_changed; before_with_detail=347294; after_with_detail=347306",
      "heartbeat_age_minutes": 7
    }
  },
  "phase2": {
    "db_exists": true,
    "contacts_layer": {
      "total": 355104,
      "active": 171005,
      "archived": 184099,
      "eligible_supabase": 57297,
      "with_relation": 108985,
      "with_active_search": 3632,
      "with_any_search": 67712,
      "with_contact_detail": 347306
    },
    "relations_layer": {
      "total": 165103,
      "active_annonce": 77186,
      "transaction": 32985,
      "by_role": [
        {
          "role_contact": "proprietaire",
          "count": 123601
        },
        {
          "role_contact": "acquereur_compromis",
          "count": 13097
        },
        {
          "role_contact": "acquereur_offre",
          "count": 10934
        },
        {
          "role_contact": "acquereur_vente",
          "count": 8954
        },
        {
          "role_contact": "mandant",
          "count": 8517
        }
      ]
    },
    "searches_layer": {
      "total": 76668,
      "active": 3812,
      "archived": 72856
    },
    "duplicates_layer": {
      "groups": 36842,
      "high_or_critical": 23933,
      "suspected_mass_archive_error": 10783
    },
    "supabase_push_state": [
      {
        "table_name": "app_contact_current",
        "rows_marked_pushed": 57288,
        "latest_pushed_at": "2026-07-10T01:09:40+00:00"
      },
      {
        "table_name": "app_contact_relation_current",
        "rows_marked_pushed": 77186,
        "latest_pushed_at": "2026-07-10T01:08:40+00:00"
      },
      {
        "table_name": "app_contact_search_current",
        "rows_marked_pushed": 3809,
        "latest_pushed_at": "2026-07-10T01:09:40+00:00"
      }
    ]
  }
}
```
