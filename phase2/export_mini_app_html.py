import json, sqlite3, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from refresh_views import HEKTOR_DB, PHASE2_DB, SQL_REFRESH_VUE_GENERALE

OUT = HERE / "app_metier.html"
OUT_JS = HERE / "app_metier_details.js"
DETAIL_DIR = HERE / "app_metier_detail_data"
PAGE_SIZE = 120
CHUNK = 100

HEAVY = {
    "texte_principal_html","images_preview_json","proprietaires_contacts","note_hektor_principale","mandat_note",
    "vente_notaires_resume","localite_json","mandats_json","proprietaires_json","honoraires_json","notes_json",
    "zones_json","particularites_json","pieces_json","images_json","textes_json","terrain_json","copropriete_json",
    "detail_raw_json","annonce_list_raw_json","corps_listing_html",
}

SQL = """
SELECT hektor_annonce_id,numero_dossier,numero_mandat,titre_bien,ville,code_postal,type_bien,prix,surface,date_maj,
date_enregistrement_annonce,photo_url_listing,ville_publique_listing,code_postal_public_listing,adresse_privee_listing,
responsable_affichage,responsable_type,statut_annonce,detail_statut_name,validation_diffusion_state,etat_visibilite,
etat_transaction,alerte_principale,priority,motif_blocage,next_action,commentaire_resume,
archive,diffusable,latitude_detail,longitude_detail,adresse_detail,ville_privee_detail,code_postal_prive_detail,
nb_images,nb_textes,nb_notes_hektor,nb_proprietaires,texte_principal_titre,texte_principal_html,images_preview_json,
nb_pieces,nb_chambres,surface_habitable_detail,etage_detail,terrasse_detail,garage_box_detail,surface_terrain_detail,
copropriete_detail,ascenseur_detail,proprietaires_resume,proprietaires_contacts,honoraires_resume,note_hektor_principale,
mandat_numero_source,mandat_type_source,mandat_date_enregistrement,mandat_date_debut,mandat_date_fin,mandat_date_cloture,
mandat_montant,mandants_texte,mandat_note,offre_id,offre_state,offre_event_date,offre_raw_status,offre_montant,
offre_acquereur_nom,offre_acquereur_portable,offre_acquereur_email,compromis_id,compromis_state,compromis_date_start,
compromis_date_end,date_signature_acte,prix_net_vendeur,prix_publique,compromis_part_admin,compromis_sequestre,
compromis_acquereurs_resume,vente_id,vente_date,vente_prix,vente_honoraires,vente_part_admin,vente_commission_agence,
vente_acquereurs_resume,vente_notaires_resume,mandat_type,localite_json,mandats_json,proprietaires_json,
honoraires_json,notes_json,zones_json,particularites_json,pieces_json,images_json,textes_json,terrain_json,
copropriete_json,detail_raw_json,annonce_list_raw_json,corps_listing_html
FROM app_view_generale
ORDER BY CASE priority WHEN 'urgent' THEN 4 WHEN 'high' THEN 3 WHEN 'normal' THEN 2 WHEN 'low' THEN 1 ELSE 0 END DESC, numero_dossier
"""


def rows():
    con = sqlite3.connect(PHASE2_DB)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        cur.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        cur.executescript(SQL_REFRESH_VUE_GENERALE)
        con.commit()
        return [dict(r) for r in cur.execute(SQL).fetchall()]
    finally:
        con.close()


def split_rows(all_rows):
    light, chunks = [], {}
    for idx, row in enumerate(all_rows):
        current = dict(row)
        chunk = f"chunk_{idx // CHUNK:04d}.js"
        current["detail_chunk"] = chunk
        chunks.setdefault(chunk, {})[str(row["hektor_annonce_id"])] = {k: current.pop(k, None) for k in HEAVY}
        light.append(current)
    return light, chunks


def write_chunks(chunks):
    DETAIL_DIR.mkdir(exist_ok=True)
    for old in DETAIL_DIR.glob("chunk_*.js"):
        old.unlink()
    for name, payload in chunks.items():
        data = json.dumps(payload, ensure_ascii=False).replace("</script>", "<\\/script>")
        (DETAIL_DIR / name).write_text(
            f'window.APP_DETAIL_CHUNKS=window.APP_DETAIL_CHUNKS||{{}};window.APP_DETAIL_CHUNKS["{name}"]={data};',
            encoding="utf-8",
        )


HTML = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>App metier</title>
<style>
:root{--forest:#21463a;--forest-soft:#2f5e4f;--mint:#dff1e7;--cream:#f7f3ec;--paper:#fffdfa;--ink:#1c2521;--muted:#68756f;--line:#d7d2c7;--line-soft:#ece7dd;--gold:#b5925c;--gold-soft:#d8c19b;--accent:#3f7a67;--shadow:0 24px 56px rgba(24,35,30,.08);--title:Georgia,"Times New Roman",serif;--body:"Segoe UI",Tahoma,sans-serif}*{box-sizing:border-box}body{margin:0;font:14px/1.55 var(--body);color:var(--ink);background:linear-gradient(180deg,#f5f1ea 0,#f0ebe2 40%,#f7f4ee 100%)}body:before{content:"";position:fixed;inset:0;background:repeating-linear-gradient(90deg,rgba(33,70,58,.03) 0,rgba(33,70,58,.03) 18px,transparent 18px,transparent 180px);pointer-events:none}.app{display:grid;grid-template-columns:300px minmax(0,1fr);min-height:100vh;position:relative}.side{position:relative;background:linear-gradient(180deg,#18342b 0,#21463a 46%,#2f5e4f 100%);color:#f5f7f4;padding:28px 22px;display:grid;gap:18px;align-content:start;box-shadow:inset -1px 0 0 rgba(255,255,255,.08)}.side:before{content:"";position:absolute;left:0;top:0;bottom:0;width:14px;background:linear-gradient(180deg,var(--gold) 0,#e1cfad 20%,rgba(255,255,255,.18) 20%,rgba(255,255,255,.18) 24%,var(--gold) 24%,var(--gold) 100%)}.brand{padding-left:16px;display:grid;gap:10px}.eyebrow{font-size:11px;letter-spacing:.18em;text-transform:uppercase;opacity:.78}.side h1{margin:0;font:700 32px/1 var(--title)}.side p{margin:0;color:rgba(245,247,244,.72)}.nav{display:grid;gap:10px}.side button{position:relative;padding:14px 16px 14px 18px;border:1px solid rgba(255,255,255,.1);border-radius:18px;text-align:left;background:rgba(255,255,255,.04);color:inherit;cursor:pointer;transition:.18s ease;overflow:hidden}.side button:before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:transparent}.side button:hover{background:rgba(255,255,255,.1)}.side button.on{background:linear-gradient(135deg,#f7f5ef,#ebe2d2);color:#173228;border-color:rgba(255,255,255,.2);font-weight:700}.side button.on:before{background:linear-gradient(180deg,var(--accent),var(--gold))}.side-stat{margin-left:16px;padding:16px 18px;border-radius:22px;background:linear-gradient(180deg,rgba(255,255,255,.1) 0,rgba(255,255,255,.05) 100%);border:1px solid rgba(255,255,255,.1)}.side-stat b{display:block;margin-top:10px;font:700 34px/1 var(--title)}.main{padding:24px;display:grid;gap:18px;position:relative}.panel{background:rgba(255,253,250,.92);border:1px solid var(--line);border-radius:24px;overflow:hidden;box-shadow:var(--shadow);backdrop-filter:blur(8px)}.hero{position:relative;display:grid;grid-template-columns:1.5fr .85fr;gap:18px;padding:28px 30px;border-radius:30px;background:linear-gradient(135deg,#1c4033 0,#356c5b 52%,#cfb180 100%);color:#f8fbf8;overflow:hidden}.hero:before{content:"";position:absolute;right:-90px;top:-60px;width:320px;height:320px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.18) 0,rgba(255,255,255,0) 68%)}.hero:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,255,255,.07) 0,rgba(255,255,255,0) 16%,rgba(255,255,255,.08) 16%,rgba(255,255,255,.08) 19%,transparent 19%,transparent 100%);mix-blend-mode:screen}.hero-copy,.hero-rail{position:relative;z-index:1}.hero h2{margin:8px 0 10px;font:700 40px/1.02 var(--title)}.hero p{margin:0;max-width:760px;color:rgba(248,251,248,.84)}.hero-rail{display:grid;gap:12px;align-content:start}.rail-card{padding:16px 18px;border-radius:20px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.16)}.rail-card b{display:block;margin-top:8px;font:700 26px/1 var(--title)}.toolbar,.summary{padding:20px}.filters{display:grid;grid-template-columns:2fr repeat(4,1fr);gap:12px}label{display:block;font-size:11px;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}input,select{width:100%;padding:12px 13px;border:1px solid var(--line);border-radius:16px;background:#fff;color:var(--ink);box-shadow:inset 0 1px 0 rgba(255,255,255,.7)}input:focus,select:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(63,122,103,.14)}.screen{display:none}.screen.on{display:grid;gap:18px}.split{display:grid;grid-template-columns:1.75fr .95fr;gap:18px}.head{padding:18px 20px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#fdfaf4 0,#f4ede2 100%);display:flex;justify-content:space-between;align-items:center;gap:12px}.head h3{margin:0;font:700 24px var(--title);color:#1d382f}.btn{padding:11px 14px;border:1px solid rgba(0,0,0,.04);border-radius:14px;background:linear-gradient(135deg,var(--accent),#2d5c4c);color:#fff;cursor:pointer;font-weight:700;box-shadow:0 10px 24px rgba(47,94,79,.22)}.btn:hover{filter:brightness(1.04)}.list{overflow:auto;max-height:calc(100vh - 305px)}table{width:100%;min-width:1120px;border-collapse:separate;border-spacing:0}th,td{padding:14px 16px;border-bottom:1px solid var(--line-soft);vertical-align:top}th{position:sticky;top:0;background:rgba(255,253,250,.98);text-align:left;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;z-index:1}tbody tr{cursor:pointer;transition:transform .14s ease,background .14s ease,box-shadow .14s ease}tbody tr:hover{background:#f1ebe0;box-shadow:inset 5px 0 0 rgba(63,122,103,.32)}.muted{color:var(--muted)}.mono{font-family:Consolas,monospace;font-size:12px}.sel{background:linear-gradient(90deg,rgba(63,122,103,.16) 0,rgba(63,122,103,.06) 100%);box-shadow:inset 5px 0 0 rgba(63,122,103,.6)}.cards{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.card{padding:12px;border:1px solid var(--line);border-radius:16px;background:linear-gradient(180deg,#fffdf9 0,#f4efe5 100%)}.card small{display:block;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.06em;font-size:11px}.section-title{margin:18px 0 8px;font:700 18px var(--title);color:#1d382f}.longtext{padding:14px;border:1px solid var(--line);border-radius:16px;background:linear-gradient(180deg,#fffdf8 0,#f5eee3 100%);line-height:1.6}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.stat{padding:18px;background:linear-gradient(180deg,#fffdfa 0,#f4ede3 100%)}.stat span{display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-size:11px}.stat b{display:block;font-size:32px;margin-top:10px;font-family:var(--title);color:#1d382f}.crm{display:grid;gap:18px}.crmH{padding:26px;border-radius:24px;background:linear-gradient(140deg,#1c4033 0,#356c5b 50%,#cfb180 100%);color:#fffdf9;box-shadow:0 24px 48px rgba(31,44,57,.22)}.crmT{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}.crmH h2{margin:0;font:700 34px var(--title)}.sub{margin:8px 0 0;color:rgba(255,253,249,.84)}.badges{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.badge{display:inline-flex;align-items:center;padding:6px 10px;border-radius:999px;background:rgba(255,253,249,.12);border:1px solid rgba(255,253,249,.18);font-size:12px}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:18px}.kpi{padding:14px 16px;border-radius:18px;background:rgba(12,18,24,.18);border:1px solid rgba(255,253,249,.1);backdrop-filter:blur(4px)}.kpi strong{display:block;font-size:24px;margin-top:6px;font-family:var(--title)}.crmL{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(320px,1fr);gap:18px}.stack{display:grid;gap:18px}.box{padding:18px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(180deg,rgba(255,253,249,.98) 0,rgba(247,242,234,.98) 100%);box-shadow:var(--shadow)}.box h4{margin:0 0 12px;font:700 21px var(--title);color:#1d382f}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.info{padding:12px;border:1px solid var(--line-soft);border-radius:16px;background:linear-gradient(180deg,#fffdf9 0,#f3ebde 100%)}.info small{display:block;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.06em;font-size:11px}.mainimg{margin-bottom:10px}.mainimg img{display:block;width:100%;max-height:420px;object-fit:cover;border-radius:20px;border:1px solid var(--line);background:#efe5d9}.thumbs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.thumbs a{display:block;border-radius:16px;overflow:hidden;border:1px solid var(--line);background:#f7efe3;box-shadow:var(--shadow)}.thumbs img{display:block;width:100%;height:110px;object-fit:cover}.list2{display:grid;gap:10px}.item,.step,.txn{padding:14px;border:1px solid var(--line-soft);border-radius:18px;background:linear-gradient(180deg,#fffdf9 0,#f3ebde 100%)}.item h5,.txn h5{margin:0 0 6px;font-size:16px;color:#1d382f}.step{border-left:5px solid var(--accent);border-radius:0 16px 16px 0}.txnG{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.txt{padding:14px;border:1px solid var(--line-soft);border-radius:18px;background:linear-gradient(180deg,#fffdf9 0,#f4ebdf 100%);line-height:1.6}.txt b{display:block;margin-bottom:8px;font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}.empty{color:var(--muted);font-style:italic}@media(max-width:1180px){.app,.filters,.split,.stats,.kpis,.crmL,.grid,.thumbs,.txnG,.hero{grid-template-columns:1fr}}@media(max-width:740px){.main{padding:16px}.side{padding:22px 16px}.hero h2{font-size:32px}.filters,.stats,.grid,.thumbs,.txnG{grid-template-columns:1fr}.list{max-height:none}}
</style>
</head>
<body>
<div class="app">
  <aside class="side">
    <div class="brand">
      <div class="eyebrow">Phase 2 · CRM reseau</div>
      <h1>Hektor Reseau</h1>
      <p>Console statique de pilotage des dossiers, compatible avec un hebergement GitHub Pages.</p>
    </div>
    <div class="nav">
      <button class="on" data-screen="dashboard">Accueil</button>
      <button data-screen="stock">Stock</button>
    </div>
    <div class="side-stat">
      <div class="eyebrow" style="opacity:.72">Dossiers charges</div>
      <b>__TOTAL__</b>
    </div>
  </aside>
  <main class="main">
    <section class="hero">
      <div class="hero-copy">
        <div class="eyebrow">Poste de pilotage</div>
        <h2>App metier consolidee</h2>
        <p>Lecture transversale du stock Hektor, avec fiche rapide immediatement exploitable et fiche complete chargee a la demande. Aucun backend requis pour l'heberger.</p>
      </div>
      <div class="hero-rail">
        <article class="rail-card"><span>Mode</span><b>Statique</b></article>
        <article class="rail-card"><span>Usage</span><b>Stock + CRM</b></article>
        <article class="rail-card"><span>Hebergement</span><b>GitHub Pages</b></article>
      </div>
    </section>
    <section class="panel toolbar">
      <div class="filters">
        <div><label for="q">Recherche</label><input id="q" placeholder="Dossier, mandat, ville, responsable"></div>
        <div><label for="commercial">Responsable</label><select id="commercial"></select></div>
        <div><label for="statut">Statut</label><select id="statut"></select></div>
        <div><label for="alerte">Alerte</label><select id="alerte"></select></div>
        <div><label for="validation">Validation</label><select id="validation"></select></div>
      </div>
    </section>
    <section class="screen on" id="screen-dashboard">
      <div class="stats">
        <article class="panel stat"><span>Dossiers visibles</span><b id="stat-total">__TOTAL__</b></article>
        <article class="panel stat"><span>A valider</span><b id="stat-a-valider">0</b></article>
        <article class="panel stat"><span>Diffuses</span><b id="stat-diffuses">0</b></article>
        <article class="panel stat"><span>Vendus</span><b id="stat-vendus">0</b></article>
      </div>
    </section>
    <section class="screen" id="screen-stock">
      <div class="split">
        <section class="panel">
          <div class="head">
            <div><h3>Stock</h3><p id="stock-count">0 dossier</p></div>
            <div><button class="btn" id="prev-stock">Prec</button> <span id="page-stock" class="muted"></span> <button class="btn" id="next-stock">Suiv</button></div>
          </div>
          <div class="list">
            <table>
              <thead><tr><th>Dossier</th><th>Annonce</th><th>Adresse / localite</th><th>Responsable</th><th>Statut</th><th>Action</th></tr></thead>
              <tbody id="rows-stock"></tbody>
            </table>
          </div>
        </section>
        <aside class="panel">
          <div class="head">
            <div><h3>Fiche rapide</h3><p>Clic pour selectionner, double-clic pour ouvrir la fiche complete.</p></div>
            <div><button class="btn" id="open-full-detail">Annonce complete</button></div>
          </div>
          <div class="summary" id="detail-body"></div>
        </aside>
      </div>
    </section>
    <section class="screen" id="screen-annonce">
      <section class="panel">
        <div class="head">
          <div><h3 id="full-detail-title">Annonce complete</h3><p id="full-detail-subtitle"></p></div>
          <div><button class="btn" id="back-to-stock">Retour stock</button></div>
        </div>
        <div class="summary" id="full-detail-body"></div>
      </section>
    </section>
  </main>
</div>
<script id="data-json" type="application/json">__DATA__</script>
<script>function card(l,v){return `<article class="card"><small>${String(l??'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]))}</small>${v||'<span class="empty">Absent</span>'}</article>`}</script>
<script>__SCRIPT__</script>
</body>
</html>"""

SCRIPT = r"""
const PAGE_SIZE=__PAGE_SIZE__,DATA=JSON.parse(document.getElementById('data-json').textContent);window.APP_DETAIL_CHUNKS=window.APP_DETAIL_CHUNKS||{};const L={};let sId=null,p=1,screen='dashboard';const E={q:document.getElementById('q'),commercial:document.getElementById('commercial'),statut:document.getElementById('statut'),alerte:document.getElementById('alerte'),validation:document.getElementById('validation'),rows:document.getElementById('rows-stock'),count:document.getElementById('stock-count'),page:document.getElementById('page-stock'),prev:document.getElementById('prev-stock'),next:document.getElementById('next-stock'),quick:document.getElementById('detail-body'),full:document.getElementById('full-detail-body'),title:document.getElementById('full-detail-title'),sub:document.getElementById('full-detail-subtitle'),open:document.getElementById('open-full-detail'),back:document.getElementById('back-to-stock'),t:document.getElementById('stat-total'),a:document.getElementById('stat-a-valider'),d:document.getElementById('stat-diffuses'),v:document.getElementById('stat-vendus')};const esc=v=>String(v??'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));const txt=v=>String(v??'').trim(),ok=v=>txt(v)!=='',j=v=>{if(!v)return null;try{return JSON.parse(v)}catch(_){return null}},join=(a,s=' · ')=>(a||[]).map(txt).filter(Boolean).join(s),br=v=>esc(v).replace(/\n+/g,'<br>'),badge=v=>`<span class="badge">${esc(v)}</span>`,cell=(l,v)=>`<div class="info"><small>${l}</small>${v||'<span class="empty">Absent</span>'}</div>`;function cards(a){const x=a.filter(e=>e&&ok(e[1])).map(e=>cell(e[0],esc(e[1])));return x.length?`<div class="grid">${x.join('')}</div>`:'<div class="empty">Aucune information exploitable</div>'}function props(b){if(!b||typeof b!=='object'||!b.props)return'';const x=Object.entries(b.props).map(([k,m])=>[txt((m&&m.label)||k),txt(m&&m.value)]).filter(e=>e[0]&&e[1]);return x.length?`<div class="grid">${x.map(e=>cell(e[0],esc(e[1]))).join('')}</div>`:''}function people(a){if(!Array.isArray(a)||!a.length)return'';return `<div class="list2">${a.map(p=>{const n=join([p.civilite,p.prenom,p.nom],' '),lines=[join([Array.isArray(p.typologie)?p.typologie.join(', '):'',p.dateenr]),join([p.coordonnees&&p.coordonnees.portable,p.coordonnees&&p.coordonnees.email]),join([p.localite&&p.localite.localite&&p.localite.localite.adresse,p.localite&&p.localite.localite&&p.localite.localite.code,p.localite&&p.localite.localite&&p.localite.localite.ville]),txt(p.commentaires||'')].filter(Boolean);return `<article class="item"><h5>${esc(n||'Contact')}</h5>${lines.map(l=>`<div>${br(l)}</div>`).join('')}</article>`}).join('')}</div>`}function notes(a,main){const x=[];if(ok(main))x.push({t:'Synthese',d:'',c:main});if(Array.isArray(a))a.slice(0,8).forEach(n=>ok(n&&n.content)&&x.push({t:n.type,d:n.date,c:n.content}));return x.length?`<div class="list2">${x.map(n=>`<article class="item"><div class="muted" style="margin-bottom:6px">${esc(n.t||'NOTE')}${n.d?' · '+esc(n.d):''}</div><div>${br(n.c||'')}</div></article>`).join('')}</div>`:''}function mandats(a,r){const x=[];if(Array.isArray(a))a.forEach(m=>x.push({h:join([m.numero,m.type]),l:[join(['Enregistrement',m.debut||m.dateenr||m.date_enregistrement],': '),join(['Fin',m.fin],': '),join(['Cloture',m.cloture],': '),join(['Montant',m.montant],': '),txt(m.note||'')].filter(Boolean)}));if(!x.length&&[r.mandat_numero_source,r.mandat_type_source,r.mandat_date_enregistrement,r.mandat_date_debut,r.mandat_date_fin,r.mandat_date_cloture,r.mandat_montant,r.mandants_texte,r.mandat_note].some(ok))x.push({h:join([r.mandat_numero_source,r.mandat_type_source]),l:[join(['Date enr.',r.mandat_date_enregistrement],': '),join(['Debut',r.mandat_date_debut],': '),join(['Fin',r.mandat_date_fin],': '),join(['Cloture',r.mandat_date_cloture],': '),join(['Montant',r.mandat_montant],': '),join(['Mandants',r.mandants_texte],': '),txt(r.mandat_note||'')].filter(Boolean)});return x.length?`<div class="list2">${x.map(m=>`<article class="step"><strong>${esc(m.h||'Mandat')}</strong>${m.l.map(l=>`<div>${br(l)}</div>`).join('')}</article>`).join('')}</div>`:''}function txn(r){const blocks=[{h:'Offre',l:[join(['ID',r.offre_id],': '),join(['Etat',r.offre_state],': '),join(['Date',r.offre_event_date],': '),join(['Montant',r.offre_montant],': '),join(['Acquereur',r.offre_acquereur_nom],': '),join(['Contact',join([r.offre_acquereur_portable,r.offre_acquereur_email])],': ')]},{h:'Compromis',l:[join(['ID',r.compromis_id],': '),join(['Etat',r.compromis_state],': '),join(['Debut',r.compromis_date_start],': '),join(['Fin',r.compromis_date_end],': '),join(['Prix public',r.prix_publique],': '),join(['Prix net vendeur',r.prix_net_vendeur],': '),join(['Sequestre',r.compromis_sequestre],': '),join(['Acquereurs',r.compromis_acquereurs_resume],': ')]},{h:'Vente',l:[join(['ID',r.vente_id],': '),join(['Date',r.vente_date],': '),join(['Prix',r.vente_prix],': '),join(['Honoraires',r.vente_honoraires],': '),join(['Commission agence',r.vente_commission_agence],': '),join(['Acquereurs',r.vente_acquereurs_resume],': '),join(['Notaires',r.vente_notaires_resume],': ')]}].map(b=>({h:b.h,l:b.l.filter(Boolean)}));return blocks.some(b=>b.l.length)?`<div class="txnG">${blocks.map(b=>`<article class="txn"><h5>${esc(b.h)}</h5>${b.l.length?b.l.map(l=>`<div>${br(l)}</div>`).join(''):'<div class="empty">Aucune information</div>'}</article>`).join('')}</div>`:''}function media(r,a){const x=Array.isArray(a)?a.filter(i=>i&&(i.url||i.full||i.path)):[];if(!x.length)return'';const f=x[0],t=x.slice(1,9);return `<div class="mainimg"><a href="${esc(f.full||f.url||f.path||'')}" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="${esc(f.url||f.full||f.path||'')}" alt="${esc(f.legend||r.titre_bien||'Image annonce')}" /></a></div>${t.length?`<div class="thumbs">${t.map(i=>`<a href="${esc(i.full||i.url||i.path||'')}" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="${esc(i.url||i.full||i.path||'')}" alt="${esc(i.legend||r.titre_bien||'Image annonce')}" /></a>`).join('')}</div>`:''}`}function texts(r,a){const x=[];ok(r.texte_principal_html)&&x.push(['DetailAnnonce',r.texte_principal_html,true]);ok(r.corps_listing_html)&&txt(r.corps_listing_html)!==txt(r.texte_principal_html)&&x.push(['ListAnnonces',r.corps_listing_html,true]);Array.isArray(a)&&a.forEach(t=>ok(t&&t.text)&&txt(t.text)!==txt(r.texte_principal_html)&&txt(t.text)!==txt(r.corps_listing_html)&&x.push([join([t.type,t.lang,t.titre])||'Texte',br(t.text),false]));return x.length?x.map(t=>`<article class="txt"><b>${esc(t[0])}</b>${t[2]?t[1]:t[1]}</article>`).join(''):''}function setScreen(n){screen=n;document.querySelectorAll('.side button[data-screen]').forEach(b=>b.classList.toggle('on',b.dataset.screen===n));document.querySelectorAll('.screen').forEach(s=>s.classList.remove('on'));document.getElementById('screen-'+n)?.classList.add('on')}function uniq(k){return [...new Set(DATA.map(r=>r[k]).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),'fr'))}function fill(sel,k,p){sel.innerHTML=`<option value="">${p}</option>`+uniq(k).map(v=>`<option>${esc(v)}</option>`).join('')}function filtered(){const q=txt(E.q.value).toLowerCase();return DATA.filter(r=>{if(E.commercial.value&&r.responsable_affichage!==E.commercial.value)return false;if(E.statut.value&&r.statut_global!==E.statut.value)return false;if(E.alerte.value&&r.alerte_principale!==E.alerte.value)return false;if(E.validation.value&&r.validation_diffusion_state!==E.validation.value)return false;if(!q)return true;return [r.numero_dossier,r.numero_mandat,r.titre_bien,r.ville,r.code_postal,r.type_bien,r.responsable_affichage,r.next_action,r.commentaire_resume,r.statut_annonce,r.detail_statut_name,r.adresse_privee_listing,r.adresse_detail,r.ville_publique_listing,r.ville_privee_detail,r.code_postal_public_listing,r.code_postal_prive_detail,r.mandants_texte,r.proprietaires_resume,r.offre_acquereur_nom,r.compromis_acquereurs_resume,r.vente_acquereurs_resume].join(' ').toLowerCase().includes(q)})}function quick(r){if(!r)return '<div class="muted">Aucun dossier selectionne</div>';const a=txt(r.adresse_privee_listing||r.adresse_detail||''),v=txt(r.ville_publique_listing||r.ville_privee_detail||r.ville||''),cp=txt(r.code_postal_public_listing||r.code_postal_prive_detail||r.code_postal||'');return `<h4>${esc(r.titre_bien||r.numero_dossier||'Annonce')}</h4><div class="muted">${esc(v)}${cp?' · '+esc(cp):''} · ${esc(r.responsable_affichage||'')}</div><div class="cards">${card('Dossier',esc(r.numero_dossier||''))+card('Mandat',esc(r.numero_mandat||''))+card('Type',esc(r.type_bien||''))+card('Prix',esc(r.prix||''))+card('Surface',esc(r.surface||r.surface_habitable_detail||''))+card('Adresse',esc(a))+card('Date enr.',esc(r.date_enregistrement_annonce||''))+card('Statut global',esc(r.statut_global||''))+card('Statut source',esc(r.statut_annonce||''))+card('Alerte',esc(r.alerte_principale||''))+card('Action',esc(r.next_action||''))+card('Transaction',esc(r.etat_transaction||''))}</div><div class="section-title">Acces detail</div><div class="longtext">La fiche complete charge les photos, le descriptif, les contacts, le mandat et le transactionnel dans une presentation type CRM.</div>`}function detail(r){if(!r)return '<div class="muted">Aucun detail</div>';const raw=j(r.detail_raw_json)||{},owners=j(r.proprietaires_json)||[],notesA=j(r.notes_json)||[],mandatsA=j(r.mandats_json)||[],imgs=j(r.images_json)||j(r.images_preview_json)||[],txts=j(r.textes_json)||[];return `<div class="crm"><section class="crmH"><div class="crmT"><div><h2>${esc(r.titre_bien||r.numero_dossier||'Annonce')}</h2><div class="sub">${esc(join([r.type_bien,r.adresse_privee_listing||r.adresse_detail,r.code_postal_public_listing||r.code_postal_prive_detail||r.code_postal,r.ville_publique_listing||r.ville_privee_detail||r.ville]))}</div><div class="badges">${[r.statut_global,r.validation_diffusion_state,r.etat_visibilite,r.etat_transaction,r.detail_statut_name,r.alerte_principale].filter(Boolean).map(badge).join('')}</div></div><div class="badges">${[r.responsable_affichage,r.priority,r.next_action].filter(Boolean).map(badge).join('')}</div></div><div class="kpis"><article class="kpi"><span>Prix</span><strong>${esc(r.prix||'')}</strong></article><article class="kpi"><span>Surface</span><strong>${esc(r.surface_habitable_detail||r.surface||'')}</strong></article><article class="kpi"><span>Pieces / chambres</span><strong>${esc(join([r.nb_pieces,r.nb_chambres],' / ')||'-')}</strong></article><article class="kpi"><span>Photos</span><strong>${esc(r.nb_images||0)}</strong></article></div></section><div class="crmL"><div class="stack"><section class="box"><h4>Photos</h4>${media(r,imgs)||'<div class="empty">Aucune photo</div>'}</section><section class="box"><h4>Descriptif</h4>${texts(r,txts)||'<div class="empty">Aucun descriptif</div>'}</section><section class="box"><h4>Fiche bien</h4>${cards([['Dossier',r.numero_dossier],['Mandat',r.numero_mandat],['Type de bien',r.type_bien],['Prix',r.prix],['Surface listing',r.surface],['Surface habitable',r.surface_habitable_detail],['Pieces',r.nb_pieces],['Chambres',r.nb_chambres],['Etage',r.etage_detail],['Terrasse',r.terrasse_detail],['Garage / box',r.garage_box_detail],['Surface terrain',r.surface_terrain_detail],['Copropriete',r.copropriete_detail],['Ascenseur',r.ascenseur_detail],['Adresse',r.adresse_privee_listing||r.adresse_detail],['Ville',r.ville_publique_listing||r.ville_privee_detail||r.ville],['Code postal',r.code_postal_public_listing||r.code_postal_prive_detail||r.code_postal],['Latitude',r.latitude_detail],['Longitude',r.longitude_detail],['Date enregistrement',r.date_enregistrement_annonce],['Derniere MAJ',r.date_maj],['Statut source',r.statut_annonce],['Statut detail',r.detail_statut_name],['Validation diffusion',r.validation_diffusion_state],['Visibilite',r.etat_visibilite]])}</section>${props(raw.ag_interieur)?`<section class="box"><h4>Interieur</h4>${props(raw.ag_interieur)}</section>`:''}${props(raw.ag_exterieur)?`<section class="box"><h4>Exterieur</h4>${props(raw.ag_exterieur)}</section>`:''}${props(raw.equipements)?`<section class="box"><h4>Equipements</h4>${props(raw.equipements)}</section>`:''}${props(raw.diagnostiques)?`<section class="box"><h4>Diagnostics</h4>${props(raw.diagnostiques)}</section>`:''}${props(raw.terrain)?`<section class="box"><h4>Terrain</h4>${props(raw.terrain)}</section>`:''}${props(raw.copropriete)?`<section class="box"><h4>Copropriete</h4>${props(raw.copropriete)}</section>`:''}${txn(r)?`<section class="box"><h4>Transaction</h4>${txn(r)}</section>`:''}${notes(notesA,r.note_hektor_principale)?`<section class="box"><h4>Notes et commentaires</h4>${notes(notesA,r.note_hektor_principale)}</section>`:''}</div><aside class="stack"><section class="box"><h4>Pilotage CRM</h4>${cards([['Responsable',r.responsable_affichage],['Role responsable',r.responsable_type],['Statut global',r.statut_global],['Sous-statut',r.sous_statut],['Alerte',r.alerte_principale],['Priorite',r.priority],['Action suivante',r.next_action],['Commentaire interne',r.commentaire_resume],['Blocage',r.motif_blocage],['Transaction',r.etat_transaction],['Archive',r.archive],['Diffusable',r.diffusable]])}</section><section class="box"><h4>Mandat et valorisation</h4>${cards([['Mandat numero source',r.mandat_numero_source],['Mandat type source',r.mandat_type_source],['Mandat type',r.mandat_type],['Mandat date enr.',r.mandat_date_enregistrement],['Mandat debut',r.mandat_date_debut],['Mandat fin',r.mandat_date_fin],['Mandat cloture',r.mandat_date_cloture],['Mandat montant',r.mandat_montant],['Mandants',r.mandants_texte],['Honoraires',r.honoraires_resume],['Prix public',r.prix_publique],['Prix net vendeur',r.prix_net_vendeur]])}</section>${people(owners)?`<section class="box"><h4>Proprietaires et contacts</h4>${people(owners)}</section>`:''}${mandats(mandatsA,r)?`<section class="box"><h4>Mandat</h4>${mandats(mandatsA,r)}</section>`:''}</aside></div></div>`}function row(r){const c=window.APP_DETAIL_CHUNKS[r.detail_chunk]||{},x=c[String(r.hektor_annonce_id)]||{};return Object.assign({},r,x)}function ensure(r){if(!r||!r.detail_chunk)return Promise.resolve();if(window.APP_DETAIL_CHUNKS[r.detail_chunk])return Promise.resolve();if(L[r.detail_chunk])return L[r.detail_chunk];L[r.detail_chunk]=new Promise((ok,ko)=>{const s=document.createElement('script');s.src='app_metier_detail_data/'+r.detail_chunk;s.onload=()=>ok();s.onerror=()=>ko(new Error('load'));document.head.appendChild(s)});return L[r.detail_chunk]}function stock(rows){const pages=Math.max(1,Math.ceil(rows.length/PAGE_SIZE));p=Math.min(Math.max(1,p),pages);const now=rows.slice((p-1)*PAGE_SIZE,p*PAGE_SIZE);if(!sId&&now.length)sId=now[0].hektor_annonce_id;E.count.textContent=`${rows.length} dossier${rows.length>1?'s':''}`;E.page.textContent=`Page ${p} / ${pages}`;E.rows.innerHTML=now.map(r=>{const v=txt(r.ville_publique_listing||r.ville_privee_detail||r.ville||''),cp=txt(r.code_postal_public_listing||r.code_postal_prive_detail||r.code_postal||''),a=txt(r.adresse_privee_listing||r.adresse_detail||'');return `<tr data-id="${esc(r.hektor_annonce_id)}" class="${String(r.hektor_annonce_id)===String(sId)?'sel':''}"><td><div class="mono">${esc(r.numero_dossier||'')}</div><div class="muted">${esc(r.numero_mandat||'')}</div></td><td><b>${esc(r.titre_bien||'')}</b><div class="muted">${esc(r.type_bien||'')} · ${esc(r.prix||'')}</div></td><td><div>${esc(a||v||'')}</div><div class="muted">${esc(v)}${cp?' · '+esc(cp):''}</div></td><td>${esc(r.responsable_affichage||'')}</td><td><div>${esc(r.statut_global||'')}</div><div class="muted">${esc(r.statut_annonce||'')}</div></td><td><div>${esc(r.next_action||'')}</div><div class="muted">${esc(r.date_enregistrement_annonce||'')}</div></td></tr>`}).join('');const cur=rows.find(r=>String(r.hektor_annonce_id)===String(sId))||now[0]||null;E.quick.innerHTML=quick(cur);E.rows.querySelectorAll('tr[data-id]').forEach(tr=>{tr.onclick=()=>{sId=tr.dataset.id;stock(filtered())};tr.ondblclick=()=>{const r=rows.find(x=>String(x.hektor_annonce_id)===String(tr.dataset.id));if(r)openFull(r)}})}function dash(rows){E.t.textContent=rows.length;E.a.textContent=rows.filter(r=>r.statut_global==='A valider').length;E.d.textContent=rows.filter(r=>r.statut_global==='Diffuse').length;E.v.textContent=rows.filter(r=>r.statut_global==='Vendu').length}function render(){const rows=filtered();if(screen==='dashboard')dash(rows);if(screen==='stock')stock(rows)}function openFull(r,push=true){if(!r)return;sId=r.hektor_annonce_id;E.title.textContent=`Annonce complete · ${r.numero_dossier||''}`;E.sub.textContent=`${r.ville||''} · ${r.responsable_affichage||''}`;E.full.innerHTML='<div class=\"longtext\">Chargement...</div>';setScreen('annonce');if(push)location.hash='annonce-'+encodeURIComponent(r.hektor_annonce_id);ensure(r).then(()=>{E.full.innerHTML=detail(row(r))}).catch(()=>{E.full.innerHTML='<div class=\"longtext\">Impossible de charger le detail lourd.</div>'})}fill(E.commercial,'responsable_affichage','Tous');fill(E.statut,'statut_global','Tous');fill(E.alerte,'alerte_principale','Toutes');fill(E.validation,'validation_diffusion_state','Toutes');[E.q,E.commercial,E.statut,E.alerte,E.validation].forEach(el=>el.addEventListener('input',()=>{p=1;render()}));E.prev.onclick=()=>{p--;render()};E.next.onclick=()=>{p++;render()};document.querySelectorAll('.side button[data-screen]').forEach(btn=>btn.onclick=()=>{location.hash='';setScreen(btn.dataset.screen);render()});E.open.onclick=()=>openFull(filtered().find(r=>String(r.hektor_annonce_id)===String(sId))||filtered()[0]||null);E.back.onclick=()=>{location.hash='';setScreen('stock');render()};window.addEventListener('hashchange',()=>{if(location.hash.startsWith('#annonce-')){const id=decodeURIComponent(location.hash.slice(9));openFull(DATA.find(r=>String(r.hektor_annonce_id)===String(id)),false)}else if(location.hash===''){setScreen('stock');render()}});setScreen('dashboard');render();
"""


def html(rows_data):
    data_json = json.dumps(rows_data, ensure_ascii=False).replace("</script>", "<\\/script>")
    return (
        HTML.replace("__DATA__", data_json)
        .replace("__TOTAL__", str(len(rows_data)))
        .replace("__PAGE_SIZE__", str(PAGE_SIZE))
        .replace("__SCRIPT__", SCRIPT.replace("__PAGE_SIZE__", str(PAGE_SIZE)).replace("</script>", "<\\/script>"))
    )


def main():
    all_rows = rows()
    light, chunks = split_rows(all_rows)
    OUT.write_text(html(light), encoding="utf-8")
    write_chunks(chunks)
    OUT_JS.write_text("// legacy file not used; details are now chunked in app_metier_detail_data/\n", encoding="utf-8")
    print(f"Exported: {OUT}")
    print(f"Exported: {OUT_JS}")
    print(f"Exported detail chunks: {len(chunks)} in {DETAIL_DIR}")
    print(f"Rows: {len(all_rows)}")


if __name__ == "__main__":
    main()
