-- Renforcement du prompt scan_fiche (app_agent_prompt) — 2026-07-08
-- Objectif : fiabiliser l'extraction de champs mentionnes mais souvent rates par le
-- modele vision (barème d'etat / statePosts, eau, assainissement), ajouter kitchen +
-- kitchenEquipment (absents), et clarifier livingSurface (sejour != habitable).
-- Idempotent : REPLACE ne matche plus une fois applique. Eval OCR : precision 95% tenue,
-- livingSurface corrige (voir backend/evals/scan_fiche). Repli code : agent_registry.py.
update public.app_agent_prompt set instructions =
  replace(
    replace(instructions,
      'water=type d''eau, sanitation=assainissement.',
      'water = le TYPE d''eau coche dans le bloc Equipements (ville/puits/forage). sanitation = l''assainissement coche (tout-a-l''egout / fosse ou individuel). kitchen = l''agencement de la cuisine coche (americaine/kitchenette/separee/ouverte). kitchenEquipment vaut ''oui'' si la cuisine est cochee equipee, sinon ''non''.'),
    'Le tableau ''statePosts'' est le bareme d''etat : une entree par poste evalue (poste ex. ''Toiture'', level = neuf/bon/correct/a prevoir, note = precision ex. ''refaite 2019'') ; liste vide si non rempli.',
    'IMPERATIF statePosts : la fiche contient un tableau ''Etat detaille'' avec une LIGNE par poste (Gros oeuvre/structure, Facade/ravalement, Chauffage/production, Plomberie/sanitaires, Toiture/charpente, Menuiseries/vitrage, Electricite, Interieur/finitions) et 4 colonnes a cocher Neuf/Bon/Correct/A prevoir + une colonne Precision. Pour CHAQUE ligne dont une colonne est cochee, ajoute une entree {poste (nom de la ligne), level = neuf/bon/correct/aprevoir selon la colonne cochee, note = le texte de precision}. Parcours TOUT le tableau, ne l''omets jamais. Precision surfaces : livingSurface = surface du SEJOUR (piece de vie), distincte et generalement plus petite que la surface habitable ; ne confonds pas sejour et habitable. La rangee exterieure aligne plusieurs Oui/Non (Jardin, Piscine, Terrasse, Cave, Balcon, Dernier etage) : lis la case de CHAQUE bloc separement, sans prendre la valeur du voisin.')
where agent_key='scan_fiche';
