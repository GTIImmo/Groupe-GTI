-- ═══════════════════════════════════════════════════════════════════════════
-- 5b — LES DEUX CASES : L'IDENTITE D'UN COTE, LA CIBLE HEKTOR DE L'AUTRE
--                                                                21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- DECISION DE FREDERIC, 21/09 (option B). Le plan prevoyait de basculer les
-- 340 endroits de l'app qui RELIENT nos donnees vers le numero de l'app. Mesure
-- du 20/09 : 6 a 9 jours, et des echecs SILENCIEUX (un compteur affiche 0 au lieu
-- de lever). On inverse : on ne touche qu'aux 88 endroits qui VISENT Hektor.
--
--    app_contact_current.hektor_contact_id  ->  L'IDENTITE du contact.
--       Elle vaut le numero Hektor pour les 61 955 fiches existantes -- aucune
--       ne change. Pour un contact ne dans l'app, elle vaudra un numero A NOUS,
--       pris dans une plage que Hektor n'atteindra jamais (son plus grand
--       numero aujourd'hui : 605 433 ; la plage commence a 10 000 000).
--
--    app_contact_current.hektor_target_id   ->  LE NUMERO POUR VISER HEKTOR.
--       C'est la case que liront les workers. Vide = Hektor ne connait pas
--       encore ce contact, donc AUCUN travail ne part : il attend.
--
-- C'EST LE MECANISME QUE LE PLAN PREVOYAIT DEJA POUR LE JOUR J (E.4 / 6.2) :
-- « le serveur remplit les deux cases : les 24 tables qui portent le numero
-- Hektor continuent sans le savoir ». On l'avance, on ne l'invente pas.
--
-- CE QUE CE PATCH FAIT, ET RIEN DE PLUS (il est DORMANT) :
--   1. la colonne cible ;
--   2. la recopie, une fois, des 61 955 numeros existants ;
--   3. un declencheur qui la remplit tout seul pour les fiches neuves -- il y a
--      cinq ecrivains (run de nuit, relecture de fiche, RPC optimistes...) et
--      les faire tous penser a la remplir, c'est l'oublier quelque part ;
--   4. le distributeur de numeros de l'app ;
--   5. la vue de la sonde.
-- AUCUN worker, AUCUN ecran ne lit encore la nouvelle case : c'est le lot
-- suivant. Tant qu'elle n'est pas lue, ce patch ne change RIEN au comportement.
--
-- RETOUR ARRIERE :
--   drop trigger trg_app_contact_current_cible on public.app_contact_current;
--   drop function public.app_contact_remplir_cible();
--   drop view public.app_v_contacts_sans_cible;
--   drop sequence public.app_contact_identite_seq;
--   alter table public.app_contact_current drop column hektor_target_id;
-- ═══════════════════════════════════════════════════════════════════════════

-- ── 1. LA CASE CIBLE ───────────────────────────────────────────────────────
alter table public.app_contact_current add column if not exists hektor_target_id text;

comment on column public.app_contact_current.hektor_target_id is
  '5b 21/09/2026 : LE NUMERO POUR VISER HEKTOR. Les workers lisent CETTE case, jamais hektor_contact_id (qui est devenue l''identite du contact). Vide = Hektor ne connait pas ce contact -> le travail attend au lieu de partir.';

comment on column public.app_contact_current.hektor_contact_id is
  '5b 21/09/2026 : L''IDENTITE du contact dans l''app. Vaut le numero Hektor pour les fiches venues de lui ; vaudra un numero >= 10 000 000 pour un contact ne dans l''app (app_contact_identite_seq). ⚠ NE PAS l''envoyer a Hektor : utiliser hektor_target_id.';

-- ── 2. LA RECOPIE, UNE FOIS ────────────────────────────────────────────────
-- Recopie, pas renumerotation : aucune valeur existante ne change. On exclut par
-- principe la plage reservee -- elle est vide aujourd'hui, elle ne le sera plus.
update public.app_contact_current
   set hektor_target_id = hektor_contact_id
 where hektor_target_id is null
   and hektor_contact_id ~ '^[0-9]+$'
   and hektor_contact_id::bigint < 10000000;

-- ── 3. LE DECLENCHEUR : LA CASE SE REMPLIT TOUTE SEULE ─────────────────────
-- Il ne fait qu'AJOUTER : il ne modifie jamais une cible deja posee, et il ne
-- touche pas a l'identite. Un contact ne dans l'app (>= 10 000 000) n'en recoit
-- pas -- c'est exactement le but : tant que Hektor ne l'a pas cree, il n'y a
-- rien a viser chez lui.
create or replace function public.app_contact_remplir_cible()
 returns trigger
 language plpgsql
as $function$
begin
  if new.hektor_target_id is null
     and new.hektor_contact_id ~ '^[0-9]+$'
     and new.hektor_contact_id::bigint < 10000000 then
    new.hektor_target_id := new.hektor_contact_id;
  end if;
  return new;
end
$function$;

drop trigger if exists trg_app_contact_current_cible on public.app_contact_current;
create trigger trg_app_contact_current_cible
  before insert or update on public.app_contact_current
  for each row execute function public.app_contact_remplir_cible();

-- ── 4. LE DISTRIBUTEUR DE NUMEROS DE L'APP ─────────────────────────────────
-- Depart a 10 000 000, dans un couloir que Hektor n'atteindra jamais : son plus
-- grand numero est 605 433, et il en cree environ 15 par jour -- soit plus de
-- 1 700 ans avant la collision. Personne ne l'appelle encore : la creation
-- depuis l'app est le lot L4.
create sequence if not exists public.app_contact_identite_seq
  as bigint start with 10000000 minvalue 10000000 no cycle;

grant usage, select on sequence public.app_contact_identite_seq to service_role, authenticated;

-- ── 5. LA SONDE ────────────────────────────────────────────────────────────
-- « Aucun contact venu de Hektor ne doit rester sans sa case cible. » Si cette
-- vue remonte, c'est qu'un ecrivain a echappe au declencheur -- et les travaux
-- de ce contact ne partiraient plus.
create or replace view public.app_v_contacts_sans_cible as
  select hektor_contact_id, nom, prenom, date_maj
    from public.app_contact_current
   where hektor_target_id is null
     and hektor_contact_id ~ '^[0-9]+$'
     and hektor_contact_id::bigint < 10000000;

comment on view public.app_v_contacts_sans_cible is
  '5b 21/09/2026 : contacts venus de Hektor dont la case cible est vide. Seuil de la sonde data.contacts_sans_cible : 0.';

grant select on public.app_v_contacts_sans_cible to service_role, authenticated;
