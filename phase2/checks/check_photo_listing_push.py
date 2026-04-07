from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync.export_app_payload import build_payload
from phase2.sync.push_upgrade_to_supabase import build_current_dossiers


def main() -> None:
    payload = build_payload(limit=None, include_filter_catalog=False)
    rows = build_current_dossiers(payload["dossiers"])
    with_photo = [row for row in rows if str(row.get("photo_url_listing") or "").strip()]
    print("rows_total", len(rows))
    print("rows_with_photo", len(with_photo))
    if with_photo:
        print("sample", with_photo[0])
    else:
        print("sample", None)


if __name__ == "__main__":
    main()
