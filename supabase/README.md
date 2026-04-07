# Supabase V1

Ce dossier contient le schema cible minimal pour la V1 React.

Point de depart :

- contrat `phase2/docs/APP_PAYLOAD_V1_SAMPLE.json`
- note `notice/NOTE_COUCHE_SYNC_PHASE2_REACT_SUPABASE_2026-03-24.md`

Le choix retenu pour la V1 est pragmatique :

- stocker une vue applicative denormalisee
- limiter le couplage du front aux tables internes de phase 2
- garder la possibilite de normaliser davantage plus tard
