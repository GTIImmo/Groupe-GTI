"""Un .xlsx minimal, SANS bibliotheque (openpyxl n'est pas installe sur cette machine) : un zip de XML.

ecrire_xlsx(chemin, [(nom_feuille, lignes, largeurs), ...]) -- la 1re ligne de chaque feuille est l'en-tete (gras,
fond gris, figee) ; les autres cellules sont du texte renvoye a la ligne, aligne en haut. Les nombres restent des
nombres. Aucune formule, aucun lien externe.
"""
from __future__ import annotations

import zipfile
from xml.sax.saxutils import escape


def _col(n: int) -> str:
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _cellule(ref: str, v, style: int) -> str:
    if v is None or v == "":
        return '<c r="%s" s="%d"/>' % (ref, style)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return '<c r="%s" s="%d"><v>%s</v></c>' % (ref, style, v)
    t = escape(str(v)).replace("\r\n", "\n")
    t = "".join(ch for ch in t if ch in "\n\t" or ord(ch) >= 32)
    return '<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, style, t)


def _feuille(lignes, largeurs) -> str:
    cols = "".join('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i + 1, i + 1, w)
                   for i, w in enumerate(largeurs))
    rows = []
    for r, ligne in enumerate(lignes):
        style = 1 if r == 0 else 2
        cells = "".join(_cellule("%s%d" % (_col(c), r + 1), v, style) for c, v in enumerate(ligne))
        rows.append('<row r="%d">%s</row>' % (r + 1, cells))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" '
            'state="frozen"/></sheetView></sheetViews>'
            '<cols>%s</cols><sheetData>%s</sheetData>'
            '<autoFilter ref="A1:%s%d"/></worksheet>'
            % (cols, "".join(rows), _col(max(len(l) for l in lignes) - 1), len(lignes)))


STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
          '<fonts count="2"><font><sz val="10"/><name val="Calibri"/></font>'
          '<font><b/><sz val="10"/><name val="Calibri"/></font></fonts>'
          '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
          '<fill><patternFill patternType="solid"><fgColor rgb="FFD9D9D9"/></patternFill></fill></fills>'
          '<borders count="1"><border/></borders>'
          '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
          '<cellXfs count="3"><xf/>'
          '<xf fontId="1" fillId="2" applyFont="1" applyFill="1" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>'
          '<xf applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf></cellXfs>'
          '</styleSheet>')


def ecrire_xlsx(chemin, feuilles) -> None:
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1)
                             for i in range(len(feuilles)))
                   + '</Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '</Relationships>')
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(n[:31]), i + 1, i + 1)
                             for i, (n, _, _) in enumerate(feuilles))
                   + '</sheets><definedNames>'
                   + "".join('<definedName name="_xlnm._FilterDatabase" localSheetId="%d" hidden="1">\'%s\'!$A$1:$%s$%d</definedName>'
                             % (i, escape(n[:31]), _col(max(len(l) for l in ls) - 1), len(ls))
                             for i, (n, ls, _) in enumerate(feuilles))
                   + '</definedNames></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1)
                             for i in range(len(feuilles)))
                   + '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' % (len(feuilles) + 1)
                   + '</Relationships>')
        z.writestr("xl/styles.xml", STYLES)
        for i, (_, lignes, largeurs) in enumerate(feuilles):
            z.writestr("xl/worksheets/sheet%d.xml" % (i + 1), _feuille(lignes, largeurs))
