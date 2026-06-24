-- Lot 2 — Email estimation : autorise le type d'événement 'download' (téléchargement
-- de l'avis de valeur, signal fort) dans app_email_event.type. Additif : reprend les
-- 5 types live (open/like/pass/visite/unsub) + ajoute 'download'. Rien retiré.

alter table public.app_email_event drop constraint if exists app_email_event_type_check;
alter table public.app_email_event add constraint app_email_event_type_check
  check (type = any (array['open','like','pass','visite','unsub','download']::text[]));
