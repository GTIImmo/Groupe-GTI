-- ═══════════════════════════════════════════════════════════════════════════
-- LE BALAYAGE DES LIGNES PROVISOIRES COUVRE ENFIN LES QUATRE TABLES
-- 25/09/2026 -- trouve par une question de Frederic : « pourquoi ces deux
-- contacts n'ont pas de relations dans l'app ? »
-- ═══════════════════════════════════════════════════════════════════════════
--
-- CE QU'IL SE PASSAIT. Quand on cree un objet depuis l'app, une ligne
-- « provisoire » s'affiche tout de suite (le calque optimiste), puis disparait
-- quand l'objet reel arrive. Un balayage tourne CHAQUE MINUTE pour nettoyer ce
-- qui resterait -- mais il ne traitait QUE `app_annonce_provisional`.
--
--   annonces    nettoyees          0 ligne en attente
--   contacts    JAMAIS nettoyees   2 lignes depuis le 18/09
--   recherches  JAMAIS nettoyees   2 lignes depuis le 31/08  (25 jours)
--   relations   JAMAIS nettoyees   0 ligne
--
-- LE CAS VECU : deux contacts d'essai crees le 18/09 (605414, 605429), reussis
-- chez Hektor, puis SUPPRIMES chez Hektor le 21/09 par le menage des essais L4-b.
-- Le contact reel n'arrivera donc jamais dans l'app -- et la ligne provisoire,
-- que rien ne purge, reste affichee « En creation... » POUR TOUJOURS.
--
-- LA REGLE, PLUS PRUDENTE QUE CELLE DES ANNONCES. On ne peut pas reprendre telle
-- quelle la regle « linked depuis 1 h -> on efface » : pour une ANNONCE, le
-- rafraichissement la ramene dans la minute ; pour un CONTACT, si la ligne
-- partait avant que le contact reel soit la, l'utilisateur le verrait
-- DISPARAITRE de son annuaire jusqu'au run de nuit. On efface donc :
--   (a) des que l'objet reel est LA (reconcilie) -- sans attendre ;
--   (b) sinon, au bout de 24 h -- le run de nuit est passe, plus rien ne viendra.
-- Et une ligne restee « en cours » plus de 15 min devient une ERREUR VISIBLE,
-- au lieu de tourner indefiniment.
--
-- ⚠ ON N'EFFACE JAMAIS UNE LIGNE « EN COURS » : une creation en vol se termine.
-- ⚠ Les etats de depart different d'une table a l'autre ('creating' pour
--   l'annonce, 'pending' pour le contact) : on raisonne donc par la NEGATIVE
--   (tout ce qui n'est ni 'linked' ni 'error' est en cours).
--
-- RETOUR ARRIERE : reposer l'ancienne version (donnee en fin de fichier).
-- ═══════════════════════════════════════════════════════════════════════════

create or replace function public.app_sweep_stale_provisionals()
returns void
language plpgsql
security definer
set search_path to 'public'
as $function$
begin
  -- ── 1) CE QUI TRAINE « EN COURS » DEVIENT UNE ERREUR VISIBLE ─────────────
  update app_annonce_provisional
     set status = 'error',
         error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (le bien n''a pas été confirmé dans le délai)'),
         updated_at = now()
   where status not in ('linked', 'error') and created_at < now() - interval '15 minutes';

  update app_contact_provisional
     set status = 'error',
         error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (le contact n''a pas été confirmé dans le délai)'),
         updated_at = now()
   where status not in ('linked', 'error') and created_at < now() - interval '15 minutes';

  update app_search_provisional
     set status = 'error',
         error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (la recherche n''a pas été confirmée dans le délai)'),
         updated_at = now()
   where status not in ('linked', 'error') and created_at < now() - interval '15 minutes';

  update app_relation_provisional
     set status = 'error',
         error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (le lien n''a pas été confirmé dans le délai)'),
         updated_at = now()
   where status not in ('linked', 'error') and created_at < now() - interval '15 minutes';

  -- ── 2) PURGE : l'objet reel est LA, ou plus rien ne viendra ───────────────
  -- (a) reconcilie : le bien / le contact existe dans la couche -> la ligne
  --     provisoire n'a plus d'objet, on l'efface sans attendre.
  delete from app_annonce_provisional p
   where p.status = 'linked'
     and exists (select 1 from app_dossier_current d
                  where d.hektor_annonce_id::text = p.hektor_annonce_id::text);

  delete from app_contact_provisional p
   where p.status = 'linked'
     and exists (select 1 from app_contact_current c
                  where c.hektor_contact_id = p.hektor_contact_id
                     or c.hektor_target_id  = p.hektor_contact_id);

  -- (b) le filet : passe 24 h, le run de nuit est passe. Ce qui n'est toujours
  --     pas reconcilie ne le sera jamais (objet supprime chez Hektor, essai
  --     abandonne...). Vaut pour les quatre tables, y compris la recherche et
  --     la relation, qui n'ont pas de cle simple a rapprocher de la couche.
  delete from app_annonce_provisional  where status = 'linked' and updated_at < now() - interval '24 hours';
  delete from app_contact_provisional  where status = 'linked' and updated_at < now() - interval '24 hours';
  delete from app_search_provisional   where status = 'linked' and updated_at < now() - interval '24 hours';
  delete from app_relation_provisional where status = 'linked' and updated_at < now() - interval '24 hours';

  -- (c) les erreurs anciennes : l'utilisateur a eu le temps de les voir.
  delete from app_annonce_provisional  where status = 'error' and updated_at < now() - interval '24 hours';
  delete from app_contact_provisional  where status = 'error' and updated_at < now() - interval '24 hours';
  delete from app_search_provisional   where status = 'error' and updated_at < now() - interval '24 hours';
  delete from app_relation_provisional where status = 'error' and updated_at < now() - interval '24 hours';
end;
$function$;

-- Le balayage tourne deja chaque minute (cron « app_sweep_stale_provisionals ») :
-- rien a programmer. Les 4 lignes fantomes (18/09 et 31/08) partiront au premier
-- passage, par la regle (b).

-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE -- l'ancienne version, exactement
-- ═══════════════════════════════════════════════════════════════════════════
-- create or replace function public.app_sweep_stale_provisionals()
-- returns void language plpgsql security definer set search_path to 'public'
-- as $function$
-- begin
--   update app_annonce_provisional
--      set status = 'error',
--          error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (le bien n''a pas été confirmé dans le délai)'),
--          updated_at = now()
--    where status = 'creating' and created_at < now() - interval '15 minutes';
--   delete from app_annonce_provisional
--    where (status = 'linked' and updated_at < now() - interval '1 hour')
--       or (status = 'error'  and updated_at < now() - interval '24 hours');
-- end;
-- $function$;
