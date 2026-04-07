truncate table
    public.app_summary_snapshot,
    public.app_dossier_detail_v1,
    public.app_work_item_v1,
    public.app_filter_catalog_v1,
    public.app_dossier_v1,
    public.app_sync_run,
    public.app_dossier_detail_current,
    public.app_work_item_current,
    public.app_filter_catalog_current_store,
    public.app_dossier_current,
    public.app_delta_run
restart identity cascade;
