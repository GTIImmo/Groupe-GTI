begin;

alter table public.app_google_workspace_action_log
drop constraint if exists app_google_workspace_action_log_action_type_check;

alter table public.app_google_workspace_action_log
add constraint app_google_workspace_action_log_action_type_check
check (action_type in (
    'calendar.freebusy',
    'calendar.event.create',
    'calendar.event.update',
    'calendar.event.delete',
    'gmail.send',
    'gmail.metadata.search',
    'gmail.readonly.thread',
    'contacts.read'
));

comment on column public.app_google_workspace_action_log.action_type
is 'Type d action Google Workspace: disponibilite agenda, creation/modification/suppression evenement, envoi Gmail, lecture future, contacts.';

commit;
