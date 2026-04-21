
const DATA=JSON.parse(document.getElementById('data-json').textContent);
const PAGE_SIZE=120;
window.APP_DETAIL_CHUNKS=window.APP_DETAIL_CHUNKS||{};
const loaders={};
let screen='dashboard', currentPage=1, selectedId=null;
const $=id=>document.getElementById(id);
const els={q:$('q'),commercial:$('commercial'),statut:$('statut'),alerte:$('alerte'),validation:$('validation'),rows:$('rows-stock'),count:$('stock-count'),page:$('page-stock'),prev:$('prev-stock'),next:$('next-stock'),quick:$('detail-body'),full:$('full-detail-body'),title:$('full-detail-title'),sub:$('full-detail-subtitle'),open:$('open-full-detail'),back:$('back-to-stock'),t:$('stat-total'),a:$('stat-a-valider'),d:$('stat-diffuses'),v:$('stat-vendus')};
function fixText(v){
  const s=String(v??'');
  if(!(s.includes('?')||s.includes('?')||s.includes('?'))) return s;
  try{
    return decodeURIComponent(escape(s));
  }catch{
    return s
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('? ').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('??').join('?')
      .split('???').join("'")
      .split('???').join('"')
      .split('???').join('"')
      .split('???').join('"')
      .split('???').join('-')
      .split('???').join('-');
  }
}
const esc=v=>fixText(v).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const txt=v=>fixText(v).trim();
const ok=v=>txt(v)!=='';
const br=v=>esc(v).replace(/\n/g,'<br>');
const j=v=>{try{return v?JSON.parse(v):null}catch{return null}};
const join=(arr,sep=' - ')=>(arr||[]).map(txt).filter(Boolean).join(sep);
const TYPE_LABELS={
  '1':'Maison',
  '2':'Appartement',
  '3':'Parking / Garage',
  '4':'Bureau',
  '5':'Terrain',
  '6':'Local',
  '7':'Immeuble',
  '8':'Divers',
  '9':'Programme neuf',
  '10':'Loft / Atelier',
  '11':'Boutique',
  '12':'Appartement meublé',
  '13':'Maison meublée',
  '14':'Garage',
  '15':'Parking',
  '16':'Local professionnel',
  '17':'Chalet',
  '18':'Bâtiment',
  '19':'Demeure',
  '20':'Propriété',
  '21':'Mas',
  '22':'Hôtel particulier',
  '23':'Commerce',
  '24':'Immeuble',
  '25':'Villa',
  '26':'Studio',
  '27':'Duplex',
  '28':'Triplex',
  '29':'Atelier',
  '30':'Ferme'
};
function typeLabel(v){const key=txt(v);return TYPE_LABELS[key]||key||'';}
function hasMandate(r){
  return [
    r&&r.numero_mandat,
    r&&r.mandat_numero_source,
    r&&r.mandat_type_source,
    r&&r.mandat_date_enregistrement,
    r&&r.mandat_montant,
    r&&r.mandants_texte
  ].some(ok);
}
function displayGlobalStatus(r){
  if(txt(r&&r.statut_global)==='Sans mandat' && hasMandate(r)) return 'Mandat detecte';
  return txt(r&&r.statut_global);
}
function displaySubStatus(r){
  if(txt(r&&r.statut_global)==='Sans mandat' && hasMandate(r)){
    return join(['Mandat', r.mandat_numero_source||r.numero_mandat], ' - ');
  }
  return txt(r&&r.sous_statut);
}
function displayTitle(r){
  const title=txt(r&&r.titre_bien);
  if(title)return title;
  const textTitle=txt(r&&r.texte_principal_titre);
  if(textTitle)return textTitle;
  const composed=join([typeLabel(r&&r.type_bien),r&&(r.ville_publique_listing||r.ville_privee_detail||r.ville)]);
  if(composed)return composed;
  return txt(r&&r.numero_dossier)||'Annonce sans titre';
}
function setScreen(name){screen=name;document.querySelectorAll('.side button[data-screen]').forEach(b=>b.classList.toggle('on',b.dataset.screen===name));document.querySelectorAll('.screen').forEach(s=>s.classList.remove('on'));const node=$('screen-'+name);if(node)node.classList.add('on');}
function uniq(key){return [...new Set(DATA.map(r=>r[key]).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),'fr'));}
function fill(sel,key,label){sel.innerHTML=`<option value="">${label}</option>`+uniq(key).map(v=>`<option>${esc(v)}</option>`).join('');}
function filtered(){const q=txt(els.q.value).toLowerCase();return DATA.filter(r=>{if(els.commercial.value&&r.responsable_affichage!==els.commercial.value)return false;if(els.statut.value&&r.statut_global!==els.statut.value)return false;if(els.alerte.value&&r.alerte_principale!==els.alerte.value)return false;if(els.validation.value&&r.validation_diffusion_state!==els.validation.value)return false;if(!q)return true;return [r.numero_dossier,r.numero_mandat,r.titre_bien,r.ville,r.code_postal,r.type_bien,r.responsable_affichage,r.next_action,r.commentaire_resume,r.adresse_privee_listing,r.adresse_detail].join(' ').toLowerCase().includes(q);});}
function quickCard(label,val){return `<div class="card"><small>${label}</small>${val?esc(val):'<span class="muted">Absent</span>'}</div>`;}
function quickView(r){if(!r)return '<div class="muted">Aucun dossier selectionne</div>';const adr=txt(r.adresse_privee_listing||r.adresse_detail||'');const ville=txt(r.ville_publique_listing||r.ville_privee_detail||r.ville||'');const cp=txt(r.code_postal_public_listing||r.code_postal_prive_detail||r.code_postal||'');return `<h4>${esc(displayTitle(r))}</h4><div class="muted">${esc(ville)}${cp?' - '+esc(cp):''} - ${esc(r.responsable_affichage||'')}</div><div class="section-title">Resume</div><div class="cards">${quickCard('Dossier',r.numero_dossier)+quickCard('Mandat',r.mandat_numero_source||r.numero_mandat)+quickCard('Type',typeLabel(r.type_bien))+quickCard('Prix',r.prix)+quickCard('Surface',r.surface||r.surface_habitable_detail)+quickCard('Adresse',adr)+quickCard('Statut',displayGlobalStatus(r))+quickCard('Action',r.next_action)}</div>`;}
function listingPhoto(r){
  const preview=(j(r.images_preview_json)||[]).find(i=>i&&(i.url||i.full||i.path));
  const src=txt((preview&&(preview.url||preview.full||preview.path))||r.photo_url_listing||'');
  if(!src)return '';
  const alt=esc(displayTitle(r)||'Image annonce');
  return `<img class="stock-thumb" loading="lazy" src="${esc(src)}" alt="${alt}">`;
}
function renderDashboard(rows){els.t.textContent=rows.length;els.a.textContent=rows.filter(r=>r.statut_global==='A valider').length;els.d.textContent=rows.filter(r=>r.statut_global==='Diffuse').length;els.v.textContent=rows.filter(r=>r.statut_global==='Vendu').length;}
function renderStock(rows){const totalPages=Math.max(1,Math.ceil(rows.length/PAGE_SIZE));currentPage=Math.min(Math.max(1,currentPage),totalPages);const pageRows=rows.slice((currentPage-1)*PAGE_SIZE,currentPage*PAGE_SIZE);if((!selectedId||!rows.some(r=>String(r.hektor_annonce_id)===String(selectedId)))&&pageRows.length)selectedId=pageRows[0].hektor_annonce_id;els.count.textContent=`${rows.length} dossier${rows.length>1?'s':''}`;els.page.textContent=`Page ${currentPage} / ${totalPages}`;els.rows.innerHTML=pageRows.map(r=>{const ville=txt(r.ville_publique_listing||r.ville_privee_detail||r.ville||'');const cp=txt(r.code_postal_public_listing||r.code_postal_prive_detail||r.code_postal||'');const adr=txt(r.adresse_privee_listing||r.adresse_detail||'');const photo=listingPhoto(r);return `<tr data-id="${esc(r.hektor_annonce_id)}" class="${String(r.hektor_annonce_id)===String(selectedId)?'sel':''}"><td><div class="mono">${esc(r.numero_dossier||'')}</div><div class="muted">${esc(r.mandat_numero_source||r.numero_mandat||'')}</div></td><td><div class="stock-row-main">${photo?`<div class="stock-photo-wrap">${photo}</div>`:''}<div><b>${esc(displayTitle(r))}</b><div class="muted">${esc(typeLabel(r.type_bien)||'')} - ${esc(r.prix||'')}</div></div></div></td><td><div>${esc(adr||ville||'')}</div><div class="muted">${esc(ville)}${cp?' - '+esc(cp):''}</div></td><td>${esc(r.responsable_affichage||'')}</td><td><div>${esc(displayGlobalStatus(r)||'')}</div><div class="muted">${esc(r.statut_annonce||'')}</div></td><td><div>${esc(r.next_action||'')}</div><div class="muted">${esc(r.date_enregistrement_annonce||'')}</div></td></tr>`;}).join('');const current=rows.find(r=>String(r.hektor_annonce_id)===String(selectedId))||pageRows[0]||null;els.quick.innerHTML=quickView(current);els.rows.querySelectorAll('tr[data-id]').forEach(tr=>{tr.onclick=()=>{selectedId=tr.dataset.id;render();};tr.ondblclick=()=>{const row=rows.find(r=>String(r.hektor_annonce_id)===String(tr.dataset.id));if(row)openFull(row,true);};});}
function detailRow(row){const chunk=window.APP_DETAIL_CHUNKS[row.detail_chunk]||{};const extra=chunk[String(row.hektor_annonce_id)]||{};return Object.assign({},row,extra);}
function ensureChunk(row){if(!row||!row.detail_chunk)return Promise.resolve();if(window.APP_DETAIL_CHUNKS[row.detail_chunk])return Promise.resolve();if(loaders[row.detail_chunk])return loaders[row.detail_chunk];loaders[row.detail_chunk]=new Promise((ok,ko)=>{const s=document.createElement('script');s.src='./app_metier_detail_data/'+row.detail_chunk;s.onload=()=>ok();s.onerror=()=>ko(new Error(`load ${row.detail_chunk}`));document.head.appendChild(s);});return loaders[row.detail_chunk];}
function section(title,body){return `<section class="box"><h4>${title}</h4>${body}</section>`;}
function grid(items){const html=items.filter(x=>txt(x[1])).map(x=>`<div class="info"><small>${x[0]}</small>${esc(x[1])}</div>`).join('');return html?`<div class="grid">${html}</div>`:'<div class="empty">Aucune information exploitable</div>';}
function detailView(r){const raw=j(r.detail_raw_json)||{};const owners=j(r.proprietaires_json)||[];const notes=j(r.notes_json)||[];const mandats=j(r.mandats_json)||[];const imgs=(j(r.images_json)||j(r.images_preview_json)||[]).filter(i=>i&&(i.url||i.full||i.path));const txts=j(r.textes_json)||[];const title=displayTitle(r);const hero=`<section class="crmH"><div class="crmT"><div><h2>${esc(title)}</h2><div class="sub">${esc(join([typeLabel(r.type_bien),r.adresse_privee_listing||r.adresse_detail,r.code_postal_public_listing||r.code_postal_prive_detail||r.code_postal,r.ville_publique_listing||r.ville_privee_detail||r.ville]))}</div><div class="badges">${[displayGlobalStatus(r),r.validation_diffusion_state,r.etat_visibilite,r.etat_transaction,r.detail_statut_name,r.alerte_principale].filter(Boolean).map(v=>`<span class="badge">${esc(v)}</span>`).join('')}</div></div><div class="badges">${[r.responsable_affichage,r.priority,r.next_action].filter(Boolean).map(v=>`<span class="badge">${esc(v)}</span>`).join('')}</div></div><div class="kpis"><article class="kpi"><span>Prix</span><strong>${esc(r.prix||'')}</strong></article><article class="kpi"><span>Surface</span><strong>${esc(r.surface_habitable_detail||r.surface||'')}</strong></article><article class="kpi"><span>Pieces / chambres</span><strong>${esc(join([r.nb_pieces,r.nb_chambres],' / ')||'-')}</strong></article><article class="kpi"><span>Photos</span><strong>${esc(r.nb_images||0)}</strong></article></div></section>`;const media=imgs.length?section('Photos',`<div class="mainimg"><a href="${esc(imgs[0].full||imgs[0].url||imgs[0].path||'')}" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="${esc(imgs[0].url||imgs[0].full||imgs[0].path||'')}" alt="${esc(imgs[0].legend||title||'Image annonce')}" /></a></div>${imgs.slice(1,9).length?`<div class="thumbs">${imgs.slice(1,9).map(i=>`<a href="${esc(i.full||i.url||i.path||'')}" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="${esc(i.url||i.full||i.path||'')}" alt="${esc(i.legend||title||'Image annonce')}" /></a>`).join('')}</div>`:''}`):section('Photos','<div class="empty">Aucune photo</div>');const texts=[ok(r.texte_principal_html)?`<article class="txt"><b>DetailAnnonce</b>${r.texte_principal_html}</article>`:'',ok(r.corps_listing_html)&&txt(r.corps_listing_html)!==txt(r.texte_principal_html)?`<article class="txt"><b>ListAnnonces</b>${r.corps_listing_html}</article>`:'',...txts.filter(t=>txt(t&&t.text)&&txt(t.text)!==txt(r.texte_principal_html)&&txt(t.text)!==txt(r.corps_listing_html)).map(t=>`<article class="txt"><b>${esc(join([t.type,t.lang,t.titre])||'Texte')}</b>${br(t.text)}</article>`)].filter(Boolean).join('')||'<div class="empty">Aucun descriptif</div>';const ownersHtml=owners.length?owners.map(p=>`<article class="item"><h5>${esc(join([p.civilite,p.prenom,p.nom],' ')||'Contact')}</h5><div>${br(join([Array.isArray(p.typologie)?p.typologie.join(', '):'',p.dateenr]))}</div><div>${br(join([p.coordonnees&&p.coordonnees.portable,p.coordonnees&&p.coordonnees.email]))}</div><div>${br(join([p.localite&&p.localite.localite&&p.localite.localite.adresse,p.localite&&p.localite.localite&&p.localite.localite.code,p.localite&&p.localite.localite&&p.localite.localite.ville]))}</div><div>${br(txt(p.commentaires||''))}</div></article>`).join(''):'<div class="empty">Aucun contact</div>';const notesHtml=([ok(r.note_hektor_principale)?{t:'Synthese',d:'',c:r.note_hektor_principale}:null,...notes.slice(0,8).map(n=>({t:n.type,d:n.date,c:n.content}))].filter(n=>n&&txt(n.c))).map(n=>`<article class="item"><div class="muted" style="margin-bottom:6px">${esc(n.t||'NOTE')}${n.d?' - '+esc(n.d):''}</div><div>${br(n.c||'')}</div></article>`).join('')||'<div class="empty">Aucune note</div>';const mandatsHtml=((mandats.length?mandats.map(m=>`<article class="step"><strong>${esc(join([m.numero,m.type])||'Mandat')}</strong><div>${br(join(['Enregistrement',m.debut||m.dateenr||m.date_enregistrement],': '))}</div><div>${br(join(['Fin',m.fin],': '))}</div><div>${br(join(['Cloture',m.cloture],': '))}</div><div>${br(join(['Montant',m.montant],': '))}</div><div>${br(txt(m.note||''))}</div></article>`).join(''):'')||([r.numero_mandat,r.mandat_numero_source].some(ok)?`<article class="step"><strong>${esc(join([r.mandat_numero_source||r.numero_mandat,r.mandat_type_source||r.mandat_type],' - ')||'Mandat')}</strong><div>${br(join(['Numero',r.mandat_numero_source||r.numero_mandat],': '))}</div>${ok(r.mandat_date_enregistrement)?`<div>${br(join(['Date enr.',r.mandat_date_enregistrement],': '))}</div>`:''}${ok(r.mandat_montant)?`<div>${br(join(['Montant',r.mandat_montant],': '))}</div>`:''}</article>`:''))||'<div class="empty">Aucun mandat detail</div>';return `<div class="crm">${hero}<div class="crmL"><div class="stack">${media}${section('Descriptif',texts)}${section('Fiche bien',grid([['Dossier',r.numero_dossier],['Mandat',r.mandat_numero_source||r.numero_mandat],['Type de bien',typeLabel(r.type_bien)],['Prix',r.prix],['Surface listing',r.surface],['Surface habitable',r.surface_habitable_detail],['Pieces',r.nb_pieces],['Chambres',r.nb_chambres],['Etage',r.etage_detail],['Terrasse',r.terrasse_detail],['Garage / box',r.garage_box_detail],['Surface terrain',r.surface_terrain_detail],['Copropriete',r.copropriete_detail],['Ascenseur',r.ascenseur_detail],['Adresse',r.adresse_privee_listing||r.adresse_detail],['Ville',r.ville_publique_listing||r.ville_privee_detail||r.ville],['Code postal',r.code_postal_public_listing||r.code_postal_prive_detail||r.code_postal],['Latitude',r.latitude_detail],['Longitude',r.longitude_detail],['Date enregistrement',r.date_enregistrement_annonce],['Derniere MAJ',r.date_maj],['Statut source',r.statut_annonce],['Statut global',displayGlobalStatus(r)],['Statut detail',r.detail_statut_name],['Validation diffusion',r.validation_diffusion_state],['Visibilite',r.etat_visibilite]]))}${raw.ag_interieur?section('Interieur',grid(Object.entries(raw.ag_interieur.props||{}).map(([k,m])=>[(m&&m.label)||k,(m&&m.value)||'']))):''}${raw.ag_exterieur?section('Exterieur',grid(Object.entries(raw.ag_exterieur.props||{}).map(([k,m])=>[(m&&m.label)||k,(m&&m.value)||'']))):''}${raw.equipements?section('Equipements',grid(Object.entries(raw.equipements.props||{}).map(([k,m])=>[(m&&m.label)||k,(m&&m.value)||'']))):''}${raw.diagnostiques?section('Diagnostics',grid(Object.entries(raw.diagnostiques.props||{}).map(([k,m])=>[(m&&m.label)||k,(m&&m.value)||'']))):''}${raw.terrain?section('Terrain',grid(Object.entries(raw.terrain.props||{}).map(([k,m])=>[(m&&m.label)||k,(m&&m.value)||'']))):''}${raw.copropriete?section('Copropriete',grid(Object.entries(raw.copropriete.props||{}).map(([k,m])=>[(m&&m.label)||k,(m&&m.value)||'']))):''}${section('Transaction',`<div class="txnG">${['Offre','Compromis','Vente'].map(name=>{const map={Offre:[['ID',r.offre_id],['Etat',r.offre_state],['Date',r.offre_event_date],['Montant',r.offre_montant],['Acquereur',r.offre_acquereur_nom],['Contact',join([r.offre_acquereur_portable,r.offre_acquereur_email])]],Compromis:[['ID',r.compromis_id],['Etat',r.compromis_state],['Debut',r.compromis_date_start],['Fin',r.compromis_date_end],['Prix public',r.prix_publique],['Prix net vendeur',r.prix_net_vendeur],['Sequestre',r.compromis_sequestre],['Acquereurs',r.compromis_acquereurs_resume]],Vente:[['ID',r.vente_id],['Date',r.vente_date],['Prix',r.vente_prix],['Honoraires',r.vente_honoraires],['Commission agence',r.vente_commission_agence],['Acquereurs',r.vente_acquereurs_resume],['Notaires',r.vente_notaires_resume]]};const items=map[name].filter(x=>txt(x[1]));return `<article class="txn"><h5>${name}</h5>${items.length?items.map(x=>`<div>${esc(x[0])} : ${esc(x[1])}</div>`).join(''):'<div class="empty">Aucune information</div>'}</article>`}).join('')}</div>`)}${section('Notes et commentaires',`<div class="list2">${notesHtml}</div>`)}</div><aside class="stack">${section('Pilotage CRM',grid([['Responsable',r.responsable_affichage],['Role responsable',r.responsable_type],['Statut global',displayGlobalStatus(r)],['Sous-statut',displaySubStatus(r)],['Alerte',r.alerte_principale],['Priorite',r.priority],['Action suivante',r.next_action],['Commentaire interne',r.commentaire_resume],['Blocage',r.motif_blocage],['Transaction',r.etat_transaction],['Archive',r.archive],['Diffusable',r.diffusable]]))}${section('Mandat et valorisation',grid([['Mandat numero source',r.mandat_numero_source||r.numero_mandat],['Mandat type source',r.mandat_type_source],['Mandat type',r.mandat_type],['Mandat date enr.',r.mandat_date_enregistrement],['Mandat debut',r.mandat_date_debut],['Mandat fin',r.mandat_date_fin],['Mandat cloture',r.mandat_date_cloture],['Mandat montant',r.mandat_montant],['Mandants',r.mandants_texte],['Honoraires',r.honoraires_resume],['Prix public',r.prix_publique],['Prix net vendeur',r.prix_net_vendeur]]))}${section('Proprietaires et contacts',`<div class="list2">${ownersHtml}</div>`)}${section('Mandat',`<div class="list2">${mandatsHtml}</div>`)}</aside></div></div>`;}
function render(){const rows=filtered();if(screen==='dashboard'){renderDashboard(rows);return;}if(screen==='stock'){renderStock(rows);return;}}
function openFull(row,push=true){if(!row)return;selectedId=row.hektor_annonce_id;els.title.textContent=`Annonce complete - ${row.numero_dossier||''}`;els.sub.textContent=`${displayTitle(row)} - ${join([row.ville,row.responsable_affichage])}`;els.full.innerHTML='<div class="longtext">Chargement...</div>';setScreen('annonce');if(push)location.hash='annonce-'+encodeURIComponent(row.hektor_annonce_id);ensureChunk(row).then(()=>{els.full.innerHTML=detailView(detailRow(row));}).catch(err=>{const msg=err&&err.message?err.message:row.detail_chunk||'chunk inconnu';els.full.innerHTML=`<div class="longtext">Impossible de charger le detail lourd: ${esc(msg)}</div>`;});}
fill(els.commercial,'responsable_affichage','Tous');fill(els.statut,'statut_global','Tous');fill(els.alerte,'alerte_principale','Toutes');fill(els.validation,'validation_diffusion_state','Toutes');[els.q,els.commercial,els.statut,els.alerte,els.validation].forEach(el=>el.addEventListener('input',()=>{currentPage=1;render();}));els.prev.onclick=()=>{currentPage--;render();};els.next.onclick=()=>{currentPage++;render();};document.querySelectorAll('.side button[data-screen]').forEach(btn=>btn.onclick=()=>{location.hash='';if(btn.dataset.screen==='stock')currentPage=1;setScreen(btn.dataset.screen);render();});els.open.onclick=()=>openFull(filtered().find(r=>String(r.hektor_annonce_id)===String(selectedId))||filtered()[0]||null);els.back.onclick=()=>{location.hash='';setScreen('stock');render();};window.addEventListener('hashchange',()=>{if(location.hash.startsWith('#annonce-')){const id=decodeURIComponent(location.hash.slice(9));openFull(DATA.find(r=>String(r.hektor_annonce_id)===String(id)),false);}else if(location.hash===''){setScreen('stock');render();}});setScreen('dashboard');render();
