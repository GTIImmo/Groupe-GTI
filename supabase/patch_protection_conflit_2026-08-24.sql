-- =====================================================================
-- Tache 0.8 -- la protection d'un conflit cesse d'etre annulee
-- Date : 2026-08-24
-- Appliquee via la migration `protection_conflit_survit_a_la_mise_en_file`
--
-- LE DEFAUT, present a l'IDENTIQUE dans les trois fonctions de mise en file --
-- app_annonce_, app_contact_ et app_search_enqueue_due_pushes :
--
--     delete from public.app_XXX_pending p
--       using public.app_console_job j
--      where p.push_job_id = j.id and j.status = 'done';     <-- aucun filtre sur le conflit
--
-- Or un blocage anti-ecrasement marque le travail 'done'. Le worker journalise
-- logJob(..., "done", "... ecriture bloquee (anti-ecrasement)") PUIS renvoie
-- { status: "held_conflict" } -- console_job_worker.js lignes 9192-9197, 11430-11435,
-- 11948-11956. La ligne d'attente est donc supprimee DANS LA MINUTE qui suit le blocage.
--
-- ET LES TROIS FONCTIONS AVAIENT ECRIT LA PROTECTION, juste en dessous :
--
--     delete from public.app_XXX_pending
--      where conflict = true and updated_at < now() - interval '24 hours';
--
-- Elle ne servait JAMAIS : la ligne etait deja partie. La protection existait, et elle
-- etait annulee par la suppression qui la precede. Le meme patron, copie trois fois.
--
-- CE QUE CA A COUTE, mesure : le contact 602197. Un negociateur affine une recherche a
-- 120 000 EUR le 21/08 a 12:27. Le garde-fou bloque. Le travail se marque 'done'. La ligne
-- disparait. Le run de nuit rapporte la valeur de Hektor. Les trois supports -- l'app, le
-- serveur, le miroir -- disent aujourd'hui prix_min = 0. La saisie n'existe nulle part.
-- Et PERSONNE n'avait rien modifie dans Hektor : le garde-fou avait bloque parce que la
-- modale n'exprime que 7 criteres sur 12, pas parce qu'il y avait un conflit.
--
-- LE CORRECTIF : `and p.conflict = false`. On ne change aucune regle -- on cesse d'en
-- annuler une.
--
-- POURQUOI MAINTENANT ET PAS A L'ETAPE 2 : 0 ligne en attente, 0 en conflit sur les trois
-- tables. Le rayon d'action est nul. Attendre reviendrait a poser le garde-fou le jour ou
-- les negociateurs en dependent ; on le pose avant, et on le laisse faire ses preuves.
--
-- LE MOTIF A ETE VERIFIE, PAS DEVINE. La migration leve une exception si le remplacement
-- ne change rien, s'il s'applique deux fois, ou si le compte n'est pas exactement 3.
-- Aucun correctif applique en silence.
--
-- VERIFIE APRES, par un essai controle sur deux identifiants inexistants :
--     -999  conflict = true   -> SURVIT au passage de la mise en file
--     -998  conflict = false  -> supprimee, le menage normal fonctionne toujours
-- Lignes d'essai retirees ; etat final 0/0 sur les trois tables.
--
-- A SURVEILLER : le nombre de lignes en conflit. Il etait fatalement a zero puisqu'elles
-- etaient effacees. S'il monte, c'est une INFORMATION et non une panne -- ce sont des
-- saisies qu'on perdait sans le savoir. L'accumulation est bornee par la regle des 24 h :
-- rien ne peut geler indefiniment.
--
-- RETOUR ARRIERE : retirer `and p.conflict = false` des trois fonctions.
-- =====================================================================

do $$
declare
  r record;
  src text;
  nouveau text;
  motif text;
  n int := 0;
begin
  for r in
    select p.oid, p.proname,
           replace(p.proname, '_enqueue_due_pushes', '_pending') as table_attente
      from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
     where ns.nspname = 'public'
       and p.proname in ('app_annonce_enqueue_due_pushes',
                         'app_contact_enqueue_due_pushes',
                         'app_search_enqueue_due_pushes')
  loop
    src := pg_get_functiondef(r.oid);
    motif := '(delete\s+from\s+public\.' || r.table_attente ||
             '\s+p\s+using\s+public\.app_console_job\s+j\s+where\s+p\.push_job_id\s*=\s*j\.id' ||
             '\s+and\s+j\.status\s*=\s*''done'')';
    nouveau := regexp_replace(src, motif, '\1 and p.conflict = false', 'i');

    if nouveau = src then
      raise exception 'MOTIF INTROUVABLE dans % -- rien n''a ete modifie', r.proname;
    end if;
    if nouveau ~* 'conflict = false[^;]*conflict = false' then
      raise exception 'DOUBLE APPLICATION detectee dans % -- annule', r.proname;
    end if;

    execute nouveau;
    n := n + 1;
  end loop;

  if n <> 3 then
    raise exception 'attendu 3 fonctions, % corrigee(s)', n;
  end if;
  raise notice 'protection du conflit retablie sur % fonctions', n;
end $$;
