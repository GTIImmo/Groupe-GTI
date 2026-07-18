import type { DashboardSummary, DiffusionRequest, DiffusionRequestEvent, DiffusionTarget, Dossier, MandatBroadcast, MandatRecord, UserProfile, WorkItem } from '../types'

export const mockSummary: DashboardSummary = {
  total_dossiers: 55976,
  total_demandes: 21377,
  total_sans_mandat: 31683,
  total_bloques: 0,
  total_valides_diffusion: 1310,
  total_visibles: 406,
}

export const mockDossiers: Dossier[] = [
  {
    // Cas riche n°1 : mandat validé + diffusé (phase « dif ») → parcours partiel, prochaine action « Relancer les acquéreurs ».
    app_dossier_id: 32621,
    hektor_annonce_id: 4,
    photo_url_listing: 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=240&q=60',
    numero_dossier: 'VA1926',
    numero_mandat: '17125',
    titre_bien: 'Grand T3 secteur Bellevue avec Garage',
    ville: 'Saint-Etienne',
    code_postal: '42000',
    type_bien: '2',
    prix: 259000,
    commercial_id: '5',
    commercial_nom: 'Melanie LEGRAND',
    agence_nom: 'GTI Saint-Etienne',
    negociateur_email: 'melanie.legrand@gti.test',
    statut_annonce: 'Disponible',
    validation_diffusion_state: 'valide',
    diffusable: '1',
    nb_portails_actifs: 3,
    portails_resume: "SeLoger · Leboncoin · Bien'ici",
    date_maj: '2026-06-15T16:02:00Z',
    etat_visibilite: 'visible',
    alerte_principale: null,
    priority: 'high',
    has_open_blocker: false,
    commentaire_resume: '',
    date_relance_prevue: null,
    dernier_event_type: 'visible',
    dernier_work_status: 'done',
  },
  {
    // Cas riche n°2 : offre reçue (phase « tra ») → parcours Offre en cours, prochaine action « Traiter l'affaire ».
    app_dossier_id: 5502,
    hektor_annonce_id: 15,
    photo_url_listing: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=240&q=60',
    numero_dossier: 'VA1988',
    numero_mandat: '16635',
    titre_bien: 'T3 lumineux avec balcon, quartier Fauriel',
    ville: 'Saint-Etienne',
    code_postal: '42100',
    type_bien: '2',
    prix: 189000,
    commercial_id: '5',
    commercial_nom: 'Melanie LEGRAND',
    agence_nom: 'GTI Saint-Etienne',
    negociateur_email: 'melanie.legrand@gti.test',
    statut_annonce: 'Disponible',
    validation_diffusion_state: 'valide',
    diffusable: '1',
    nb_portails_actifs: 3,
    portails_resume: 'SeLoger · Leboncoin · Bienici',
    offre_id: 'OF-2231',
    offre_state: 'en_cours',
    etat_visibilite: 'visible',
    alerte_principale: null,
    priority: 'high',
    has_open_blocker: false,
    commentaire_resume: '',
    date_relance_prevue: null,
    dernier_event_type: 'visible',
    dernier_work_status: 'done',
  },
]

// Payloads détaillés (mock) : injectés par loadDossierDetail quand Supabase est absent, pour
// exercer les blocs data-dépendants du cockpit (photos, €/m², contacts, RDV, offre, portails).
function mockImages(seeds: Array<[string, string]>) {
  return seeds.map(([id, legend]) => ({ url: `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=1200&q=70`, legend }))
}
export const mockDetailPayloads: Record<number, Record<string, unknown>> = {
  32621: {
    surface_habitable_detail: 74,
    date_avis: '2026-06-11',
    date_mandat: '2026-06-15',
    nb_pieces: 3,
    nb_chambres: 2,
    etage_detail: '3e étage avec ascenseur',
    garage_box_detail: 'Garage fermé',
    surface_terrain_detail: 0,
    adresse_detail: '18 rue de la Bellevue',
    code_postal_prive_detail: '42000',
    ville_privee_detail: 'Saint-Etienne',
    latitude_detail: 45.4397,
    longitude_detail: 4.3872,
    // Le Bien (v21) : description, diagnostics DPE/GES, notes internes.
    texte_principal_titre: 'Grand T3 lumineux · secteur Bellevue',
    texte_principal_html: '<p><b>Exclusivité — secteur Bellevue.</b> Grand T3 de 74 m² au 3e étage avec ascenseur, très lumineux, séjour traversant ouvrant sur balcon, deux chambres et cuisine équipée. Garage fermé en sous-sol.</p><p>Proche commerces, écoles et transports. Copropriété bien tenue, faibles charges. Idéal premier achat ou investissement locatif.</p>',
    dpe_conso: 210,
    dpe_ges: 35,
    ascenseur_detail: 'Oui',
    // Calque optimiste (mock) : peuple les champs wizard lus par wizardDetailValue (overlay-first).
    // Overlay optimiste = vrais champs wizard Hektor (rendu « plein » de la fiche Le Bien, façon v21).
    app_optimistic_overlay: {
      // Composition
      nbpieces: '3', NB_CHAMBRES: '2', NB_NIVEAUX: '1', ETAGE: '3', surfappart: '74', SURF_CARREZ: '74', EXPOSITION: 'Sud-Ouest', vuee: 'Dégagée',
      // Intérieur
      NB_SDB: '1', NB_SE: '1', NB_WC: '1', SURF_SEJOUR: '28', CUISINE: 'Équipée', CUISINE_EQUIPEMENT: 'Four, plaque, hotte', cheminee: 'NON', Particularites: 'Balcon exposé sud',
      // Extérieur & annexes
      MURS_MITOYENS: 'NON', NB_ETAGES: '4', CAVE: 'OUI', SURFACE_CAVE: '6', BALCON: 'OUI', NB_BALCON: '1', SURFACE_BALCON: '5',
      TERRASSE: 'OUI', NB_TERRASSE: '1', SURFACE_TERRASSE: '8', 'GARAGE_BOX': '1', SURFACE_GARAGE: '15', NB_PARK_INT: '1', NB_PARK_EXT: '0',
      'JARDIN-': 'NON', surfterrain: '', SHON: '', terrain_arbore: 'NON', terrain_constructible: 'NON', terrain_viabilise: 'OUI',
      // Construction
      ANNEE_CONS: '1972', etat_interieur: 'Bon état', etat_exterieur: 'Bon état', garantie_decennale: 'NON', assurance_dommages_ouvrage: 'NON', certificat_conformite: 'NON', declaration_achevement_travaux: 'NON',
      // Piscine (appartement → masquée via condField PISCINE-)
      'PISCINE-': 'NON',
      // Confort & équipements
      formatChauff: 'Individuel', typeChauff: 'Gaz', energieChauff: 'Gaz de ville', ASCENSEUR: 'OUI', ACCES_HANDI: 'NON', climatisation: 'NON',
      EAU: 'Ville', ASSAINISSEMENT: 'Tout à l’égout', DISTRIBUTION_EAU: 'Individuelle', ENERGIE_EAU: 'Gaz',
      volets_elctriques: 'OUI', double_vitrage: 'OUI', triple_vitrage: 'NON', cable: 'OUI', porte_blindee: 'NON',
      interphone: 'OUI', visiophone: 'NON', alarme: 'NON', digicode: 'OUI', detecteur_fumee: 'OUI', gardien: 'NON',
      // Copropriété (affichée via condField copropriete=OUI)
      copropriete: 'OUI', copropriete_lot: '42', copropriete_nb_lot: '36', copropriete_quote_part: '120/1000', montant_fonds_travaux: '1 200', copropriete_plan_sauvegarde: 'NON', copropriete_statut_syndicat: 'Sans procédure',
      // Diagnostics & énergie
      diagnostiqueur: 'Diag Immo 42', dpe_date: '15/05/2026', dpe_cons: '210', dpe_ges: '32', dpe_couts_min: '980', dpe_couts_max: '1 380', dpe_annee_reference: '2021',
      diag_amiante: 'OUI', diag_amiante_date: '15/05/2026', diag_termites: 'NON', diag_termites_date: '', diag_plomb: 'OUI', diag_plomb_date: '15/05/2026',
      diag_electrique: 'OUI', diag_electrique_date: '15/05/2026', diag_gaz: 'OUI', diag_loi_carrez: 'OUI', diag_risques_nat_tech: 'OUI', diag_assainissement: 'NON',
      // Prix, mandat & honoraires
      prix: '259000', PRIXNETVENDEUR: '246000', _selecterHonoraires2: 'Charge acquéreur', _tauxHonoraire2: '13000', _pourcentHonoraire2: '5,28',
      _selecterHonoraires3: '', _tauxHonoraire3: '', masque: '', ESTIMATION_MONTANT: '265000', ESTIMATION_DATE: '11/06/2026',
      TRAVAUX: 'Rafraîchissement peintures', DEPOT_GARANTIE: '', TAXE_FONCIERE: '980', TAXE_HABITATION: '', CHARGES: '1 320', CHARGES_DETAIL: 'Eau froide, entretien parties communes, ascenseur',
      // Disponibilité & visite
      DISPO: 'OUI', DATE_LIBER: '01/10/2026', DATE_DISPO: '01/10/2026', CLES: 'À l’agence', moyens_visite: 'Sur RDV · bon de visite',
      // Diffusion
      diffusable: 'Oui', titre: 'Grand T3 secteur Bellevue avec garage', NO_DOSSIER: 'VA1926', dateenr: '11/06/2026',
      // Localisation & secteur
      codepublique: '42000', villepublique: 'Saint-Etienne', ADRESSE_COMPL: '18 rue de la Bellevue', TRANSPORT: 'Tram T1 · 300 m', PROXIMITE: 'Commerces, écoles, parc', ENVIRONNEMENT: 'Quartier résidentiel calme', latitude: '45.4397', longitude: '4.3872',
    },
    notes_json: JSON.stringify([
      { type: 'Note interne', date: '2026-06-12', content: 'Vendeurs disponibles pour les visites en semaine après 17 h. Prévoir un bon de visite systématique.' },
      { type: 'Note interne', date: '2026-06-28', content: 'Prix légèrement au-dessus du marché — envisager une baisse si pas d’offre sous 3 semaines.' },
    ]),
    images_json: JSON.stringify(mockImages([
      ['1505693416388-ac5ce068fe85', 'Séjour'],
      ['1512917774080-9991f1c4c750', 'Façade'],
      ['1522708323590-d24dbb6b0267', 'Cuisine'],
      ['1502672260266-1c1ef2d93688', 'Chambre'],
      ['1560448204-e02f11c3d0e2', 'Salle de bains'],
    ])),
    proprietaires_json: JSON.stringify([
      {
        id: 'P-1001', civilite: 'M.', prenom: 'Jean', nom: 'MOREAU', typologie: ['mandant'],
        coordonnees: { portable: '06 12 34 56 78', email: 'jean.moreau@example.fr' },
        localite: { localite: { code: '42000', ville: 'Saint-Etienne', adresse: '18 rue de la Bellevue' } },
        commentaires: 'Vendeur motivé, disponible en semaine après 17 h.', datemaj: '2026-06-15',
      },
      {
        id: 'P-1002', civilite: 'Mme', prenom: 'Claire', nom: 'MOREAU', typologie: ['mandant'],
        coordonnees: { portable: '06 98 76 54 32', email: 'claire.moreau@example.fr' },
        localite: { localite: { code: '42000', ville: 'Saint-Etienne', adresse: '18 rue de la Bellevue' } },
        commentaires: 'Co-vendeur (indivision) — passer par M. MOREAU en priorité.', datemaj: '2026-06-15',
      },
    ]),
    appointment_requests_json: JSON.stringify([
      { id: 'RDV-1', visitor_name: 'Sophie BERNARD', visitor_email: 'sophie.bernard@example.fr', status: 'pending', requested_at: '2026-07-14T10:00:00Z', message: 'Disponible en semaine après 18h.' },
      { id: 'RDV-2', visitor_name: 'Karim ALLAOUI', visitor_email: 'karim.allaoui@example.fr', status: 'pending', requested_at: '2026-07-15T09:30:00Z', message: 'Souhaite visiter ce week-end.' },
    ]),
    // Publicité (v36) : détail passerelles (dont une bloquée), retour d'application, demandes.
    portails_detail_json: JSON.stringify([
      { name: 'SeLoger', state: 'active', sub: 'Portail national · annonce en ligne' },
      { name: 'Leboncoin', state: 'active', sub: 'Portail national · annonce en ligne' },
      { name: "Bien'ici", state: 'active', sub: 'Portail national · annonce en ligne' },
      { name: 'Le Figaro Immobilier', state: 'blocked', sub: 'Passerelle bloquée côté Hektor · à réactiver' },
    ]),
    diffusion_apply_json: JSON.stringify({ add: 1, remove: 0, ok: 3, wait: 1, err: 0, at: '2026-06-15T16:02:00Z' }),
    diffusion_requests_json: JSON.stringify([
      { date: '2026-06-15', title: 'Demande de diffusion', status: 'Acceptée', tone: 'ok' },
      { date: '2026-06-30', title: 'Baisse de prix (269 000 → 259 000)', status: 'En traitement', tone: 'wait' },
    ]),
    // Contact (v34) : intervenants diagnostics & syndic.
    intervenants_json: JSON.stringify([
      { role: 'Diagnostiqueur', name: 'Diag Immo 42', sub: 'DPE · Amiante · Électricité · Gaz', phone: '04 77 00 00 00' },
      { role: 'Notaire acquéreur', name: 'Me Bernard', sub: 'Étude Bernard & Associés', phone: '04 77 11 11 11' },
      { role: 'Notaire vendeur', name: '', sub: '' },
      { role: 'Syndic', name: '', sub: 'Copropriété — non applicable si maison individuelle' },
    ]),
    // Affaires (v31) : aucune offre en cours (annonce en ligne, en attente d'offre).
    affaire_json: JSON.stringify({
      banner: { mood: 'ok', state: "En ligne — en attente d'offre", next: 'Relancer les acquéreurs rapprochés — 0 proposition en attente.', comment: '', chip: '✓ Aucun blocage' },
      tl: { offre: 'pending', compromis: 'pending', vente: 'pending' },
      offre: null,
      compromis: null,
      vente: null,
      parties: { acq: null, notAcq: null, notVend: null, vendeur: { n: 'M. & Mme MOREAU', s: 'Mandants · vendeurs · Contact 18542', tel: '0612345678', mail: 'jean.moreau@example.fr' } },
      honoraires: { fai: '12 500 € TTC', charge: 'Acquéreur', taux: '4,83 % TTC', part: '100 % agence', rendement: '4,1 %' },
    }),
    price_change_event_count: 1,
    price_change_last_old_value: 269000,
    price_change_last_new_value: 259000,
    price_change_last_detected_at: '2026-06-30T08:00:00Z',
    // Activité (v26 synthèse) : fil d'événements variés.
    activite_json: JSON.stringify([
      { icon: 'rapprochement', aud: 'acq', nb: '#daeef1', nc: '#0f7c8a', time: 'il y a 5 min', html: '<b>Nouvel acquéreur</b> correspond — M. Petit · <b>score 92</b>', new: true },
      { icon: 'heart', aud: 'acq', nb: '#fdeaf2', nc: '#c2125f', time: 'il y a 30 min', html: '<b>Coup de cœur ❤️</b> — Mme Leroy a aimé le bien · <b>lead chaud</b>' },
      { icon: 'rendezvous', aud: 'acq', nb: '#ece4f8', nc: '#6d4bb5', time: 'il y a 25 min', html: "<b>Demande de visite</b> — Mme Leroy · issue de l'espace client" },
      { icon: 'mail', aud: 'acq', nb: '#e7edf7', nc: '#3a5a8a', time: 'il y a 2 h', html: '<b>Reçu</b> de M. Durand (acquéreur) · « Toujours dispo samedi ? »' },
      { icon: 'contact', aud: 'mandant', nb: '#e7edf7', nc: '#3a5a8a', time: 'il y a 3 j', html: '<b>Point mandant</b> — appel aux MOREAU · compte-rendu de commercialisation' },
      { icon: 'mail', aud: 'acq', nb: '#fbeee0', nc: '#c2701a', time: 'il y a 6 j', html: '<b>Relance à faire</b> — M. Morel · proposé, sans réponse', over: true },
    ]),
    // Historique (v27) : journal des demandes filtrable.
    historique_json: JSON.stringify([
      { title: 'Bien diffusable non visible', type: 'Diffusion', date: '2026-06-24', states: [{ a: 'pending', b: 'pret_diffusion' }, { a: 'valide', b: 'en_erreur', tone: 'err' }], relance: '—' },
      { title: 'Demande de baisse de prix', type: 'Baisse de prix', date: '2026-06-20', states: [{ a: 'pending', b: 'a_traiter' }, { a: 'accepte', b: 'applique', tone: 'ok' }], relance: '02/07/2026' },
      { title: 'Demande de validation', type: 'Diffusion', date: '2026-06-11', states: [{ a: 'pending', b: 'a_valider' }, { a: 'valide', b: 'ok', tone: 'ok' }], relance: '—' },
    ]),
    // Reporting (v27) : vues + envoi propriétaire.
    vues_30j: 148,
    report_sent: '2026-06-28',
    report_opened: '2026-06-29',
    // Documents (v27) : liste avec type + statut signature.
    documents_json: JSON.stringify([
      { name: 'Mandat 17125.pdf', sig: 'Signé le 14/06 · ImmoSign', badge: 'Signé', signed: true, type: 'mandat', typeLabel: 'Mandat' },
      { name: 'DPE.pdf', sig: 'À envoyer en signature', badge: 'À préparer', signed: false, type: 'diag', typeLabel: 'Diagnostic' },
      { name: 'Avenant rectificatif.pdf', sig: 'À envoyer en signature', badge: 'À préparer', signed: false, type: 'avenant', typeLabel: 'Avenant' },
      { name: 'Attestation de propriété.pdf', sig: 'À envoyer en signature', badge: 'À préparer', signed: false, type: 'autre', typeLabel: 'Autre' },
      { name: 'Plan des lots.pdf', sig: 'À envoyer en signature', badge: 'À préparer', signed: false, type: 'autre', typeLabel: 'Autre' },
    ]),
    // Mandat (v22) : n° mandat, dates, honoraires, suivi de signature.
    mandat_json: JSON.stringify({
      num: '17125', type: 'ACCORD', dateStart: '15/06/2026', dateEnd: '14/06/2027', statut: 'Valide',
      honorairesVendeur: '18 000 €', taux: '4,6 %',
      demarches: [
        { title: 'Validation', sub: 'Confirmer le mandat pour débloquer la diffusion', state: 'ok', badge: 'Demande de validation', act: 'Demander' },
        { title: 'Baisse de prix', sub: 'Ajuster le prix public de l’annonce', state: 'lock', lockLabel: 'Après validation' },
        { title: 'Annulation mandat', sub: 'Clôturer et retirer le mandat', state: 'lock', lockLabel: 'Après validation' },
      ],
      avenant: {
        num: '17125',
        repris: [{ t: 'Mandants (2)', ok: true }, { t: 'Bien & adresse', ok: true }, { t: 'Type ACCORD', ok: true }, { t: 'Durée', ok: true }, { t: 'Honoraires — à confirmer', warn: true }],
        nouveauxHonos: '16 000 €', dateAvenant: '10/07/2026',
      },
      signatures: [
        { av: 'IS', tone: 'ok', name: 'Mandat de vente 17125.pdf', sub: 'Envoyé le 12/06 · signé le 14/06 par les mandants', badge: 'Signé', badgeTone: 'ok' },
        { av: 'A', tone: 'wait', name: 'Avenant rectificatif.pdf', sub: 'Envoyé le 08/07 · en attente de signature', badge: 'En attente', badgeTone: 'wait' },
      ],
    }),
    // Estimation (v27) : avis de valeur + KPIs + barème + sources mémorisées.
    estimation_json: JSON.stringify({
      valeur: '259 000 €', prixM2: '3 500 €', basse: '238 000 €', haute: '278 000 €', grade: 'Bon état',
      kpis: [{ k: 'Valeur estimée', v: '259 000 €', s: 'marché DVF', tone: 'br' }, { k: 'Rendement brut', v: '4,6 %', s: 'potentiel locatif', tone: '' }, { k: 'DPE réel', v: 'D · 210', s: 'ADEME', tone: '' }],
      sources: [
        { icon: 'estimation', title: 'Marché & valeur', sub: 'Ventes DVF comparables du secteur', c: '#c2125f', s: '#f9e7ef', desc: 'Prix médian au m² et valeur estimée à partir des ventes comparables (même type, surface ±20 %).', state: 'ok', stateLabel: 'à jour · 08/07', value: '2 610 €/m² médian' },
        { icon: 'lebien', title: 'Le bâti', sub: 'Caractéristiques BDNB · RNB', c: '#b5651d', s: '#f6e9db', desc: 'Année, type, matériaux, niveaux, DPE théorique depuis la Base de Données Nationale des Bâtiments.', state: 'ok', stateLabel: 'à jour · 08/07', value: '1972 · béton' },
        { icon: 'estimation', title: 'DPE réel', sub: 'Dernier diagnostic ADEME', c: '#2f8a5b', s: '#e6f2ea', desc: "Dernier DPE réel de l'ADEME retrouvé par l'adresse exacte (id BAN).", state: 'ok', stateLabel: 'à jour · 08/07', value: 'D · 210 kWh/m²' },
        { icon: 'rendezvous', title: 'Cadre de vie', sub: 'Commodités & risques', c: '#3a5a8a', s: '#e7edf7', desc: 'Commodités (écoles, commerces, santé) et risques naturels/technologiques.', state: 'old', stateLabel: 'à actualiser', value: '' },
        { icon: 'reporting', title: 'Profil commune', sub: 'Population & revenus (INSEE)', c: '#0f7c8a', s: '#daeef1', desc: 'Population (INSEE), évolution, revenu médian des ménages (FiLoSoFi).', state: 'ok', stateLabel: 'à jour · 08/07', value: '172 000 hab' },
        { icon: 'estimation', title: 'Potentiel locatif', sub: 'Loyer de marché & rendement', c: '#0f7c8a', s: '#daeef1', desc: 'Loyer de marché, loyer mensuel estimé, rendement brut et zone fiscale ABC.', state: 'void', stateLabel: 'non récupéré', value: '' },
      ],
    }),
  },
  5502: {
    surface_habitable_detail: 58,
    date_avis: '2026-05-28',
    date_mandat: '2026-06-03',
    date_offre: '2026-07-12',
    nb_pieces: 3,
    nb_chambres: 2,
    etage_detail: '2e étage',
    adresse_detail: '7 boulevard Fauriel',
    code_postal_prive_detail: '42100',
    ville_privee_detail: 'Saint-Etienne',
    offre_id: 'OF-2231',
    offre_state: 'en_cours',
    etat_transaction: 'offre',
    images_json: JSON.stringify(mockImages([
      ['1512917774080-9991f1c4c750', 'Balcon'],
      ['1502672260266-1c1ef2d93688', 'Séjour'],
      ['1522708323590-d24dbb6b0267', 'Cuisine'],
    ])),
    proprietaires_json: JSON.stringify([
      {
        id: 'P-2001', civilite: 'Mme', prenom: 'Isabelle', nom: 'PETIT', typologie: ['mandant'],
        coordonnees: { portable: '06 22 33 44 55', email: 'isabelle.petit@example.fr' },
        localite: { localite: { code: '42100', ville: 'Saint-Etienne', adresse: '7 boulevard Fauriel' } },
        commentaires: 'Vendeuse motivée, disponible en semaine après 17 h.', datemaj: '2026-07-08',
      },
    ]),
    appointment_requests_json: JSON.stringify([
      { id: 'RDV-9', visitor_name: 'Thomas GIRAUD', visitor_email: 'thomas.giraud@example.fr', status: 'confirmed', requested_at: '2026-07-12T14:00:00Z', message: 'Deuxième visite avant offre.' },
    ]),
    // Mandat (v22) sur ce dossier aussi.
    mandat_json: JSON.stringify({
      num: '16635', type: 'ACCORD', dateStart: '03/06/2026', dateEnd: '02/06/2027', statut: 'Valide',
      honorairesVendeur: '9 000 €', taux: '4,94 %',
      demarches: [
        { title: 'Validation', sub: 'Confirmer le mandat pour débloquer la diffusion', state: 'ok', badge: 'Validé', act: 'Voir' },
        { title: 'Baisse de prix', sub: 'Ajuster le prix public de l’annonce', state: 'ok', badge: 'À traiter', act: 'Demander' },
        { title: 'Annulation mandat', sub: 'Clôturer et retirer le mandat', state: 'lock', lockLabel: 'Après validation' },
      ],
      avenant: { num: '16635', repris: [{ t: 'Mandants (1)', ok: true }, { t: 'Bien & adresse', ok: true }, { t: 'Type ACCORD', ok: true }, { t: 'Durée', ok: true }, { t: 'Honoraires — à confirmer', warn: true }], nouveauxHonos: '8 000 €', dateAvenant: '12/07/2026' },
      signatures: [{ av: 'IS', tone: 'ok', name: 'Mandat de vente 16635.pdf', sub: 'Signé le 05/06 par Mme PETIT', badge: 'Signé', badgeTone: 'ok' }],
    }),
    // Affaires (v31) : offre en cours (compromis/vente à venir).
    affaire_json: JSON.stringify({
      banner: { mood: 'warn', state: 'Offre en cours', next: "Traiter l'offre — accepter, contre-proposer ou refuser (via l'évolution du statut).", comment: 'Acquéreur motivé ; financement en cours de validation bancaire.', chip: '⏱ Réponse attendue < 48 h' },
      tl: { offre: 'active', compromis: 'pending', vente: 'pending' },
      offre: { montant: '182 000 €', net: '173 000 €', date: '12/07/2026', validite: '10 j · échéance 22/07/2026', etat: 'Proposition', raw: 'En attente de réponse vendeur', acqNom: 'M. Durand', acqTel: '06 12 34 56 78', acqMail: 'm.durand@email.fr' },
      compromis: null,
      vente: null,
      parties: { acq: { n: 'M. Durand', s: 'Acquéreur · Contact 61924', tel: '0612345678', mail: 'm.durand@email.fr' }, notAcq: null, notVend: null, vendeur: { n: 'Mme Isabelle PETIT', s: 'Vendeur · mandant · Contact 18543', tel: '0622334455', mail: 'isabelle.petit@example.fr' } },
      honoraires: { fai: '9 000 € TTC', charge: 'Acquéreur', taux: '4,94 % TTC', part: '60 % / 40 %', rendement: '4,6 %' },
    }),
  },
}

export const mockWorkItems: WorkItem[] = [
  {
    app_dossier_id: 1,
    hektor_annonce_id: 44506,
    photo_url_listing: 'https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=240&q=60',
    numero_dossier: 'VM18892',
    numero_mandat: '12960',
    titre_bien: 'Appartement T4 avec jardin',
    commercial_nom: 'Melanie LEGRAND',
    negociateur_email: 'melanie.legrand@gti.test',
    agence_nom: 'GTI Saint-Etienne',
    type_demande_label: 'Mandat actif non diffusable',
    work_status: 'pending',
    internal_status: 'a_controler',
    priority: 'high',
    validation_diffusion_state: 'a_controler',
    etat_visibilite: 'non_diffusable',
    motif_blocage: null,
    has_open_blocker: false,
    next_action: null,
    date_relance_prevue: null,
    date_entree_file: '2026-03-24T09:00:00Z',
    date_derniere_action: '2026-03-24T09:00:00Z',
    age_jours: 0,
  },
]

export const mockUserProfile: UserProfile = {
  id: 'local-user',
  email: 'local@gti.test',
  role: 'admin',
  first_name: 'Mode',
  last_name: 'local',
  display_name: 'Mode local',
  is_active: true,
}

export const mockMandats: MandatRecord[] = [
  {
    app_dossier_id: 32621,
    hektor_annonce_id: 4,
    photo_url_listing: 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=240&q=60',
    archive: '0',
    diffusable: '1',
    nb_portails_actifs: 2,
    has_diffusion_error: false,
    portails_resume: 'bienicidirect, leboncoinDirect',
    numero_dossier: 'VA1926',
    numero_mandat: '17125',
    titre_bien: 'Grand T3 secteur Bellevue avec Garage',
    ville: 'Saint-Etienne',
    type_bien: 'Appartement',
    prix: 259000,
    commercial_id: '5',
    commercial_nom: 'Melanie LEGRAND',
    negociateur_email: 'melanie.legrand@gti.test',
    agence_nom: 'GTI Saint-Etienne',
    statut_annonce: 'Actif',
    priority: 'high',
    offre_id: null,
    compromis_id: null,
    vente_id: null,
    source_updated_at: '2026-03-26T10:30:00Z',
    refreshed_at: '2026-03-27T08:30:00Z',
  },
  {
    app_dossier_id: 5502,
    hektor_annonce_id: 15,
    photo_url_listing: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=240&q=60',
    archive: '0',
    diffusable: '1',
    nb_portails_actifs: 3,
    has_diffusion_error: false,
    portails_resume: 'SeLoger · Leboncoin · Bienici',
    numero_dossier: 'VA1988',
    numero_mandat: '16635',
    titre_bien: 'T3 lumineux avec balcon, quartier Fauriel',
    ville: 'Saint-Etienne',
    type_bien: 'Appartement',
    prix: 189000,
    commercial_id: '5',
    commercial_nom: 'Melanie LEGRAND',
    negociateur_email: 'melanie.legrand@gti.test',
    agence_nom: 'GTI Saint-Etienne',
    statut_annonce: 'Actif',
    priority: 'high',
    offre_id: 'OF-2231',
    compromis_id: null,
    vente_id: null,
    source_updated_at: '2026-07-12T10:30:00Z',
    refreshed_at: '2026-07-13T08:30:00Z',
  },
]

export const mockMandatBroadcasts: MandatBroadcast[] = [
  {
    app_dossier_id: 32621,
    hektor_annonce_id: 4,
    passerelle_key: 'leboncoinDirect',
    commercial_key: '5',
    commercial_id: '5',
    commercial_nom: 'Melanie LEGRAND',
    commercial_prenom: '',
    current_state: 'broadcasted',
    export_status: 'exported',
    is_success: true,
    is_error: false,
    refreshed_at: '2026-03-27T08:30:00Z',
  },
  {
    app_dossier_id: 32621,
    hektor_annonce_id: 4,
    passerelle_key: 'bienicidirect',
    commercial_key: '5',
    commercial_id: '5',
    commercial_nom: 'Melanie LEGRAND',
    commercial_prenom: '',
    current_state: 'broadcasted',
    export_status: 'exported',
    is_success: true,
    is_error: false,
    refreshed_at: '2026-03-27T08:30:00Z',
  },
]

export const mockDiffusionRequests: DiffusionRequest[] = []

export const mockDiffusionRequestEvents: DiffusionRequestEvent[] = []

export const mockDiffusionTargets: DiffusionTarget[] = [
  {
    app_dossier_id: 32621,
    hektor_annonce_id: 4,
    hektor_broadcast_id: '2',
    portal_key: 'bienicidirect',
    target_state: 'enabled',
    source_ref: 'mock_seed',
    note: 'Cible locale de demonstration',
    requested_by_role: 'admin',
    requested_by_name: 'Mode local',
    requested_at: '2026-03-31T10:00:00Z',
    last_applied_at: null,
    last_apply_status: null,
    last_apply_error: null,
  },
  {
    app_dossier_id: 32621,
    hektor_annonce_id: 4,
    hektor_broadcast_id: '5',
    portal_key: 'leboncoinDirect',
    target_state: 'enabled',
    source_ref: 'mock_seed',
    note: 'Cible locale de demonstration',
    requested_by_role: 'admin',
    requested_by_name: 'Mode local',
    requested_at: '2026-03-31T10:00:00Z',
    last_applied_at: null,
    last_apply_status: null,
    last_apply_error: null,
  },
]

// Acquéreurs correspondants (écran Rapprochement v35) — démo locale.
// Shape = RapprochementForDossierRow (api.ts) ; api.ts caste. statut : null=À contacter,
// 'propose'/'visite'=En cours, 'ecarte'=Écarté.
function rapRow(o: {
  key: string; nom: string; prenom: string; phone: string; email: string; score: number;
  villes: string[]; type: string; prixMax: number; surfMin: number; piecesMin?: number;
  statut?: 'propose' | 'visite' | 'ecarte' | null; channel?: string; reason?: string; seen?: string; proposedAt?: string;
}): Record<string, unknown> {
  return {
    contact_search_key: o.key, hektor_contact_id: o.key, display_name: `${o.prenom} ${o.nom}`, nom: o.nom, prenom: o.prenom,
    email: o.email, phone: o.phone, search_index: 1,
    villes_json: Object.fromEntries(o.villes.map((v, i) => [String(42000 + i), v])),
    types_json: { [o.type === 'Maison' ? '1' : '2']: o.type },
    criteres_json: {}, prix_min: null, prix_max: o.prixMax, surface_min: o.surfMin, pieces_min: o.piecesMin ?? null,
    chambre_min: null, surface_terrain_min: null,
    owner_negociateur_email: 'melanie.legrand@gti.test', owner_commercial_nom: 'Melanie LEGRAND', agence_nom: 'GTI Saint-Etienne',
    score: o.score, components: null,
    statut: o.statut ?? null, statut_channel: o.channel ?? null, statut_reason: o.reason ?? null,
    proposed_at: o.proposedAt ?? null, first_seen_at: o.seen ?? '2026-07-16T09:00:00Z', computed_at: '2026-07-18T07:00:00Z',
  }
}

export const mockRapprochementsForDossier: Record<number, Array<Record<string, unknown>>> = {
  32621: [
    rapRow({ key: 'rap-c-6101', nom: 'ROUYER', prenom: 'Loïc', phone: '06 47 77 36 25', email: 'loic.rouyer@email.fr', score: 96, villes: ['Saint-Etienne', 'Saint-Priest', 'La Talaudière', 'Villars'], type: 'Appartement', prixMax: 280000, surfMin: 65, piecesMin: 3 }),
    rapRow({ key: 'rap-c-6102', nom: 'BAUZA', prenom: 'Mireille & Patrick', phone: '06 11 22 33 44', email: 'bauza.mp@email.fr', score: 93, villes: ['Saint-Etienne', 'Saint-Chamond', 'Sorbiers'], type: 'Appartement', prixMax: 300000, surfMin: 70, piecesMin: 3 }),
    rapRow({ key: 'rap-c-6103', nom: 'CARRET', prenom: 'Roland', phone: '06 55 44 33 22', email: 'carret.r@email.fr', score: 89, villes: ['Saint-Etienne', 'Roche-la-Molière'], type: 'Appartement', prixMax: 270000, surfMin: 60, piecesMin: 3 }),
    rapRow({ key: 'rap-c-6104', nom: 'ESTEVE', prenom: 'Sophie', phone: '06 78 90 12 34', email: 'sophie.esteve@email.fr', score: 85, villes: ['Saint-Etienne'], type: 'Appartement', prixMax: 265000, surfMin: 70, piecesMin: 3, statut: 'propose', channel: 'email', proposedAt: '2026-07-17T10:00:00Z' }),
    rapRow({ key: 'rap-c-6105', nom: 'MOREL', prenom: 'Karim', phone: '06 33 22 11 00', email: 'karim.morel@email.fr', score: 81, villes: ['Saint-Etienne', 'Firminy'], type: 'Appartement', prixMax: 250000, surfMin: 60 }),
    rapRow({ key: 'rap-c-6106', nom: 'FAURE', prenom: 'Julie', phone: '06 90 80 70 60', email: 'julie.faure@email.fr', score: 78, villes: ['Saint-Etienne'], type: 'Appartement', prixMax: 240000, surfMin: 55, statut: 'ecarte', reason: 'Budget insuffisant' }),
  ],
  5502: [
    rapRow({ key: 'rap-c-6201', nom: 'GIRAUD', prenom: 'Thomas', phone: '06 12 12 12 12', email: 'thomas.giraud@email.fr', score: 94, villes: ['Saint-Etienne', 'Saint-Priest'], type: 'Appartement', prixMax: 200000, surfMin: 60, piecesMin: 3 }),
    rapRow({ key: 'rap-c-6202', nom: 'LAMBERT', prenom: 'Nadia', phone: '06 21 21 21 21', email: 'nadia.lambert@email.fr', score: 88, villes: ['Saint-Etienne'], type: 'Appartement', prixMax: 195000, surfMin: 58, piecesMin: 3 }),
    rapRow({ key: 'rap-c-6203', nom: 'DURAND', prenom: 'M. & Mme', phone: '06 12 34 56 78', email: 'm.durand@email.fr', score: 90, villes: ['Saint-Etienne'], type: 'Appartement', prixMax: 190000, surfMin: 60, piecesMin: 3, statut: 'propose', channel: 'email', proposedAt: '2026-07-12T09:00:00Z' }),
  ],
}
