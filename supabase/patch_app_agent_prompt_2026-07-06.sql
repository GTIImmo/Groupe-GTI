-- Registre d'agents IA : fiche par agent (prompt + modele + max_tokens), editable
-- sans redeploiement. Le backend lit cette table (service_role) avec repli sur des
-- defauts EN CODE (agent_registry.py) -> si la table/ligne manque, comportement
-- identique. Le schema JSON de sortie reste dans le code (couple au parsing).
--
-- Application GATED (a appliquer manuellement apres validation). Additif, reversible.
-- Seed = prompts ACTUELS ; model NULL -> modele par defaut de l'env (gpt-4.1-mini)
-- jusqu'a ce qu'on choisisse un modele par agent (simple UPDATE, sans redeploy).

create table if not exists public.app_agent_prompt (
  agent_key          text primary key,
  label              text,
  instructions       text not null,
  model              text,                       -- NULL -> defaut env (OPENAI_VISION_MODEL)
  max_output_tokens  integer not null default 1200,
  is_active          boolean not null default true,
  version            integer not null default 1,
  updated_by         text,
  updated_at         timestamptz not null default now(),
  created_at         timestamptz not null default now()
);

comment on table public.app_agent_prompt is
  'Registre des agents IA (prompt + modele + max_tokens). Lu par le backend (service_role) avec repli sur les defauts en code (agent_registry.py). Schema JSON de sortie = cote code.';

-- RLS : verrouille par defaut. Seul le service_role (backend) y accede tant qu'aucune
-- policy n'est ajoutee. Une policy admin (lecture/edition depuis le cockpit) sera
-- ajoutee quand l'ecran d'edition sera construit.
alter table public.app_agent_prompt enable row level security;

-- Seed : les 2 agents de redaction, avec leurs prompts actuels (gabarits {{variables}}).
insert into public.app_agent_prompt (agent_key, label, instructions, model, max_output_tokens)
values
  (
    'redacteur',
    'Redacteur d''annonce',
    $prompt$Tu es redacteur immobilier expert (agence GTI Immobilier). Redige une annonce en francais a partir des seules DONNEES FACTUELLES fournies.
Regles :
- N'utilise QUE les faits fournis ; n'invente aucun chiffre ni caracteristique ; n'affirme rien d'incertain.
- Style precis et evocateur, sans cliches ('coup de coeur', 'ecrin de verdure', 'prestations de qualite', 'rare a la vente') ni superlatifs vides.
- Valorise concretement : volumes, luminosite, exposition, distribution des pieces, atouts techniques (DPE, chauffage) et environnement.
Produis (JSON) :
- title : 60-70 caracteres (type + atout majeur + secteur).
- accroche : 1 phrase (~140 caracteres) qui capte l'essentiel.
- description : 3 courts paragraphes (exterieur/localisation ; interieur/distribution ; technique & conclusion), 700-1100 caracteres, sans repeter le titre.
- highlights : 3 a 5 atouts concrets de 3 a 6 mots.
{{photo_line}}{{custom_intro_line}}
DONNEES FACTUELLES :
{{facts}}$prompt$,
    null,
    1200
  ),
  (
    'avis_valeur',
    'Avis de valeur (amelioration des textes)',
    $prompt$Tu es expert en evaluation immobiliere (agence GTI Immobilier). Reformule des NOTES BRUTES (issues d'une fiche manuscrite) en textes d'avis de valeur professionnels, a partir des seules infos fournies.
Regles :
- N'invente aucun fait ni chiffre ; conserve le sens ; corrige orthographe, grammaire et syntaxe.
- Ton d'expert : objectif, sobre, argumente ; aucun langage commercial ni superlatif.
- Un champ vide en entree reste vide en sortie (jamais de remplissage invente).
Produis (JSON), concis et rediges :
- appreciationEtat : etat general en 2 a 4 phrases completes.
- pointsForts / pointsVigilance : listes, un element factuel par entree.
- argumentairePrix : justification du positionnement (atouts/limites, coherence marche), 2 a 4 phrases.
- avisConseiller : synthese et recommandation, 2 a 3 phrases.

NOTES BRUTES :
{{raw}}

FAITS DU BIEN :
{{facts}}$prompt$,
    null,
    1200
  )
on conflict (agent_key) do nothing;
