// ============================================================================
// Avis de valeur — design "maquette V2" (cartes, palette par chapitre).
// MODULE ISOLÉ / ADDITIF : n'est PAS encore branché sur la génération prod.
// La fonction prod actuelle (estimationAvisValeurHtmlPremium) reste intacte.
// Objectif : porter ce design sur le worker sans casser les données ni les
// fonctions (carte + estimMapWithPins, QR conseiller, DVF/INSEE/cadastre…).
// Le rendu se fait via le même renderHtmlToPdfBuffer({ preferCSSPageSize:true }).
//
// Contenu : ESTIM_CSS_V2 = CSS complète validée sur la maquette (avis_v2.html),
// incluant palette par chapitre (var --acc posée par section, inline de préf.),
// blocs commentaire "citation", diagnostics, pins de commodités, etc.
// ============================================================================

const ESTIM_CSS_V2 = `
:root{
  --ink:#211f1c; --body:#4a453e; --muted:#8c847a; --brand:#c5005f; --brand-deep:#8a0043;
  --line:#e8e1d6; --soft:#f8f4ec; --card:#fffdfa; --gold:#a8842c;
  --dpeA:#2a9d3f;--dpeB:#57b03a;--dpeC:#a0cf3a;--dpeD:#f5d800;--dpeE:#f3a712;--dpeF:#ec6c1f;--dpeG:#d7191c;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:'Inter',sans-serif;color:var(--body);font-size:11px;line-height:1.55;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.serif{font-family:'Spectral',Georgia,serif}
h1,h2,h3{margin:0;color:var(--ink);font-weight:600}
.tnum{font-variant-numeric:tabular-nums}
@page{size:A4;margin:0}
.doc{}
.sheet{page-break-after:always;padding:16mm 14mm 14mm}
.sheet:last-child{page-break-after:auto}
.flow > *{break-inside:avoid}
.card{break-inside:avoid}
.rh{display:flex;align-items:center;justify-content:space-between;border-bottom:1.5px solid var(--ink);padding-bottom:8px;margin-bottom:16px}
.rh .brand{font-family:'Spectral',serif;font-weight:700;font-size:14px;letter-spacing:.02em;color:var(--ink)}
.rh .brand b{color:var(--brand)}
.rh .meta{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;text-align:right}
.rf{display:flex;align-items:center;justify-content:space-between;border-top:1px solid var(--line);margin-top:16px;padding-top:7px;font-size:8.5px;color:var(--muted)}
.kicker{display:inline-flex;align-items:center;gap:7px;font-size:9px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--brand)}
.kicker i{width:16px;height:1.5px;background:var(--brand);display:inline-block}
.h{font-family:'Spectral',serif;font-size:19px;font-weight:600;color:var(--ink);margin:6px 0 3px;letter-spacing:-.01em}
.h.mt{margin-top:22px}
.sub{font-size:10px;color:var(--muted);margin:0 0 12px}
.section-ico{width:34px;height:34px;border-radius:9px;background:color-mix(in srgb,var(--brand) 9%,#fff);display:inline-flex;align-items:center;justify-content:center;color:var(--brand)}
.section-ico svg{width:19px;height:19px}
.sec-lead{display:flex;align-items:center;gap:11px;margin-bottom:14px}
.sec-lead .txt .h{margin:0}
.sec-lead .txt .sub{margin:2px 0 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:11px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:11px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:11px}
.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:14px 16px}
.card-lead{display:flex;align-items:center;gap:10px;margin-bottom:11px}
.card-ico{width:30px;height:30px;border-radius:8px;background:color-mix(in srgb,var(--brand) 8%,#fff);display:flex;align-items:center;justify-content:center;color:var(--brand);flex:none}
.card-ico svg{width:17px;height:17px}
.card-t{font-size:12px;font-weight:600;color:var(--ink)}
.card-s{font-size:9px;color:var(--muted)}
.card-badge{margin-left:auto;font-size:9px;color:var(--brand);background:color-mix(in srgb,var(--brand) 8%,#fff);border:1px solid color-mix(in srgb,var(--brand) 20%,#fff);border-radius:20px;padding:2px 9px;white-space:nowrap}
.card-badge.warn{color:#9a3412;background:#fdf1e7;border-color:#f6d5b8}
.kv{display:grid;grid-template-columns:repeat(2,1fr);gap:9px 18px}
.kv.k4{grid-template-columns:repeat(4,1fr)}
.kv .k{font-size:8.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.kv .v{font-size:12.5px;font-weight:600;color:var(--ink)}
.kv .v.big{font-size:15px;color:var(--brand)}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px}
.tag{font-size:9.5px;color:var(--body);background:var(--soft);border-radius:6px;padding:3px 9px}
.note{font-size:9px;color:var(--muted);margin:9px 0 0;line-height:1.5}
.alert{display:flex;gap:8px;align-items:flex-start;font-size:10px;color:#9a3412;background:#fdf1e7;border:1px solid #f6d5b8;border-radius:9px;padding:9px 11px;margin-top:11px;line-height:1.45}
.alert svg{width:15px;height:15px;flex:none;margin-top:1px;stroke:#9a3412}
.cover{height:297mm;padding:0;display:flex;flex-direction:column;page-break-after:always;position:relative}
.cover-top{background:var(--ink);color:#fff;padding:14mm 14mm 12mm;display:flex;align-items:flex-start;justify-content:space-between}
.cover-top .brand{font-family:'Spectral',serif;font-size:19px;font-weight:700}
.cover-top .brand b{color:#ff5aa1}
.cover-top .ref{text-align:right;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#cfc8c0}
.cover-top .ref b{display:block;font-size:15px;color:#fff;letter-spacing:0;text-transform:none;margin-top:3px}
.cover-hero{flex:1;position:relative;background:linear-gradient(135deg,#2a2723,#413b34);display:flex;align-items:flex-end}
.cover-hero .photo{position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,17,14,.05),rgba(20,17,14,.72))}
.cover-caption{position:relative;padding:0 14mm 13mm;color:#fff;width:100%}
.cover-caption .kick{display:inline-flex;align-items:center;gap:7px;font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:#ffb3d4;margin-bottom:9px}
.cover-caption .kick svg{width:14px;height:14px;stroke:#ffb3d4}
.cover-caption .title{font-family:'Spectral',serif;font-size:46px;font-weight:600;line-height:1;letter-spacing:-.02em}
.cover-caption .bien{font-family:'Spectral',serif;font-size:21px;font-weight:500;margin-top:10px;color:#f3ede6}
.cover-caption .loc{font-size:11px;color:#d8d1c8;margin-top:5px;display:flex;align-items:center;gap:6px}
.cover-caption .loc svg{width:14px;height:14px;stroke:#ffb3d4}
.cover-caption .chips{display:flex;gap:7px;margin-top:14px;flex-wrap:wrap}
.cover-caption .chips span{font-size:9.5px;border:1px solid rgba(255,255,255,.32);border-radius:20px;padding:3px 11px;color:#f0eae2}
.cover-foot{background:#fff;padding:11mm 14mm;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.cover-foot .cf .l{font-size:8.5px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}
.cover-foot .cf .v{font-size:12.5px;font-weight:600;color:var(--ink);margin-top:3px}
.cover-foot .seal{grid-column:1/-1;display:flex;align-items:center;gap:9px;border-top:1px solid var(--line);padding-top:11px;margin-top:2px;color:var(--gold);font-size:10px}
.cover-foot .seal svg{width:20px;height:20px;stroke:var(--gold)}
.value-hero{background:linear-gradient(135deg,#fff,var(--soft));border:1px solid var(--line);border-radius:16px;padding:20px 22px;display:grid;grid-template-columns:1.1fr 1fr;gap:20px;align-items:center}
.value-hero .vlabel{font-size:9px;text-transform:uppercase;letter-spacing:.14em;color:var(--muted)}
.value-hero .vmain{font-family:'Spectral',serif;font-size:44px;font-weight:600;color:var(--brand);line-height:1;letter-spacing:-.02em;margin-top:5px}
.value-hero .vsub{font-size:10.5px;color:var(--body);margin-top:6px}
.gauge{margin-top:4px}
.gauge .bar{height:7px;border-radius:5px;background:linear-gradient(90deg,#e9c9d8,var(--brand),#7a0038);position:relative}
.gauge .pin{position:absolute;top:-4px;left:52%;width:15px;height:15px;border-radius:50%;background:#fff;border:3px solid var(--brand)}
.gauge .ends{display:flex;justify-content:space-between;margin-top:7px}
.gauge .ends .e{text-align:center}
.gauge .ends .e .k{font-size:8px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.gauge .ends .e .v{font-family:'Spectral',serif;font-size:14px;font-weight:600;color:var(--ink)}
.gauge .ends .e.mid .v{color:var(--brand)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin-top:14px}
.kpi{border:1px solid var(--line);border-radius:12px;padding:13px 14px;background:var(--card)}
.kpi .k{font-size:8.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.kpi .v{font-family:'Spectral',serif;font-size:22px;font-weight:600;color:var(--ink);margin-top:3px;line-height:1}
.kpi .v.brand{color:var(--brand)}
.kpi .s{font-size:8.5px;color:var(--muted);margin-top:3px}
.energy{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:6px}
.rg .rgh{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:6px}
.rg-row{display:flex;align-items:center;gap:6px;margin-bottom:3px}
.rg-bar{color:#fff;font-weight:700;font-size:10px;padding:2px 8px;border-radius:3px;min-width:26px;text-align:center}
.rg-cur{font-size:11px;font-weight:700}
.stats3{display:grid;grid-template-columns:repeat(3,1fr);gap:11px;margin-top:6px}
.scard{border:1px solid var(--line);border-radius:12px;padding:13px 14px;background:var(--card);display:flex;flex-direction:column;gap:3px}
.scard .ic{width:26px;height:26px;border-radius:7px;background:var(--soft);display:flex;align-items:center;justify-content:center;color:var(--brand);margin-bottom:4px}
.scard .ic svg{width:15px;height:15px}
.scard .v{font-family:'Spectral',serif;font-size:20px;font-weight:600;color:var(--ink);line-height:1}
.scard .v small{font-size:11px;color:var(--muted);font-family:'Inter'}
.scard .l{font-size:9px;color:var(--muted)}
.chart{border:1px solid var(--line);border-radius:12px;padding:14px 16px 10px;margin-top:12px;background:var(--card)}
.chart-h{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px}
.chart-h .t{font-size:11px;font-weight:600;color:var(--ink)}
.chart-h .s{font-size:9px;color:var(--muted)}
.bars{display:flex;align-items:flex-end;gap:14px;height:70px}
.bcol{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:5px}
.bcol .bv{font-size:9px;font-weight:600;color:var(--ink)}
.bar-el{width:100%;max-width:40px;background:linear-gradient(180deg,#e9aac6,var(--brand));border-radius:5px 5px 0 0}
.bcol .bk{font-size:9px;color:var(--muted)}
.comp-head{display:grid;grid-template-columns:2.4fr 1fr .8fr 1fr 1fr .7fr;gap:8px;font-size:8px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:0 12px 7px;border-bottom:1.5px solid var(--ink)}
.comp-row{display:grid;grid-template-columns:2.4fr 1fr .8fr 1fr 1fr .7fr;gap:8px;align-items:center;padding:9px 12px;border-bottom:1px solid var(--line);break-inside:avoid}
.comp-row:nth-child(even){background:var(--soft)}
.comp-row .b{font-size:10.5px;font-weight:600;color:var(--ink)}
.comp-row .m{font-size:8.5px;color:var(--muted)}
.comp-row .cell{font-size:10px}
.comp-row .num{text-align:right;font-weight:600;color:var(--ink)}
.comp-row .pm{text-align:right;color:var(--brand);font-weight:600}
.comp-idx{display:inline-flex;width:16px;height:16px;border-radius:50%;background:var(--ink);color:#fff;font-size:8px;font-weight:700;align-items:center;justify-content:center;margin-right:6px}
.acq-hero{background:linear-gradient(135deg,#1f1c19,#3a332c);color:#fff;border-radius:16px;padding:20px 22px;display:flex;align-items:center;gap:20px}
.acq-hero .big{font-family:'Spectral',serif;font-size:50px;font-weight:600;line-height:1;color:#ff6fae}
.acq-hero .big small{display:block;font-size:11px;color:#d8d1c8;font-family:'Inter';font-weight:400;letter-spacing:.03em;margin-top:4px}
.acq-hero .txt{flex:1}
.acq-hero .txt .t{font-family:'Spectral',serif;font-size:17px;font-weight:600}
.acq-hero .txt .d{font-size:10.5px;color:#e7e0d8;margin-top:5px;line-height:1.5}
.acq-list{display:grid;grid-template-columns:repeat(3,1fr);gap:11px;margin-top:12px}
.acq-card{border:1px solid var(--line);border-radius:12px;padding:12px 13px;background:var(--card)}
.acq-card .who{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.acq-card .av{width:26px;height:26px;border-radius:50%;background:color-mix(in srgb,var(--brand) 12%,#fff);color:var(--brand-deep);font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center}
.acq-card .score{font-size:9px;font-weight:700;color:#0f6e56;background:#eef8f3;border:1px solid #bfe3d5;border-radius:20px;padding:2px 8px}
.acq-card .bud{font-family:'Spectral',serif;font-size:14px;font-weight:600;color:var(--ink)}
.acq-card .cri{font-size:9px;color:var(--muted);margin-top:3px}
.method{display:flex;gap:11px;background:var(--soft);border-radius:12px;padding:13px 15px;margin-top:14px}
.method svg{width:20px;height:20px;stroke:var(--brand);flex:none}
.method .t{font-size:11px;font-weight:600;color:var(--ink)}
.method .d{font-size:9.5px;color:var(--body);line-height:1.55;margin-top:3px}
.pts{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin-top:12px}
.pts .col{border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.pts .ph{display:flex;align-items:center;gap:7px;font-size:10.5px;font-weight:600;margin-bottom:7px}
.pts .ph svg{width:15px;height:15px}
.pts.forts .ph{color:#0f6e56}
.pts .vigi .ph{color:#9a3412}
.pts ul{margin:0;padding:0;list-style:none}
.pts li{font-size:10px;color:var(--body);padding:3px 0 3px 16px;position:relative}
.pts li::before{content:'';position:absolute;left:0;top:8px;width:5px;height:5px;border-radius:50%;background:var(--brand)}
.disc{font-size:8.5px;color:var(--muted);line-height:1.5;border-top:1px solid var(--line);padding-top:9px;margin-top:16px}
.stars svg{width:15px;height:15px;fill:var(--gold)}.stars svg.off{fill:#e2dccf}
.gallery{display:grid;grid-template-columns:2fr 1fr 1fr;grid-auto-rows:30mm;gap:6px;margin-bottom:15px;break-inside:avoid}
.gallery img{width:100%;height:100%;object-fit:cover;border-radius:9px;display:block}
.gallery .big{grid-row:1/3;border-radius:11px}
.mapfig{position:relative;border-radius:13px;overflow:hidden;border:1px solid var(--line);height:64mm;margin-bottom:13px;break-inside:avoid}
.mapfig img{width:100%;height:100%;object-fit:cover;display:block}
.mapfig .pin,.cadmap .pin{position:absolute;left:50%;top:50%;transform:translate(-50%,-100%);color:var(--brand)}
.mapfig .pin svg{width:28px;height:28px;filter:drop-shadow(0 2px 3px rgba(0,0,0,.45))}
.mapfig .cap,.cadmap .cap{position:absolute;left:10px;bottom:9px;background:rgba(255,255,255,.92);border-radius:6px;padding:3px 9px;font-size:8.5px;color:var(--body)}
.cadmap{position:relative;border-radius:11px;overflow:hidden;border:1px solid var(--line);height:56mm;margin-bottom:12px;break-inside:avoid}
.cadmap img{width:100%;height:100%;object-fit:cover;display:block}
.cadmap .pin svg{width:24px;height:24px;filter:drop-shadow(0 2px 3px rgba(0,0,0,.45))}
.postes{margin-top:4px}
.pst{margin-bottom:9px}
.pst-top{display:flex;justify-content:space-between;font-size:10px;margin-bottom:3px}
.pst-top .n{color:var(--body)}.pst-top .v{font-weight:600}
.pst-bar{height:6px;border-radius:4px;background:#ece3d4;overflow:hidden}
.pst-fill{height:100%;border-radius:4px}
.est-support{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}
.est-support .m{border:1px solid var(--line);border-radius:11px;padding:11px 13px;text-align:center;background:var(--card)}
.est-support .m .k{font-size:8px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
.est-support .m .v{font-family:'Spectral',serif;font-size:17px;font-weight:600;color:var(--ink);margin-top:3px}
.est-note{font-size:9px;color:var(--muted);text-align:center;margin-top:7px}
/* Repasse design : fonds, profondeur, motifs */
.doc{counter-reset:sheet}
.sheet{background:#faf9f5;position:relative;counter-increment:sheet}
.sheet::before{content:'';position:absolute;top:0;left:0;right:0;height:40mm;background:radial-gradient(120% 100% at 85% 0%,rgba(197,0,95,.05),transparent 60%);pointer-events:none;z-index:0}
.sheet::after{content:counter(sheet,decimal-leading-zero);position:absolute;top:9mm;right:13mm;font-family:'Spectral',serif;font-size:44px;font-weight:700;color:rgba(197,0,95,.07);line-height:1;pointer-events:none;z-index:0}
.rh,.flow{position:relative;z-index:1}
.rh{border-bottom:none;padding-bottom:11px}
.rh::after{content:'';position:absolute;left:0;bottom:0;width:44px;height:2px;background:var(--brand)}
.rh::before{content:'';position:absolute;left:0;bottom:0;right:0;height:1px;background:var(--line)}
.card{background:#fff;box-shadow:0 1px 2px rgba(40,25,15,.04),0 10px 22px -16px rgba(40,25,15,.16)}
.card-ico,.section-ico,.scard .ic{background:linear-gradient(135deg,color-mix(in srgb,var(--brand) 15%,#fff),color-mix(in srgb,var(--brand) 4%,#fff));box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--brand) 13%,transparent)}
.kpi,.scard,.est-support .m{background:#fff;box-shadow:0 1px 2px rgba(40,25,15,.04),0 8px 18px -15px rgba(40,25,15,.14)}
.value-hero{background:linear-gradient(120deg,#fff 0%,#fdf2f7 58%,#f9e7ef 100%);box-shadow:0 3px 26px -14px rgba(197,0,95,.34);position:relative;overflow:hidden;border-color:color-mix(in srgb,var(--brand) 16%,#fff)}
.value-hero::before{content:'';position:absolute;top:-46px;right:-46px;width:170px;height:170px;border-radius:50%;background:radial-gradient(circle,rgba(197,0,95,.1),transparent 70%)}
.value-hero::after{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,var(--brand),var(--gold))}
.gallery img,.mapfig,.cadmap{box-shadow:0 2px 12px -6px rgba(40,25,15,.34)}
.mapfig::after,.cadmap::after{content:'';position:absolute;inset:7px;border:1px solid rgba(255,255,255,.6);border-radius:8px;pointer-events:none}
.rf{border-top:none;padding-top:9px;position:relative}
.rf::before{content:'';position:absolute;left:0;top:0;right:0;height:1px;background:linear-gradient(90deg,var(--brand),transparent 42%)}
.acq-hero{background:linear-gradient(125deg,#1c1916,#3a2f2a 68%,#4a2a3a);box-shadow:0 6px 30px -14px rgba(28,20,16,.6);position:relative;overflow:hidden}
.acq-hero::before{content:'';position:absolute;top:-30px;right:-20px;width:150px;height:150px;border-radius:50%;background:radial-gradient(circle,rgba(255,90,161,.16),transparent 68%)}
.acq-card{box-shadow:0 8px 18px -15px rgba(40,25,15,.16)}
.cover-top{border-bottom:2px solid var(--gold)}
.cover-hero::after{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px);background-size:100% 7px;opacity:.6;pointer-events:none}
.cover-foot{border-top:3px solid var(--brand)}
.cover-caption .title{text-shadow:0 2px 20px rgba(0,0,0,.35)}
.section-ico svg,.card-ico svg,.scard .ic svg,.method svg,.kicker svg{stroke:currentColor;stroke-linecap:round;stroke-linejoin:round}
.section-ico svg [fill]:not([fill="none"]),.card-ico svg{fill:none}
.cover-logo{height:30mm;width:auto;display:block}
.rh .brand-img{display:flex;align-items:center;gap:8px}
.rh .brand-img img{height:14mm;width:auto;display:block}
.rh .brand-img span{display:none}
.cover-hero{flex:none;height:95mm;background:none}
.cover-hero::after{opacity:.3}
.cover-caption{flex:1;width:auto;padding:12mm 14mm;background:#fff;color:var(--ink);display:flex;flex-direction:column;justify-content:center}
.cover-caption .kick,.cover-caption .kick svg,.cover-caption .loc svg{color:var(--brand);stroke:var(--brand)}
.cover-caption .title{color:var(--ink);text-shadow:none}
.cover-caption .bien{color:var(--ink)}
.cover-caption .loc{color:var(--body)}
.cover-caption .chips span{border-color:var(--line);color:var(--body)}
/* Bloc conseiller "version en ligne" (contact-fuse) */
.contact-fuse{border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-top:12px;background:#fff;display:flex;align-items:stretch;box-shadow:0 8px 18px -15px rgba(40,25,15,.16)}
.cf-body{padding:16px 20px;flex:1;min-width:0}
.cf-nego{display:flex;align-items:center;gap:13px;padding-bottom:13px;border-bottom:1px solid var(--line)}
.cf-qr{flex:none;width:150px;border-left:1px solid var(--line);background:var(--soft);padding:14px 12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;text-align:center}
.cf-qr .qr-box{width:112px;height:112px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:7px;display:grid;place-items:center}
.cf-qr .qr-box svg{width:100%;height:100%;display:block}
.cf-qr .qr-cap{font-size:9px;font-weight:800;color:var(--brand);letter-spacing:.4px;text-transform:uppercase;line-height:1.3}
.cf-qr .qr-sub{font-size:8px;color:var(--muted);line-height:1.35}
.cf-nego .av{width:50px;height:50px;border-radius:50%;flex:none;background:linear-gradient(150deg,var(--brand),var(--brand-deep));display:grid;place-items:center;color:#fff;font-family:'Spectral',serif;font-size:19px;font-weight:600}
.cf-role{font-size:8.5px;font-weight:800;color:var(--brand);letter-spacing:1.3px;text-transform:uppercase}
.cf-nm{font-family:'Spectral',serif;font-size:18px;font-weight:600;margin-top:2px;color:var(--ink)}
.cf-contact{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:6px}.cf-contact span{display:inline-flex;align-items:center;gap:6px;font-size:11px;color:var(--body);font-weight:500}.cf-contact svg{width:12px;height:12px;color:var(--brand);stroke:var(--brand)}
.cf-agence-lbl{font-size:8.5px;font-weight:800;color:var(--brand);letter-spacing:1.3px;text-transform:uppercase;margin-top:14px}
.cf-agence{display:flex;align-items:center;gap:14px;margin-top:9px}
.cf-agence-photo{flex:none;width:72px;height:58px;border-radius:9px;background:var(--soft);border:1px dashed #d8cfc8;display:grid;place-items:center;color:var(--brand);overflow:hidden}
.cf-agence-photo svg{width:30px;height:30px;opacity:.7;stroke:var(--brand)}
.cf-agence .cf-rows{margin-top:0;flex:1;min-width:0}
.cf-rows{margin-top:9px;display:flex;flex-direction:column;gap:8px}.cf-row{display:flex;align-items:center;gap:10px;font-size:11px;color:var(--body)}
.cf-row b{color:var(--ink)}
.cf-row .i{width:24px;height:24px;flex:none;border-radius:7px;background:var(--soft);display:grid;place-items:center;color:var(--brand)}.cf-row .i svg{width:12px;height:12px;stroke:var(--brand)}
/* Cohérence pied/fond + pied ancré en bas de page */
.sheet{display:flex;flex-direction:column;min-height:297mm}
.rf{margin-top:auto}
.rf span:last-child{font-size:0}
.rf span:last-child::after{content:counter(sheet,decimal-leading-zero);font-size:8.5px;color:var(--muted);letter-spacing:0}
/* Palette secondaire (vert=conforme, ambre=attention, bleu=info technique) */
:root{--green:#1f8a5b;--green-bg:#e9f6ef;--green-bd:#bfe3d2;--blue:#245ea6;--blue-bg:#eaf1fb;--blue-bd:#c9dbf1;--amber:#a86a12;--amber-bg:#fbf0dd;--amber-bd:#eed9af}
.diags{display:flex;flex-direction:column}
.drow{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 1px;border-bottom:1px solid var(--line);font-size:11px}
.drow:last-child{border-bottom:none}
.drow .dk{color:var(--body)}
.dv{font-size:9px;font-weight:700;padding:3px 10px;border-radius:20px;white-space:nowrap;letter-spacing:.01em}
.dv.ok{color:var(--green);background:var(--green-bg);border:1px solid var(--green-bd)}
.dv.na{color:var(--muted);background:var(--soft);border:1px solid var(--line)}
.dv.warn{color:var(--amber);background:var(--amber-bg);border:1px solid var(--amber-bd)}
.grid3 .scard:nth-child(1) .ic{color:var(--blue);background:var(--blue-bg);box-shadow:inset 0 0 0 1px var(--blue-bd)}
.grid3 .scard:nth-child(2) .ic{color:var(--amber);background:var(--amber-bg);box-shadow:inset 0 0 0 1px var(--amber-bd)}
.grid3 .scard:nth-child(3) .ic{color:var(--green);background:var(--green-bg);box-shadow:inset 0 0 0 1px var(--green-bd)}
.tag.risk{color:var(--amber);background:var(--amber-bg);border:1px solid var(--amber-bd);font-weight:600}
.kpi .v.pos{color:var(--green)}
.card-ico.tech{color:var(--blue) !important;background:var(--blue-bg) !important;box-shadow:inset 0 0 0 1px var(--blue-bd) !important}
/* Palette par chapitre : --acc posé en inline style sur chaque <section class="sheet" style="--acc:#xxxxxx"> (robuste aux pages conditionnelles) */
.sheet{--acc:var(--brand)}
.sheet .section-ico{color:var(--acc);background:linear-gradient(135deg,color-mix(in srgb,var(--acc) 15%,#fff),color-mix(in srgb,var(--acc) 4%,#fff));box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--acc) 16%,transparent)}
.sheet .section-ico svg{stroke:var(--acc)}
.sheet::after{color:color-mix(in srgb,var(--acc) 12%,transparent)}
.sheet .rh::after{background:var(--acc)}
.sheet .rf::before{background:linear-gradient(90deg,var(--acc),transparent 42%)}
.sheet .card-ico,.sheet .scard .ic{color:var(--acc);background:linear-gradient(135deg,color-mix(in srgb,var(--acc) 14%,#fff),#fff);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--acc) 14%,transparent)}
.sheet .card-ico svg,.sheet .scard .ic svg{stroke:var(--acc)}
.sheet .kicker{color:var(--acc)}.sheet .kicker i{background:var(--acc)}
.sheet .bar-el{background:linear-gradient(180deg,color-mix(in srgb,var(--acc) 42%,#fff),var(--acc))}
.sheet .card-badge{color:var(--acc);background:color-mix(in srgb,var(--acc) 8%,#fff);border-color:color-mix(in srgb,var(--acc) 22%,#fff)}
.value-hero .vmain{color:var(--brand)}
/* Blocs commentaire = citation identifiable (label + guillemet filigrané) */
.comment{position:relative;background:linear-gradient(180deg,#fff,var(--soft));border:1px solid var(--line);border-left:2px solid var(--acc);border-radius:14px;padding:32px 26px 19px;box-shadow:0 5px 24px -14px rgba(40,25,15,.24);overflow:hidden;font-family:'Spectral',serif;font-style:italic;font-size:12.5px;color:#3a352f;line-height:1.72}
.comment::before{content:'—  Le mot de votre conseiller';position:absolute;left:26px;top:15px;white-space:nowrap;font-family:'Inter',sans-serif;font-style:normal;font-weight:700;font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:var(--acc)}
.comment::after{content:'\\201D';position:absolute;right:20px;top:0;font-family:Georgia,serif;font-style:normal;font-weight:700;font-size:64px;color:var(--acc);opacity:.13;line-height:1;pointer-events:none}
.comment.empty{font-style:normal;font-family:'Inter',sans-serif;color:var(--muted)}
.comment.empty::before,.comment.empty::after{content:none}
/* Localisation de TOUTES les commodités sur la carte (écoles, commerces, santé, gare…) */
.mapfig .mp{position:absolute;transform:translate(-50%,-50%);width:15px;height:15px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.45);z-index:2}
.mapfig .mp.ecole{background:#245ea6}
.mapfig .mp.commerce{background:#a8842c}
.mapfig .mp.sante{background:#1f8a5b}
.mapfig .mp.transport{background:#7a4fa3}
.map-legend{display:flex;gap:15px;flex-wrap:wrap;margin-top:9px;font-size:9px;color:var(--body)}
.map-legend span{display:inline-flex;align-items:center;gap:6px}
.map-legend i{width:10px;height:10px;border-radius:50%;border:1.5px solid #fff;box-shadow:0 0 0 1px var(--line)}
.map-legend i.home{background:var(--brand)}.map-legend i.ecole{background:#245ea6}.map-legend i.commerce{background:#a8842c}.map-legend i.sante{background:#1f8a5b}.map-legend i.transport{background:#7a4fa3}
`;

// Couleur d'accent par chapitre (posée en inline style sur chaque section — robuste
// aux pages conditionnelles, contrairement à nth-of-type).
const ESTIM_V2_ACCENTS = {
  bien: "#0f6e6e", composition: "#3a5a8c", etat: "#2e7d5b", cadre: "#2f7cb8",
  urbanisme: "#a8842c", marche: "#c5005f", comparables: "#0f6e6e",
  estimation: "#c5005f", conseiller: "#8a3d6b",
};

// ---- Icônes ----
const V2_ICO = {
  bien: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M3 21h18M5 21V8l7-5 7 5v13M9 21v-6h6v6"/></svg>',
  compo: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="5" rx="1"/><rect x="13" y="11" width="8" height="10" rx="1"/><rect x="3" y="14" width="8" height="7" rx="1"/></svg>',
  etat: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M12 3 5 6v5c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6z"/><path d="m9 11 2 2 4-4"/></svg>',
  cadre: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M20 10c0 7-8 12-8 12s-8-5-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>',
  cadastre: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14"/></svg>',
  marche: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M4 19V5M4 14l4-4 3 3 5-6M17 7h4v4"/></svg>',
  comps: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/></svg>',
  estim: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><circle cx="12" cy="9" r="6"/><path d="m8.5 14-1.5 7 5-3 5 3-1.5-7"/></svg>',
  acq: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><circle cx="9" cy="8" r="3.2"/><path d="M3.5 20a5.5 5.5 0 0 1 11 0M16 6.5a3 3 0 0 1 0 5.8M15.5 20a5.5 5.5 0 0 0-2-4.3"/></svg>',
  phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 4h4l2 5-3 2a11 11 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>',
  mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
  home2: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21V8l9-5 9 5v13"/></svg>',
  homePin: '<svg viewBox="0 0 24 24" fill="#c5005f" stroke="#fff" stroke-width="1.5"><path d="M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7z"/><circle cx="12" cy="9" r="2.6" fill="#fff"/></svg>',
};

// Génère le HTML "maquette V2" à partir d'un modèle m (toutes les vars déjà extraites côté worker).
function buildV2Html(m) {
  const T = m._t, E = m._e, ESC = m._esc || ((s) => String(s == null ? "" : s));
  const acc = (k) => ESTIM_V2_ACCENTS[k] || "#c5005f";
  const rh = (label) => `<div class="rh"><span class="brand-img"><img src="${m.mark || ""}" alt="GTI"></span><div class="meta">${label}<br>N° ${m.docNumber}</div></div>`;
  const rf = () => `<div class="rf"><span>Groupe GTI — Avis de valeur indicatif</span><span>x</span></div>`;
  const secLead = (ico, title, sub) => `<div class="sec-lead"><span class="section-ico">${V2_ICO[ico] || ""}</span><div class="txt"><div class="h serif">${title}</div><div class="sub">${sub}</div></div></div>`;
  const sheet = (k, label, inner) => `<section class="sheet" style="--acc:${acc(k)}">${rh(label)}<div class="flow">${inner}</div>${rf()}</section>`;
  const kv = (pairs, cls) => `<div class="kv${cls ? " " + cls : ""}">${pairs.filter(Boolean).map(([k, v]) => `<div><div class="k">${k}</div><div class="v">${v}</div></div>`).join("")}</div>`;
  const cardLead = (title, sub, badge, ico) => `<div class="card-lead"><span class="card-ico">${ico || V2_ICO.compo}</span><div><div class="card-t">${title}</div>${sub ? `<div class="card-s">${sub}</div>` : ""}</div>${badge || ""}</div>`;

  // ---- Couverture ----
  const heroBg = m.photos && m.photos[0]
    ? `background:linear-gradient(180deg,rgba(20,17,14,.05),rgba(20,17,14,.5)),url('${T(m.photos[0])}') center/cover`
    : `background:linear-gradient(135deg,#2a2723,#413b34)`;
  const cover = `<section class="cover">
    <div class="cover-top"><img class="cover-logo" src="${m.logoCover || ""}" alt="Groupe GTI"><div class="ref">Dossier confidentiel<b>N° ${m.docNumber}</b></div></div>
    <div class="cover-hero"><div class="photo" style="${heroBg}"></div></div>
    <div class="cover-caption">
      <div class="kick"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M12 3l8 4v5c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V7z"/></svg>Estimation immobilière · établie par un professionnel</div>
      <div class="title serif">Avis de valeur</div>
      <div class="bien serif">${m.titre}</div>
      <div class="loc">${V2_ICO.cadre}${T(m.localite || "—")}</div>
      <div class="chips">${m.tags || '<span>Caractéristiques à compléter</span>'}${m.dpeEff ? `<span>DPE ${m.dpeEff}</span>` : ""}</div>
    </div>
    <div class="cover-foot">
      <div class="cf"><div class="l">Établi pour</div><div class="v">${m.proprio}</div></div>
      <div class="cf"><div class="l">Votre conseiller</div><div class="v">${m.negoNom}</div></div>
      <div class="cf"><div class="l">Date · validité</div><div class="v">${m.dateLong} · ${T(m.validite)}</div></div>
      <div class="seal"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M12 3l8 4v5c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V7z"/><path d="m9 12 2 2 4-4"/></svg>Analyse fondée sur les ventes réelles (DVF), les bases officielles du bâtiment et notre fichier acquéreurs.</div>
    </div></section>`;

  // ---- 1. Le bien & le bâtiment ----
  const gallery = m.photos && m.photos.length ? `<div class="gallery">${[0,1,2,3,4].map((i)=>m.photos[i]?`<img${i===0?' class="big"':''} src="${T(m.photos[i])}" alt="">`:`<div${i===0?' class="big"':''} style="background:var(--soft);border-radius:9px"></div>`).join("")}</div>` : "";
  const bienCard = `<div class="card">${cardLead("Caractéristiques", "Déclaré au mandat", "", V2_ICO.bien)}${kv([
    ["Type", T(m.type || "—")], ["Surface", m.surface ? m.surface + " m²" : "—"],
    ["Pièces", T(m.pieces || "—")], ["Chambres", T(m.chambres || "—")],
    ["Étage", T((m.detail && m.detail.etage) || "—")], ["Copropriété", T((m.detail && m.detail.copropriete) || "—")],
  ])}</div>`;
  const bdnbCard = m.bdnb ? `<div class="card">${cardLead("Données bâtiment", "BDNB · CSTB", m.bdnb.rnb_id ? `<span class="card-badge">RNB ${T(m.bdnb.rnb_id)}</span>` : "", V2_ICO.cadastre)}${kv([
    m.bdnb.annee_construction != null ? ["Construction", T(m.bdnb.annee_construction)] : null,
    m.bdnb.type_batiment ? ["Type bâti", T(m.bdnb.type_batiment)] : null,
    (m.bdnb.mat_mur || m.bdnb.mat_toit) ? ["Murs · toit", T([m.bdnb.mat_mur, m.bdnb.mat_toit].filter(Boolean).join(" · "))] : null,
    m.bdnb.nb_logements != null ? ["Niveaux · logts", T([m.bdnb.nb_niveau, m.bdnb.nb_logements != null ? m.bdnb.nb_logements + " logts" : null].filter(Boolean).join(" · "))] : null,
    m.bdnb.classe_dpe ? ["DPE théorique", T(m.bdnb.classe_dpe)] : null,
    m.bdnb.alea_argile ? ["Aléa argile", T(m.bdnb.alea_argile)] : null,
  ])}</div>` : `<div class="card">${cardLead("Bâtiment", "Base officielle", "", V2_ICO.cadastre)}<p class="note">Données bâtiment (BDNB) à charger.</p></div>`;
  const dpeCard = `<div class="card">${cardLead("DPE réel · ADEME", m.dpeReal && m.dpeReal.date ? "Diagnostic du " + m.dateCourt(m.dpeReal.date) : "Performance énergétique", m.dpeReal && m.dpeReal.matched_by === "adresse" ? '<span class="card-badge">Adresse exacte</span>' : "", V2_ICO.marche)}<div class="energy">${regletteV2("dpe", m.dpeEff)}${regletteV2("ges", m.gesEff)}</div>${m.dpeReal ? `<p class="note">DPE enregistré à l'ADEME${m.dpeReal.surface ? " · " + T(m.dpeReal.surface) + " m²" : ""} — à titre indicatif.</p>` : ""}</div>`;
  const chargesCard = `<div class="card">${cardLead("Charges annuelles", "Déclaratif propriétaire", "", V2_ICO.estim)}<div class="diags">${["Taxe foncière","Énergie","Eau","Assurance"].map((lbl,i)=>{const keys=["taxeFonciere","energie","eau","assurance"];const v=E((m.charges||{})[keys[i]]);return `<div class="drow"><span class="dk">${lbl}</span><span class="dv ${v?"ok":"na"}">${v?v+"/an":"à compléter"}</span></div>`;}).join("")}</div></div>`;
  const p1 = sheet("bien", "Le bien · caractéristiques", secLead("bien","Le bien &amp; le bâtiment","Caractéristiques déclarées, complétées par les bases officielles du bâti.") + gallery + `<div class="grid2">${bienCard}${bdnbCard}</div>` + `<div class="h mt">Performance énergétique</div><div class="grid2">${dpeCard}${chargesCard}</div>`);

  // ---- 2. Composition & détail ----
  const D = m.detail || {};
  const oui = (v, s) => v === "Oui" ? (s ? "Oui · " + s + " m²" : "Oui") : null;
  const interieurKv = [
    D.sdb != null && D.sdb !== "" ? ["Salles de bain", T(D.sdb)] : null, D.se != null && D.se !== "" ? ["Salles d'eau", T(D.se)] : null,
    D.wc != null && D.wc !== "" ? ["WC", T(D.wc)] : null, D.surfSejour ? ["Séjour", D.surfSejour + " m²"] : null,
    D.surfCarrez ? ["Carrez", D.surfCarrez + " m²"] : null, D.cuisine ? ["Cuisine", T(D.cuisine)] : null,
    D.exposition ? ["Exposition", T(D.exposition)] : null, D.vue ? ["Vue", T(D.vue)] : null,
  ].filter(Boolean);
  const exterieurKv = [
    oui(D.jardin, D.surfJardin) ? ["Jardin", oui(D.jardin, D.surfJardin)] : null,
    oui(D.terrasse, D.surfTerrasse) ? ["Terrasse", oui(D.terrasse, D.surfTerrasse)] : null,
    oui(D.cave, D.surfCave) ? ["Cave", oui(D.cave, D.surfCave)] : null,
    (D.garage || D.surfGarage) ? ["Garage", D.surfGarage ? D.surfGarage + " m²" : T(D.garage)] : null,
    (D.parkInt || D.parkExt) ? ["Parking", [D.parkInt ? D.parkInt + " int." : null, D.parkExt ? D.parkExt + " ext." : null].filter(Boolean).join(" · ")] : null,
    D.niveaux ? ["Niveaux", T(D.niveaux)] : null,
    (D.chauffageType || D.chauffageEnergie) ? ["Chauffage", T([D.chauffageType, D.chauffageEnergie].filter(Boolean).join(" · "))] : null,
    D.assainissement ? ["Assainissement", T(D.assainissement)] : null,
  ].filter(Boolean);
  const hasDet = interieurKv.length || exterieurKv.length || m.equipList || D.particularites;
  const detCards = hasDet ? `<div class="grid2">
    ${interieurKv.length ? `<div class="card">${cardLead("Intérieur", "Pièces &amp; aménagement", "", V2_ICO.compo)}${kv(interieurKv)}</div>` : ""}
    ${exterieurKv.length ? `<div class="card">${cardLead("Extérieur &amp; confort", "Annexes, chauffage, réseaux", "", V2_ICO.bien)}${kv(exterieurKv)}</div>` : ""}
  </div>${m.equipList ? `<div class="h mt">Équipements &amp; sécurité</div><div class="tags">${m.equipList.replace(/<span class="eqp">[\s\S]*?<\/svg>/g, '<span class="tag">')}</div>` : ""}` : `<p class="note">Caractéristiques détaillées non renseignées dans la fiche du bien.</p>`;
  const descBlock = m.descriptif ? `<div class="h mt">Descriptif du bien</div><p class="note" style="font-size:10.5px;color:var(--body);line-height:1.6">${ESC(m.descriptif)}</p>` : "";
  const partBlock = D.particularites ? `<div class="h mt">Particularités</div><p class="note" style="font-size:10.5px;color:var(--body);line-height:1.6">${ESC(D.particularites)}</p>` : "";
  const p2 = sheet("composition", "Composition &amp; détail", secLead("compo","Composition &amp; détail du bien","Aménagement intérieur / extérieur, confort et équipements.") + detCards + descBlock + partBlock);

  // ---- 3. État & appréciation + diagnostics ----
  const noteCard = `<div class="card">${cardLead("Note d'état","Appréciation globale", m.etatLabel?`<span class="card-badge">${T(m.etatLabel)}</span>`:"", V2_ICO.etat)}<div class="stars">${m.stars||""}</div>${m.postesBlock ? `<div class="postes" style="margin-top:10px">${(m.postes||[]).map((p)=>posteRowV2(p)).join("")}</div>` : ""}</div>`;
  const ptsCard = `<div class="card">${cardLead("Points clés","Forts &amp; vigilance","",V2_ICO.etat)}<div class="pts" style="grid-template-columns:1fr;margin-top:2px">
    <div class="col" style="border:none;padding:0"><div class="ph" style="color:#0f6e56">${chk()}Points forts</div><ul>${liList(m.forts)}</ul></div>
    <div class="col vigi" style="border:none;padding:0;margin-top:8px"><div class="ph" style="color:#9a3412">${warn()}Points de vigilance</div><ul>${liList(m.vigi)}</ul></div>
  </div></div>`;
  const commentEtat = m.etatComment ? `<div class="h mt">Commentaire de votre conseiller · état du bien</div><div class="comment">${ESC(m.etatComment)}</div>` : "";
  const diagAll = [{ k: "DPE · classe énergie", v: m.dpeEff ? T(m.dpeEff) + " · réalisé" : "", ok: !!m.dpeEff }, { k: "GES · émissions", v: m.gesEff ? T(m.gesEff) : "", ok: !!m.gesEff }];
  const DIAG_LABELS = { amiante: "Amiante", plomb: "Plomb (CREP)", electricite: "Électricité", gaz: "Gaz", termites: "Termites", erp: "ERP · état des risques" };
  Object.entries((m.detail && m.detail.diagnostics) || {}).forEach(([key, val]) => {
    if (key === "DPE" || key === "GES") return;
    let v = "", ok = false;
    if (val && typeof val === "object") { v = val.done ? "Réalisé" + (val.date ? " · " + m.dateCourt(val.date) : "") : "Non communiqué"; ok = !!val.done; }
    else if (val) { v = T(val); ok = /conform|absence|réalis|realis|néant|neant/i.test(String(val)); }
    if (v) diagAll.push({ k: DIAG_LABELS[key] || key, v, ok });
  });
  const diagHalf = Math.ceil(diagAll.length / 2);
  const diagCard = (title, sub, ico, items) => `<div class="card">${cardLead(title, sub, "", ico)}<div class="diags">${items.map((dr) => `<div class="drow"><span class="dk">${dr.k}</span><span class="dv ${dr.ok ? "ok" : "na"}">${dr.v || "—"}</span></div>`).join("")}</div></div>`;
  const diagBlock = diagAll.length ? `<div class="h mt">Diagnostics obligatoires</div><div class="grid2">${diagCard("Performance &amp; santé", "DPE, amiante, plomb", V2_ICO.etat, diagAll.slice(0, diagHalf))}${diagCard("Sécurité &amp; contrôles", "Électricité, gaz, ERP", V2_ICO.estim, diagAll.slice(diagHalf))}</div>` : "";
  const p3 = sheet("etat", "État &amp; appréciation", secLead("etat","État général &amp; appréciation","Évaluation poste par poste, points clés et diagnostics.") + `<div class="grid2">${noteCard}${ptsCard}</div>` + commentEtat + diagBlock);

  // ---- 4. Cadre de vie ----
  const mapfig = m.cdv && m.cdv.mapUrl ? `<div class="mapfig"><img src="${T(m.cdv.mapUrl)}" alt="Localisation"><span class="pin">${V2_ICO.homePin}</span>${m.mapPins || ""}<span class="cap">Fond Plan IGN v2 · commodités géolocalisées</span></div>
    <div class="map-legend"><span><i class="home"></i>Le bien</span><span><i class="ecole"></i>Écoles</span><span><i class="commerce"></i>Commerces</span><span><i class="sante"></i>Santé · hôpital</span><span><i class="transport"></i>Gare &amp; transports</span></div>` : "";
  const com = m.cdvCom || {};
  const comStats = `<div class="grid3">
    <div class="scard"><span class="ic">${V2_ICO.bien}</span><div class="v">${com.ecoles != null ? com.ecoles : "—"}</div><div class="l">Écoles &lt; 1,5 km</div></div>
    <div class="scard"><span class="ic">${V2_ICO.estim}</span><div class="v">${com.commerces != null ? com.commerces : "—"}</div><div class="l">Commerces &lt; 1 km</div></div>
    <div class="scard"><span class="ic">${V2_ICO.etat}</span><div class="v">${com.sante != null ? com.sante : "—"}</div><div class="l">Santé (pharmacie, médecin)</div></div>
  </div>`;
  const poles = (m.cdv && Array.isArray(m.cdv.poles)) ? m.cdv.poles : [];
  const accessCard = `<div class="card">${cardLead("Accès &amp; mobilité","Pôles et grands axes","",V2_ICO.cadre)}${kv([
    (com.gareNom || com.gareKm != null) ? ["Gare", `${T(com.gareNom || "")}${com.gareKm != null ? " · " + com.gareKm + " km" : ""}`] : null,
    poles[0] ? [T(poles[0].nom), poles[0].km + " km"] : null,
    poles[1] ? [T(poles[1].nom), poles[1].km + " km"] : null,
    (m.inseeProfil && m.inseeProfil.population) ? ["Population", Number(m.inseeProfil.population).toLocaleString("fr-FR") + " hab."] : null,
  ])}</div>`;
  const risks = (m.cdvRisk && Array.isArray(m.cdvRisk.risques)) ? m.cdvRisk.risques : [];
  const riskCard = `<div class="card">${cardLead("Risques recensés","Géorisques","",V2_ICO.etat)}<div class="tags">${risks.length ? risks.map((r)=>`<span class="tag risk">${T(r)}</span>`).join("") : '<span class="tag">Non communiqué</span>'}</div><p class="note">Information préventive — sans valeur d'état des risques réglementaire (ERP).</p></div>`;
  const p4 = sheet("cadre", "Cadre de vie · localisation", secLead("cadre",`Cadre de vie &amp; environnement`,`${m.cdv && m.cdv.commune ? T(m.cdv.commune) + " — " : ""}commodités, accessibilité et risques.`) + mapfig + comStats + `<div class="grid2" style="margin-top:11px">${accessCard}${riskCard}</div>`);

  // ---- 5. Urbanisme, cadastre & patrimoine ----
  const cadmap = m.cadMapUrl ? `<div class="cadmap"><img src="${T(m.cadMapUrl)}" alt="Plan cadastral"><span class="pin">${V2_ICO.homePin}</span><span class="cap">Fond Plan IGN v2 · parcellaire PCI Express</span></div>` : "";
  const cadP0 = (m.cadParcelles && m.cadParcelles[0]) || {};
  const cadCard = `<div class="card">${cardLead("Éléments cadastraux","IGN · Géoportail","",V2_ICO.cadastre)}${kv([
    ["Parcelle", T(cadP0.reference || (m.cadParcelles && m.cadParcelles.length ? m.cadParcelles.length + " parcelles" : "—"))],
    ["Contenance", (m.cad && m.cad.contenance_totale) ? Number(m.cad.contenance_totale).toLocaleString("fr-FR") + " m²" : "—"],
    ["Zone PLU", T((m.cadPlu && m.cadPlu.zone) || "—")],
    ["Libellé", T((m.cadPlu && m.cadPlu.libelle) || "—")],
  ])}</div>`;
  const patriItems = (m.patri && Array.isArray(m.patri.items)) ? m.patri.items.slice(0, 4) : [];
  const patriCard = `<div class="card">${cardLead("Patrimoine &amp; ABF","Géoportail de l'urbanisme", m.patri && m.patri.abf ? '<span class="card-badge warn">Périmètre ABF</span>' : "", V2_ICO.cadastre)}${m.patri && m.patri.abf ? `<div class="alert"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg><span>Bien en périmètre de protection — les travaux extérieurs sont soumis à l'avis de l'Architecte des Bâtiments de France.</span></div>` : ""}<div class="tags">${patriItems.length ? patriItems.map((it)=>`<span class="tag">${T(it.type_label || "—")}${it.nom ? " · " + T(it.nom) : ""}</span>`).join("") : '<span class="tag">Aucune servitude recensée</span>'}</div></div>`;
  const reseauxCard = `<div class="card">${cardLead("Desserte &amp; réseaux","Viabilisation","",V2_ICO.bien)}${kv([
    ["Eau potable", "Réseau public"], ["Assainissement", T((m.detail && m.detail.assainissement) || "—")],
    ["Électricité", "Raccordé"], ["Fibre optique", "Éligible"],
  ])}</div>`;
  const p5 = (m.cad || m.patri) ? sheet("urbanisme", `Urbanisme &amp; patrimoine`, secLead("cadastre",`Urbanisme, cadastre &amp; patrimoine`,`Parcellaire IGN, zonage PLU et servitudes de protection.`) + cadmap + `<div class="grid2">${cadCard}${patriCard}</div>` + `<div class="grid2" style="margin-top:11px">${reseauxCard}<div class="card">${cardLead("Zone " + T((m.cadPlu && m.cadPlu.zone) || "PLU"),"Règles indicatives","",V2_ICO.cadastre)}${kv([["Destination","Selon zonage"],["Implantation","Selon règlement"],["Hauteur","Selon règlement"],["Stationnement","Selon règlement"]])}<p class="note">Synthèse indicative — se référer au règlement du PLU/PLUi en vigueur.</p></div></div>`) : "";

  // ---- 6. Marché & profil du secteur ----
  const barsMax = (m.mEvo && m.mEvo.length) ? Math.max(...m.mEvo.map((e) => e.prix_m2 || 0)) : 0;
  const evoChart = (m.mEvo && m.mEvo.length) ? `<div class="chart"><div class="chart-h"><div class="t">Évolution du prix au m² · secteur</div><div class="s">${m.mEvo[0].annee} → ${m.mEvo[m.mEvo.length-1].annee}</div></div><div class="bars" style="height:56px">${m.mEvo.map((e)=>`<div class="bcol"><div class="bv">${E(e.prix_m2)||"—"}</div><div class="bar-el" style="height:${barsMax?Math.round((e.prix_m2/barsMax)*42)+6:6}px"></div><div class="bk">${T(e.annee)}</div></div>`).join("")}</div></div>` : "";
  const marketStats = `<div class="stats3">
    <div class="scard"><span class="ic">${V2_ICO.marche}</span><div class="v">${m.mMed ? E(m.mMed) + '<small> €/m²</small>' : "—"}</div><div class="l">Prix médian · ${T(m.marche ? m.marche.type : "secteur")}</div></div>
    <div class="scard"><span class="ic">${V2_ICO.marche}</span><div class="v">${m.mTrend != null ? (m.mTrend >= 0 ? "+" : "") + m.mTrend + " %" : "—"}</div><div class="l">Évolution prix/m²</div></div>
    <div class="scard"><span class="ic">${V2_ICO.comps}</span><div class="v">${m.mCount != null ? m.mCount : "—"}</div><div class="l">Comparables${m.mRadius != null ? " · " + m.mRadius + " km" : ""}</div></div>
  </div>`;
  const locatifKpis = m.loyer ? `<div class="h mt">Potentiel locatif</div><div class="kpis">
    <div class="kpi"><div class="k">Loyer estimé</div><div class="v">${m.loyerMensuel != null ? E(m.loyerMensuel) + '<small style="font-size:11px"> €/mois</small>' : "—"}</div><div class="s">${m.loyerM2 != null ? m.loyerM2 + " €/m²" : ""}</div></div>
    <div class="kpi"><div class="k">Rendement brut</div><div class="v pos">${m.loyerRdt != null ? m.loyerRdt + " %" : "—"}</div><div class="s">loyer annuel / prix</div></div>
    <div class="kpi"><div class="k">Zone ABC</div><div class="v">${T(m.loyer.zone_abc || "—")}</div><div class="s">${m.loyer.zone_abc ? (m.loyerTendue ? "tendue" : "détendue") : ""}</div></div>
    <div class="kpi"><div class="k">Loyer annuel</div><div class="v">${m.loyerMensuel != null ? E(m.loyerMensuel * 12) : "—"}</div><div class="s">avant charges</div></div>
  </div>` : "";
  const prof = m.inseeProfil || null;
  const popSeries = prof && prof.pop_series ? Object.entries(prof.pop_series).map(([y, v]) => [parseInt(y, 10), Number(v)]).filter(([y, v]) => y && v).sort((a, b) => a[0] - b[0]) : [];
  const popMax = popSeries.length ? Math.max(...popSeries.map((s) => s[1])) : 0;
  const popBadge = prof && prof.pop_tendance ? `<span class="card-badge warn">${T(prof.pop_tendance)}${prof.pop_evolution != null ? ` · ${prof.pop_evolution > 0 ? "+" : ""}${prof.pop_evolution}% / 15 ans` : ""}</span>` : "";
  const popBars = popSeries.length >= 2 ? `<div class="bars" style="height:84px;align-items:flex-end;margin-top:10px">${popSeries.map(([y, v]) => `<div class="bcol" style="justify-content:flex-end"><div class="bv">${Number(v).toLocaleString("fr-FR")}</div><div class="bar-el" style="height:${popMax ? Math.round((v / popMax) * 42) + 6 : 6}px"></div><div class="bk">${y}</div></div>`).join("")}</div><div class="note">${prof.population ? Number(prof.population).toLocaleString("fr-FR") + " habitants" : ""}${prof.population_annee ? " (" + prof.population_annee + ")" : ""}</div>` : (prof && prof.population ? `<div class="kv" style="margin-top:6px"><div><div class="k">Population</div><div class="v big">${Number(prof.population).toLocaleString("fr-FR")}</div></div></div>` : '<p class="note">Série population à charger.</p>');
  const revItems = prof ? [
    prof.revenu_median ? { l: T(prof.commune || "Commune"), v: prof.revenu_median, hl: true } : null,
    prof.dept_revenu_median ? { l: "Département (médiane)", v: prof.dept_revenu_median } : null,
    prof.france_revenu_median ? { l: "France", v: prof.france_revenu_median } : null,
  ].filter(Boolean) : [];
  const revMax = revItems.length ? Math.max(...revItems.map((r) => r.v)) : 1;
  const revBars = revItems.length ? `<div class="postes" style="margin-top:6px">${revItems.map((r) => `<div class="pst"><div class="pst-top"><span class="n">${r.l}</span><span class="v"${r.hl ? ' style="color:var(--brand)"' : ""}>${Number(r.v).toLocaleString("fr-FR")} €</span></div><div class="pst-bar"><div class="pst-fill" style="width:${Math.round(r.v / revMax * 100)}%;background:${r.hl ? "var(--brand)" : "#c9c2bc"}"></div></div></div>`).join("")}</div><div class="note">Niveau de vie médian annuel — INSEE FiLoSoFi.</div>` : '<p class="note">Revenu médian à charger.</p>';
  const inseeBlock = prof && (popSeries.length || revItems.length) ? `<div class="h mt">Profil de la commune${m.cdv && m.cdv.commune ? " · " + T(m.cdv.commune) : ""}</div><div class="grid2"><div class="card">${cardLead("Population", "Recensements INSEE", popBadge, V2_ICO.acq)}${popBars}</div><div class="card">${cardLead("Revenu des ménages", "Niveau de vie médian · FiLoSoFi", "", V2_ICO.estim)}${revBars}</div></div>` : "";
  const p6 = sheet("marche", "Marché &amp; secteur", secLead("marche",`Indicateurs de marché${m.marche && m.marche.commune ? " · " + T(m.marche.commune) : ""}`,`Ventes réelles DVF (open data) — un repère objectif, non un prix.`) + marketStats + evoChart + locatifKpis + inseeBlock + `<p class="disc"><b>Source.</b> DVF (open data)${m.marche ? ` · prix médian sur ${m.mCount} ventes, rayon ${m.mRadius} km` : ""} · INSEE. Valeurs à titre indicatif.</p>`);

  // ---- 7. Comparables DVF ----
  const p7 = (m.mCompsList && m.mCompsList.length) ? sheet("comparables", "Comparables DVF", secLead("comps",`${m.mCompsList.length} ventes comparables retenues`,`Transactions réelles ayant servi de base au prix au m² et à la fourchette.`) + `<div class="comp-head"><span>Bien</span><span>Commune</span><span>Date</span><span style="text-align:right">Surface</span><span style="text-align:right">Prix</span><span style="text-align:right">€/m²</span></div>${m.mCompsList.map((c,i)=>`<div class="comp-row"><div><span class="comp-idx">${i+1}</span><span class="b">${T(c.type||"Bien")} ${c.surface?c.surface+" m²":""}${c.pieces?" · "+T(c.pieces)+" p.":""}</span></div><div class="cell">${T(c.commune||"—")}</div><div class="cell m">${T(m.dateCourt(c.date)||"—")}</div><div class="num">${c.surface?c.surface+" m²":"—"}</div><div class="num">${E(c.valeur)||"—"}</div><div class="pm">${c.prix_m2?E(c.prix_m2):"—"}</div></div>`).join("")}${(m.mP25||m.mP75)?`<div class="h mt">Synthèse au m² · secteur</div><div class="est-support"><div class="m"><div class="k">Fourchette basse</div><div class="v">${E(m.mP25)||"—"} €/m²</div></div><div class="m"><div class="k">Médiane retenue</div><div class="v" style="color:var(--brand)">${E(m.mMed)||"—"} €/m²</div></div><div class="m"><div class="k">Fourchette haute</div><div class="v">${E(m.mP75)||"—"} €/m²</div></div></div>`:""}<p class="disc"><b>Source.</b> DVF (open data publique) — ${m.mCount || m.mCompsList.length} ventes analysées, ${m.mCompsList.length} listées.</p>`) : "";

  // ---- 8. Notre estimation (conclusion) ----
  const gaugePin = (m.valBasse && m.valHaute) ? 52 : 52;
  const p8 = sheet("estimation", "Notre estimation", `<div class="kicker"><i></i>Conclusion</div><div class="h serif">La valeur que nous vous conseillons</div><p class="sub">Déterminée par votre conseiller au regard de l'ensemble du dossier. Les indicateurs de marché l'éclairent — ils ne la fixent pas.</p>
    <div class="value-hero card"><div><div class="vlabel">Valeur conseillée</div><div class="vmain serif">${m.valEstimee}</div><div class="vsub">${m.pricePerM2}</div></div><div class="gauge"><div class="bar"><div class="pin" style="left:${gaugePin}%"></div></div><div class="ends"><div class="e"><div class="v serif">${m.valBasse}</div><div class="k">Bas</div></div><div class="e mid"><div class="v serif">${m.valEstimee}</div><div class="k">Conseillé</div></div><div class="e"><div class="v serif">${m.valHaute}</div><div class="k">Haut</div></div></div></div></div>
    <div class="est-support">
      <div class="m"><div class="k">Prix médian DVF</div><div class="v">${m.mMed ? E(m.mMed) + " €/m²" : "—"}</div></div>
      <div class="m"><div class="k">Tendance ${m.marche && m.marche.months ? Math.round(m.marche.months / 12) + " ans" : "secteur"}</div><div class="v">${m.mTrend != null ? (m.mTrend >= 0 ? "+" : "") + m.mTrend + " %" : "—"}</div></div>
      <div class="m"><div class="k">Rendement brut</div><div class="v">${m.loyerRdt != null ? m.loyerRdt + " %" : "—"}</div></div>
    </div>
    <div class="est-note">Indicateurs ayant éclairé l'estimation — la valeur retenue intègre l'état, l'emplacement, la performance énergétique et la demande.</div>
    ${m.argPrix ? `<div class="h mt">Commentaire de votre conseiller · sur la valeur retenue</div><div class="comment">${ESC(m.argPrix)}</div>` : ""}
    ${m.appreciation ? `<div class="h mt">Appréciation générale</div><div class="comment">${ESC(m.appreciation)}</div>` : ""}
    <div class="method"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg><div><div class="t">Notre méthode</div><div class="d">${ESC(m.methode)}</div></div></div>
    <p class="disc"><b>Avis de valeur indicatif.</b> Le présent document constitue une estimation de la valeur vénale du bien. Il ne constitue ni une expertise au sens réglementaire, ni un engagement sur un prix de vente.</p>`);

  // ---- 9. Acquéreurs & conseiller ----
  const acqHero = `<div class="acq-hero"><div class="big">${m.acquereursN > 0 ? m.acquereursN : "✓"}<small>acquéreurs qualifiés</small></div><div class="txt"><div class="t">${m.acquereursN > 0 ? "Une demande réelle, dès la mise en vente." : "Un réseau d'acquéreurs prêts à visiter."}</div><div class="d">${m.acquereursN > 0 ? `${m.acquereursN} acquéreur${m.acquereursN>1?"s":""} de notre fichier recherche${m.acquereursN>1?"nt":""} activement un bien correspondant au vôtre, au prix conseillé de <b style="color:#fff">${m.valEstimee}</b>. Dès la mise en vente, ils sont contactés en priorité.` : `Dès la signature du mandat, votre bien est présenté à notre fichier d'acquéreurs qualifiés et diffusé sur les grands portails — au prix conseillé de <b style="color:#fff">${m.valEstimee}</b>.`}</div></div></div>`;
  const contactFuse = `<div class="h mt">Votre conseiller</div><div class="contact-fuse"><div class="cf-body">
    <div class="cf-nego"><div class="av">${m.initials}</div><div><div class="cf-role">Votre conseiller</div><div class="cf-nm">${m.negoNom}</div><div class="cf-contact">${m.tel?`<span>${V2_ICO.phone}${T(m.tel)}</span>`:""}${m.email?`<span>${V2_ICO.mail}${T(m.email)}</span>`:""}</div></div></div>
    <div class="cf-agence-lbl">Agence</div><div class="cf-agence"><div class="cf-agence-photo">${m.agencePhoto?`<img src="${T(m.agencePhoto)}" alt="">`:V2_ICO.home2}</div><div class="cf-rows"><div class="cf-row"><span class="i">${V2_ICO.home2}</span><b>${m.agence}</b></div>${m.agenceTel?`<div class="cf-row"><span class="i">${V2_ICO.phone}</span>${T(m.agenceTel)}</div>`:""}${m.agenceMail?`<div class="cf-row"><span class="i">${V2_ICO.mail}</span>${T(m.agenceMail)}</div>`:""}</div></div>
  </div>${m.qrSvg?`<aside class="cf-qr"><div class="qr-box">${m.qrSvg}</div><div class="qr-cap">Ajoutez-moi à vos contacts</div><div class="qr-sub">Scannez avec l'appareil photo</div></aside>`:""}</div>`;
  const p9 = sheet("conseiller", "Acquéreurs &amp; conseiller", secLead("acq","Vos acquéreurs vous attendent déjà","Fichier qualifié Groupe GTI — rapprochement automatique bien × recherches.") + acqHero + (m.avis?`<div class="h mt">L'avis de votre conseiller</div><div class="comment">${ESC(m.avis)}</div>`:"") + contactFuse + `<div class="disc">GROUPE GTI, SAS — RCS Saint-Étienne 502 811 144 — CPI 42022019 000 043 878.</div>`);

  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Avis de valeur ${m.docNumber}</title>
<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,500;0,600;0,700;1,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>${ESTIM_CSS_V2}</style></head><body><div class="doc">
${cover}${p1}${p2}${p3}${p4}${p5}${p6}${p7}${p8}${p9}
</div></body></html>`;
}

// Réglette DPE/GES (7 crans, style maquette)
function regletteV2(kind, cls) {
  const cols = { A: "#2a9d3f", B: "#57b03a", C: "#a0cf3a", D: "#f5d800", E: "#f3a712", F: "#ec6c1f", G: "#d7191c" };
  const letters = ["A", "B", "C", "D", "E", "F", "G"];
  const rows = letters.map((l, i) => `<div class="rg-row">${cls === l ? `<span class="rg-cur" style="color:${cols[l]}">◀</span>` : ""}<span class="rg-bar" style="background:${cols[l]};width:${34 + i * 9}px">${l}</span></div>`).join("");
  return `<div class="rg"><div class="rgh">${kind === "dpe" ? "DPE · énergie" : "GES · émissions"}</div>${cls && cols[cls] ? rows : `<div class="note">${kind.toUpperCase()} à compléter</div>`}</div>`;
}
// Convertit les "diag-row" (worker) en "drow" (maquette)
function dtRows(html) { return String(html || "").replace(/<div class="diag-row"><span class="k">([\s\S]*?)<\/span><span class="v[^"]*">([\s\S]*?)<\/span><\/div>/g, '<div class="drow"><span class="dk">$1</span><span class="dv na" style="color:var(--ink);background:none;border:none;font-weight:600">$2</span></div>'); }
function diagRowsV2(html) { return String(html || "").replace(/<div class="diag-row"><span class="k">([\s\S]*?)<\/span><span class="v ([^"]*)">([\s\S]*?)<\/span><\/div>/g, (mm, k, cls, v) => `<div class="drow"><span class="dk">${k}</span><span class="dv ${cls.includes("ok") ? "ok" : "na"}">${v}</span></div>`); }
function posteRowV2(p) {
  const NIV = { neuf: { c: "#1f8a5b", f: 100, t: "Neuf / Refait" }, bon: { c: "#46a35a", f: 84, t: "Bon état" }, correct: { c: "#e0a800", f: 55, t: "Correct" }, aprevoir: { c: "#e0662a", f: 30, t: "À prévoir" } };
  const n = NIV[p.niveau] || NIV.correct;
  return `<div class="pst"><div class="pst-top"><span class="n">${String(p.poste || "")}</span><span class="v" style="color:${n.c}">${(p.label && String(p.label).trim()) || n.t}</span></div><div class="pst-bar"><div class="pst-fill" style="width:${n.f}%;background:${n.c}"></div></div></div>`;
}
function chk() { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5 10 17 19 7"/></svg>'; }
function warn() { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>'; }
function liList(arr) { return (Array.isArray(arr) && arr.length) ? arr.map((t) => `<li>${String(t)}</li>`).join("") : '<li>À compléter par votre conseiller</li>'; }

module.exports = { ESTIM_CSS_V2, ESTIM_V2_ACCENTS, buildV2Html };
