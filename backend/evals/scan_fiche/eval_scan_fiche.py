"""
Eval du scan OCR (openai_listing_sheet_service) contre une fiche de reference a
verite connue. Detecte les REGRESSIONS de complétude/precision (ex. le 84->70) que
l'oeil nu laisse passer.

Usage :
    cd backend && python -m evals.scan_fiche.eval_scan_fiche
    (option) --fixture fiche_test_v1   --min-accuracy 0.80

Sort un tableau de score + la liste des ecarts. Code retour != 0 si sous le seuil
(pour brancher en CI plus tard). L'OCR n'etant pas deterministe, le seuil a une marge.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/
from PIL import Image
from app.settings import get_settings
from app.services import openai_listing_sheet_service as sheet

HERE = Path(__file__).resolve().parent


def norm(v: str) -> str:
    v = unicodedata.normalize("NFKD", str(v or "")).encode("ascii", "ignore").decode()
    return " ".join(v.lower().split())


def digits(v: str) -> str:
    return "".join(c for c in str(v or "") if c.isdigit())


def down_b64(path: Path, ms: int = 1280) -> str:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    ls = max(w, h)
    if ls > ms:
        s = ms / ls
        im = im.resize((round(w * s), round(h * s)))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def merged_extract(svc, pages: list[Path]) -> dict[str, str]:
    # OCR de chaque page + fusion (valeur non vide la plus fiable), comme le front.
    merged: dict[str, tuple[str, float]] = {}
    for p in pages:
        res = svc.extract({"imageBase64": f"data:image/jpeg;base64,{down_b64(p)}", "mimeType": "image/jpeg"})
        for k, item in res["fields"].items():
            val = item.get("value")
            conf = item.get("confidence") or 0
            if val and (k not in merged or conf > merged[k][1]):
                merged[k] = (val, conf)
    return {k: v for k, (v, _) in merged.items()}


def evaluate(gold: dict, got: dict[str, str]) -> dict:
    rows = []  # (key, kind, expected, ocr, ok)
    def check(key, kind, expected):
        ocr = got.get(key, "")
        present = bool(str(ocr).strip())
        if kind == "num":
            ok = present and digits(ocr) == digits(expected)
        elif kind == "enum":
            ok = present and (norm(expected) in norm(ocr) or norm(ocr) in norm(expected))
        elif kind == "text":
            ok = present and norm(expected) in norm(ocr)
        else:  # present
            ok = present
        rows.append((key, kind, expected, ocr, ok))

    for k, v in (gold.get("num") or {}).items():
        check(k, "num", v)
    for k, v in (gold.get("enum") or {}).items():
        check(k, "enum", v)
    for k, v in (gold.get("text") or {}).items():
        check(k, "text", v)
    for k in (gold.get("present") or []):
        if not any(r[0] == k for r in rows):  # eviter doublon si deja verifie ailleurs
            check(k, "present", "")

    total = len(rows)
    ok_n = sum(1 for r in rows if r[4])
    present_n = sum(1 for r in rows if str(r[3]).strip())
    return {"rows": rows, "total": total, "ok": ok_n, "present": present_n}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", default="fiche_test_v1")
    ap.add_argument("--min-accuracy", type=float, default=0.80)
    args = ap.parse_args()

    fx = HERE / "fixtures" / args.fixture
    gold = json.loads((fx / "gold.json").read_text(encoding="utf-8"))
    pages = sorted(fx.glob("page*.png"))
    if not pages:
        print(f"Aucune image dans {fx}"); return 2

    svc = sheet.OpenAIListingSheetService(get_settings())
    print(f"Eval scan OCR — fixture '{args.fixture}' ({len(pages)} pages)...")
    got = merged_extract(svc, pages)
    r = evaluate(gold, got)

    acc = r["ok"] / r["total"] if r["total"] else 0
    comp = r["present"] / r["total"] if r["total"] else 0
    print(f"\n  Champs verifies : {r['total']}")
    print(f"  Presents (non vides) : {r['present']}/{r['total']}  ({comp:.0%})  [completude]")
    print(f"  Corrects : {r['ok']}/{r['total']}  ({acc:.0%})  [precision]")

    fails = [row for row in r["rows"] if not row[4]]
    if fails:
        print(f"\n  ECARTS ({len(fails)}) :")
        for key, kind, exp, ocr, _ in fails:
            print(f"   [{kind:7}] {key:20} attendu={exp!r:30} obtenu={str(ocr)[:40]!r}")

    ok = acc >= args.min_accuracy
    print(f"\n  => {'PASS' if ok else 'FAIL'} (seuil precision {args.min_accuracy:.0%})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
