@echo off
REM ============================================================================
REM Ingestion semestrielle GTI : DVF + Georisques + INSEE + Loyers (donnees pre-
REM chargees lues a la generation de l'avis de valeur). Lance par le Planificateur
REM de taches Windows 2x/an (28 avril : DVF S2 N-1 ; 28 octobre : DVF S1 N).
REM (Les loyers ANIL et le zonage ABC changent ~1x/an ; re-ingerer 2x/an est
REM  idempotent -- pensez a bumper MILLESIME + URLs dans ingest_loyers.py a la
REM  sortie annuelle de la Carte des loyers.)
REM ============================================================================
setlocal
set PY=C:\Python314\python.exe
set ROOT=C:\Hektor\Projet
cd /d %ROOT%
if not exist logs mkdir logs

echo ==================================================================>> logs\ingest_biannual.log
echo [%DATE% %TIME%] DEBUT ingestion semestrielle>> logs\ingest_biannual.log

echo [%DATE% %TIME%] DVF...>> logs\ingest_biannual.log
"%PY%" backend\scripts\ingest_dvf.py >> logs\ingest_dvf.log 2>&1

echo [%DATE% %TIME%] Georisques...>> logs\ingest_biannual.log
"%PY%" backend\scripts\ingest_georisques.py >> logs\ingest_georisques.log 2>&1

echo [%DATE% %TIME%] INSEE...>> logs\ingest_biannual.log
"%PY%" backend\scripts\ingest_insee.py >> logs\ingest_insee.log 2>&1

echo [%DATE% %TIME%] Loyers...>> logs\ingest_biannual.log
"%PY%" backend\scripts\ingest_loyers.py >> logs\ingest_loyers.log 2>&1

echo [%DATE% %TIME%] FIN ingestion semestrielle>> logs\ingest_biannual.log
endlocal
