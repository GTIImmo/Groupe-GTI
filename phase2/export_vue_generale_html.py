import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from refresh_views import PHASE2_DB, HEKTOR_DB, SQL_REFRESH_VUE_GENERALE

OUTPUT_HTML = HERE / "vue_generale.html"
PAGE_SIZE = 200


def fetch_rows() -> list[dict]:
    con = sqlite3.connect(PHASE2_DB)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        cur.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        cur.executescript(SQL_REFRESH_VUE_GENERALE)
        con.commit()
        rows = cur.execute(
            """
            SELECT
                hektor_annonce_id, numero_dossier, numero_mandat, titre_bien, ville,
                type_bien, prix, commercial_nom, statut_annonce,
                validation_diffusion_state, etat_visibilite, nb_portails_actifs,
                portails_resume, etat_transaction,
                alerte_principale, priority, motif_blocage, next_action,
                commentaire_resume
            FROM app_view_generale
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 4
                    WHEN 'high' THEN 3
                    WHEN 'normal' THEN 2
                    WHEN 'low' THEN 1
                    ELSE 0
                END DESC,
                numero_dossier
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def build_html(rows: list[dict]) -> str:
    payload = json.dumps(rows, ensure_ascii=False).replace("</script>", "<\\/script>")
    total = len(rows)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vue générale - Outil métier Hektor</title>
<style>
:root{{--bg:#f4ede4;--panel:#fffdfa;--soft:#f8f1e7;--line:#dacdb7;--ink:#171412;--muted:#75695d;--brand:#8f4d31;--blue:#355e77;--green:#2f7d4f;--amber:#b77a1f;--red:#b04335;--shadow:0 18px 36px rgba(72,43,21,.08);--r1:28px;--r2:18px;--r3:12px;--title:Georgia,"Times New Roman",serif;--body:"Segoe UI",Tahoma,sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(180deg,#fbf7f0 0%,var(--bg) 100%);font-family:var(--body);color:var(--ink)}}
.app{{max-width:1660px;margin:0 auto;padding:24px}}.panel{{background:var(--panel);border:1px solid var(--line);border-radius:var(--r2);box-shadow:var(--shadow)}}
.top{{display:grid;grid-template-columns:1.45fr 1fr;gap:18px;margin-bottom:18px}}.hero{{padding:28px;border-radius:var(--r1);background:linear-gradient(135deg,rgba(143,77,49,.97),rgba(97,44,26,.95));color:#fff7f0;box-shadow:0 24px 48px rgba(72,43,21,.12)}}
.eyebrow{{font-size:12px;text-transform:uppercase;letter-spacing:.15em;opacity:.8}}h1{{margin:10px 0 0;font:700 40px/1 var(--title)}}.hero p{{max-width:800px;line-height:1.6;color:rgba(255,247,240,.9)}}
.hero-meta{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px}}.hero-card{{padding:14px 16px;border-radius:var(--r2);background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.14)}}.hero-card b{{display:block;margin-top:8px;font:700 24px/1 var(--title)}}
.notes{{display:grid;gap:14px}}.note{{padding:18px 20px}}.note h2,.head h2,.detail-head h2{{margin:0;font:700 24px/1.1 var(--title)}}.note p,.head p,.detail-head p{{margin:8px 0 0;color:var(--muted);line-height:1.5}}
.controls{{padding:18px 20px 20px;margin-bottom:18px}}.filters{{display:grid;grid-template-columns:2.2fr repeat(5,minmax(0,1fr));gap:12px}}label{{display:block;margin-bottom:7px;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}input,select{{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:var(--r3);font:inherit;background:#fff}}
.quick{{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}}.chip{{padding:8px 12px;border-radius:999px;border:1px solid var(--line);background:var(--soft);cursor:pointer}}.chip.on{{background:var(--brand);border-color:var(--brand);color:#fff}}
.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:18px}}.stat{{padding:16px 18px}}.stat .l{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}.stat .v{{display:block;margin-top:10px;font:700 30px/1 var(--title)}}
.workspace{{display:grid;grid-template-columns:1.55fr .95fr;gap:18px}}.head,.detail-head{{padding:20px 22px 14px;border-bottom:1px solid var(--line);background:var(--soft)}}.head{{display:flex;justify-content:space-between;align-items:center;gap:14px}}
.pager{{display:flex;gap:10px;align-items:center}}button{{border:0;border-radius:12px;padding:10px 14px;background:var(--brand);color:#fff;font:inherit;cursor:pointer}}button:disabled{{opacity:.4;cursor:default}}
.list{{overflow:auto;max-height:calc(100vh - 292px)}}table{{width:100%;min-width:1080px;border-collapse:collapse}}th{{position:sticky;top:0;background:rgba(255,253,250,.98);z-index:1;text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}td{{padding:13px 14px;border-bottom:1px solid rgba(218,205,183,.65);vertical-align:top}}tbody tr:hover{{background:rgba(143,77,49,.05)}}tbody tr.sel{{background:rgba(53,94,119,.09)}}
.mono{{font-family:Consolas,Monaco,monospace;font-size:12px}}.stack{{display:grid;gap:6px}}.title{{font-weight:700;line-height:1.45}}.muted{{color:var(--muted)}}.empty{{color:#aa9b8a;font-style:italic}}
.badge{{display:inline-flex;align-items:center;width:fit-content;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}}.state-Vendu,.validation-valide,.vis-visible{{background:rgba(47,125,79,.14);color:var(--green)}}.state-Valide,.state-Diffuse,.state-Compromis_signe,.state-Compromis_fixe,.state-Vente_fixee{{background:rgba(53,94,119,.12);color:var(--blue)}}.state-Offre_validee,.state-Offre_recue,.state-A_valider,.priority-high{{background:rgba(183,122,31,.14);color:var(--amber)}}.state-Annule,.state-Bloque,.vis-en_erreur,.priority-urgent{{background:rgba(176,67,53,.13);color:var(--red)}}.priority-normal{{background:rgba(23,20,18,.08);color:var(--ink)}}.priority-low,.priority-none,.state-Non_qualifie,.state-sans_transaction,.validation-a_controler,.vis-non_diffusable{{background:rgba(117,105,93,.13);color:var(--muted)}}
.detail{{min-height:calc(100vh - 210px);display:grid;grid-template-rows:auto 1fr;overflow:hidden}}.detail-body{{padding:20px 22px 24px;display:grid;gap:18px;align-content:start}}.highlight{{padding:18px;border-radius:var(--r2);background:linear-gradient(135deg,rgba(53,94,119,.1),rgba(53,94,119,.04));border:1px solid rgba(53,94,119,.14)}}.highlight h3{{margin:0;font:700 26px/1.1 var(--title)}}.highlight p{{margin:8px 0 0;color:var(--muted);line-height:1.55}}.dgrid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}.dcard{{padding:14px 15px;border-radius:var(--r3);border:1px solid var(--line);background:var(--soft)}}.dcard .l{{margin-bottom:8px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}.dcard .v{{font-size:15px;line-height:1.5}}
@media (max-width:1280px){{.top,.workspace{{grid-template-columns:1fr}}.filters{{grid-template-columns:repeat(2,minmax(0,1fr))}}.hero-meta,.notes,.stats,.dgrid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.detail{{min-height:auto}}}}
@media (max-width:740px){{.app{{padding:16px}}h1{{font-size:32px}}.filters,.hero-meta,.stats,.dgrid{{grid-template-columns:1fr}}.list{{max-height:none}}}}
</style></head>
<body><main class="app">
<section class="top">
  <section class="hero">
    <div class="eyebrow">Phase 2 · Poste de pilotage</div>
    <h1>Vue générale des dossiers</h1>
    <p>Lecture transversale du stock Hektor consolidé. Cette vue sert de tableau central avant fiche dossier, files métier et décisions de diffusion.</p>
    <div class="hero-meta">
      <div class="hero-card"><span>Dossiers chargés</span><b>{total}</b></div>
      <div class="hero-card"><span>Positionnement</span><b>Pilotage réseau</b></div>
      <div class="hero-card"><span>Usage</span><b>Liste + détail</b></div>
    </div>
  </section>
  <section class="notes">
    <article class="panel note"><h2>Lecture métier</h2><p>Le statut global donne l’étape principale. Le sous-statut précise la situation opérationnelle. L’alerte remonte le point d’attention immédiat.</p></article>
    <article class="panel note"><h2>Point de vigilance</h2><p>Les dossiers archivés encore marqués <strong>Actif</strong> dans Hektor restent volontairement non qualifiés tant que le correctif amont n’est pas appliqué.</p></article>
  </section>
</section>

<section class="panel controls">
  <div class="filters">
    <div><label for="q">Recherche</label><input id="q" placeholder="Dossier, titre, ville, commercial, action"></div>
    <div><label for="commercial">Commercial</label><select id="commercial"></select></div>
    <div><label for="statut">Statut global</label><select id="statut"></select></div>
    <div><label for="alerte">Alerte</label><select id="alerte"></select></div>
    <div><label for="validation">Validation</label><select id="validation"></select></div>
    <div><label for="transaction">Transaction</label><select id="transaction"></select></div>
  </div>
  <div class="quick" id="quickbar">
    <button class="chip on" data-quick="">Tout le stock</button>
    <button class="chip" data-quick="A valider">À valider</button>
    <button class="chip" data-quick="Valide">Validés</button>
    <button class="chip" data-quick="Diffuse">Diffusés</button>
    <button class="chip" data-quick="Offre validee">Offres validées</button>
    <button class="chip" data-quick="Vendu">Vendus</button>
    <button class="chip" data-quick="__alertes__">Avec alerte</button>
  </div>
  <section class="stats">
    <article class="panel stat"><div class="l">Dossiers visibles</div><span class="v" id="stat-total">{total}</span></article>
    <article class="panel stat"><div class="l">À valider</div><span class="v" id="stat-a-valider">0</span></article>
    <article class="panel stat"><div class="l">Diffusés</div><span class="v" id="stat-diffuses">0</span></article>
    <article class="panel stat"><div class="l">Offres validées</div><span class="v" id="stat-offres-validees">0</span></article>
    <article class="panel stat"><div class="l">Non qualifiés</div><span class="v" id="stat-non-qualifies">0</span></article>
  </section>
</section>

<section class="workspace">
  <section class="panel">
    <div class="head">
      <div><h2>Liste de pilotage</h2><p id="result-count">0 dossier</p></div>
      <div class="pager"><button id="prev">Précédent</button><span id="page-label" class="muted"></span><button id="next">Suivant</button></div>
    </div>
    <div class="list"><table><thead><tr><th>Dossier</th><th>Bien</th><th>Commercial</th><th>Statut</th><th>Diffusion</th><th>Transaction</th><th>Action</th></tr></thead><tbody id="rows"></tbody></table></div>
  </section>
  <aside class="panel detail">
    <div class="detail-head"><h2>Fiche rapide</h2><p>Détail immédiat du dossier sélectionné sans quitter la liste.</p></div>
    <div class="detail-body" id="detail-body"></div>
  </aside>
</section>

<script id="data-json" type="application/json">{payload}</script>
<script>
const PAGE_SIZE={PAGE_SIZE},DATA=JSON.parse(document.getElementById('data-json').textContent);let currentPage=1,filteredRows=DATA,selectedAnnonceId=null,quickFilter='';
const els={{q:document.getElementById('q'),commercial:document.getElementById('commercial'),statut:document.getElementById('statut'),alerte:document.getElementById('alerte'),validation:document.getElementById('validation'),transaction:document.getElementById('transaction'),quickbar:document.getElementById('quickbar'),rows:document.getElementById('rows'),detailBody:document.getElementById('detail-body'),resultCount:document.getElementById('result-count'),statTotal:document.getElementById('stat-total'),statAValider:document.getElementById('stat-a-valider'),statDiffuses:document.getElementById('stat-diffuses'),statOffresValidees:document.getElementById('stat-offres-validees'),statNonQualifies:document.getElementById('stat-non-qualifies'),prev:document.getElementById('prev'),next:document.getElementById('next'),pageLabel:document.getElementById('page-label')}};
const LABELS={{validation_diffusion_state:{{a_controler:'À contrôler',valide:'Validé',refuse:'Refusé',en_attente_commercial:'En attente commercial'}},etat_visibilite:{{non_diffusable:'Non diffusable',diffusable_non_visible:'Diffusable non visible',visible:'Visible',en_erreur:'Erreur diffusion',a_verifier:'À vérifier'}},etat_transaction:{{sans_transaction:'Sans transaction',offre_en_cours:'Offre en cours',compromis_en_cours:'Compromis en cours',vente_en_cours:'Vente en cours'}}}};
function e(v){{return String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}}function u(k){{return[...new Set(DATA.map(r=>r[k]||'').filter(Boolean))].sort((a,b)=>a.localeCompare(b,'fr'))}}function d(k,v){{return v===null||v===undefined||v===''?'':(LABELS[k]?.[v]||v)}}function fill(el,key,label){{el.innerHTML=['<option value="">'+label+'</option>'].concat(u(key).map(v=>`<option value="${{e(v)}}">${{e(v)}}</option>`)).join('')}}function bc(kind,value){{return`badge ${{kind}}-${{String(value||'none').replaceAll(' ','_')}}`}}
function updateStats(rows){{els.statTotal.textContent=rows.length;els.statAValider.textContent=rows.filter(r=>r.statut_global==='A valider').length;els.statDiffuses.textContent=rows.filter(r=>r.statut_global==='Diffuse').length;els.statOffresValidees.textContent=rows.filter(r=>r.statut_global==='Offre validee').length;els.statNonQualifies.textContent=rows.filter(r=>!r.statut_global).length}}
function renderDetail(row){{if(!row){{els.detailBody.innerHTML=`<div class="highlight"><h3>Aucun dossier sélectionné</h3><p>Sélectionne une ligne dans la liste pour afficher une fiche rapide exploitable sans quitter la vue générale.</p></div>`;return;}}const prix=row.prix?Number(row.prix).toLocaleString('fr-FR')+' EUR':'Prix absent',statut=row.statut_global||'Non qualifie',sous=row.sous_statut||'Sans sous-statut',alerte=row.alerte_principale||'Aucune',note=row.commentaire_resume||'Aucune note',action=row.next_action||'Aucune action définie',vis=d('etat_visibilite',row.etat_visibilite),validation=d('validation_diffusion_state',row.validation_diffusion_state),transaction=d('etat_transaction',row.etat_transaction),blocage=row.motif_blocage||'Aucun blocage déclaré',portails=row.portails_resume||'Aucun portail actif';els.detailBody.innerHTML=`<section class="highlight"><div class="eyebrow" style="color:#5d7281;opacity:1">Dossier ${{e(row.numero_dossier||'')}}</div><h3>${{e(row.titre_bien||'Titre absent')}}</h3><p>${{e(row.ville||'Ville absente')}} · ${{e(row.commercial_nom||'Commercial non attribué')}} · ${{prix}}</p></section><div class="dgrid"><div class="dcard"><div class="l">Statut global</div><div class="v"><span class="${{bc('state',statut)}}">${{e(statut)}}</span></div></div><div class="dcard"><div class="l">Sous-statut</div><div class="v">${{e(sous)}}</div></div><div class="dcard"><div class="l">Alerte</div><div class="v">${{row.alerte_principale?`<span class="${{bc('state',row.alerte_principale)}}">${{e(alerte)}}</span>`:e(alerte)}}</div></div><div class="dcard"><div class="l">Priorité</div><div class="v"><span class="${{bc('priority',row.priority)}}">${{e(row.priority||'normal')}}</span></div></div><div class="dcard"><div class="l">Validation diffusion</div><div class="v">${{e(validation)}}</div></div><div class="dcard"><div class="l">Visibilité</div><div class="v">${{e(vis)}}</div></div><div class="dcard"><div class="l">Transaction</div><div class="v">${{e(transaction)}}</div></div><div class="dcard"><div class="l">Portails actifs</div><div class="v">${{e(portails)}}</div></div><div class="dcard"><div class="l">Prochaine action</div><div class="v">${{e(action)}}</div></div><div class="dcard"><div class="l">Blocage</div><div class="v">${{e(blocage)}}</div></div></div><div class="dcard"><div class="l">Note de synthèse</div><div class="v">${{e(note)}}</div></div>`}}
function renderPage(rows,page){{const totalPages=Math.max(1,Math.ceil(rows.length/PAGE_SIZE)),start=(Math.min(Math.max(1,page),totalPages)-1)*PAGE_SIZE,pageRows=rows.slice(start,start+PAGE_SIZE);currentPage=Math.min(Math.max(1,page),totalPages);els.resultCount.textContent=`${{rows.length}} dossier${{rows.length>1?'s':''}}`;els.pageLabel.textContent=`Page ${{currentPage}} / ${{totalPages}}`;els.prev.disabled=currentPage<=1;els.next.disabled=currentPage>=totalPages;if(!selectedAnnonceId&&pageRows.length)selectedAnnonceId=pageRows[0].hektor_annonce_id;if(selectedAnnonceId&&!rows.some(r=>r.hektor_annonce_id===selectedAnnonceId))selectedAnnonceId=pageRows.length?pageRows[0].hektor_annonce_id:null;els.rows.innerHTML=pageRows.map(row=>{{const bien=row.titre_bien?e(row.titre_bien):'<span class="empty">Titre absent</span>',action=row.next_action?e(row.next_action):'<span class="empty">Non définie</span>',prix=row.prix?Number(row.prix).toLocaleString('fr-FR')+' EUR':'Prix absent',alerte=row.alerte_principale?`<div class="${{bc('state',row.alerte_principale)}}">${{e(row.alerte_principale)}}</div>`:'',statut=row.statut_global||'Non qualifie',sous=row.sous_statut||'Sans sous-statut',validation=d('validation_diffusion_state',row.validation_diffusion_state),vis=d('etat_visibilite',row.etat_visibilite),transaction=d('etat_transaction',row.etat_transaction),sel=row.hektor_annonce_id===selectedAnnonceId?'sel':'';return `<tr data-annonce-id="${{e(row.hektor_annonce_id||'')}}" class="${{sel}}"><td><div class="stack"><div class="mono">${{e(row.numero_dossier||'')}}</div><div class="muted">Mandat ${{e(row.numero_mandat||'')}}</div></div></td><td><div class="stack"><div class="title">${{bien}}</div><div class="muted">${{e(row.ville||'Ville absente')}} · ${{prix}}</div></div></td><td><div class="stack"><strong>${{e(row.commercial_nom||'Non attribué')}}</strong><div class="muted">${{e(row.statut_annonce||'Statut inconnu')}}</div></div></td><td><div class="stack"><div class="${{bc('state',statut)}}">${{e(statut)}}</div><div class="muted">${{e(sous)}}</div><div class="${{bc('priority',row.priority)}}">${{e(row.priority||'')}}</div>${{alerte}}</div></td><td><div class="stack"><div class="${{bc('validation',row.validation_diffusion_state)}}">${{e(validation)}}</div><div class="${{bc('vis',row.etat_visibilite)}}">${{e(vis)}}</div><div class="muted">${{row.nb_portails_actifs||0}} portail(x)</div></div></td><td><div class="stack"><div class="${{bc('state',row.etat_transaction)}}">${{e(transaction)}}</div></div></td><td><div class="stack">${{action}}</div></td></tr>`}}).join('');const selectedRow=rows.find(r=>r.hektor_annonce_id===selectedAnnonceId)||pageRows[0]||null;renderDetail(selectedRow);els.rows.querySelectorAll('tr[data-annonce-id]').forEach(tr=>tr.addEventListener('click',()=>{{selectedAnnonceId=tr.dataset.annonceId;renderPage(filteredRows,currentPage)}}))}}
function filterRows(){{const q=els.q.value.trim().toLowerCase(),commercial=els.commercial.value,statut=els.statut.value,alerte=els.alerte.value,validation=els.validation.value,transaction=els.transaction.value;filteredRows=DATA.filter(row=>{{const hay=[row.numero_dossier,row.numero_mandat,row.titre_bien,row.ville,row.commercial_nom,row.commentaire_resume,row.next_action,row.sous_statut].join(' ').toLowerCase(),quickMatch=!quickFilter||(quickFilter==='__alertes__'&&!!row.alerte_principale)||row.statut_global===quickFilter;return(!q||hay.includes(q))&&(!commercial||row.commercial_nom===commercial)&&(!statut||row.statut_global===statut)&&(!alerte||row.alerte_principale===alerte)&&(!validation||row.validation_diffusion_state===validation)&&(!transaction||row.etat_transaction===transaction)&&quickMatch}});updateStats(filteredRows);renderPage(filteredRows,1)}}
function bindQuick(){{els.quickbar.querySelectorAll('[data-quick]').forEach(btn=>btn.addEventListener('click',()=>{{quickFilter=btn.dataset.quick||'';els.quickbar.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));btn.classList.add('on');filterRows()}}))}}
fill(els.commercial,'commercial_nom','Tous les commerciaux');fill(els.statut,'statut_global','Tous les statuts globaux');fill(els.alerte,'alerte_principale','Toutes les alertes');fill(els.validation,'validation_diffusion_state','Toutes les validations');fill(els.transaction,'etat_transaction','Toutes les transactions');[els.q,els.commercial,els.statut,els.alerte,els.validation,els.transaction].forEach(el=>el.addEventListener('input',filterRows));els.prev.addEventListener('click',()=>renderPage(filteredRows,currentPage-1));els.next.addEventListener('click',()=>renderPage(filteredRows,currentPage+1));bindQuick();updateStats(DATA);renderPage(DATA,1);
</script></main></body></html>"""


def main() -> None:
    rows = fetch_rows()
    OUTPUT_HTML.write_text(build_html(rows), encoding="utf-8")
    print(f"Exported: {OUTPUT_HTML}")
    print(f"Rows: {len(rows)}")


if __name__ == "__main__":
    main()
