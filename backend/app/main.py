from __future__ import annotations

import logging
import os
import subprocess
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("gti.backend")

from .routers.admin_users import router as admin_users_router
from .routers.annonces import router as annonces_router
from .routers.appointments import router as appointments_router
from .routers.dvf import router as dvf_router
from .routers.emails import router as emails_router
from .routers.geo import router as geo_router
from .routers.espace import router as espace_router
from .routers.google_workspace import router as google_workspace_router
from .routers.hektor_diffusion import router as hektor_diffusion_router
from .routers.notifications import router as notifications_router
from .routers.visite import router as visite_router


app = FastAPI(title="GTI Backend", version="0.1.0")


# ---------------------------------------------------------------------------
# QUEL COMMIT TOURNE ?   ajoute le 27/09/2026
#
# POURQUOI : ce jour-la, apres avoir pousse deux lots backend (G.14 le logo des emails,
# G.15-e les photos), je n'ai PAS PU PROUVER qu'ils etaient en ligne. /health rendait une
# version ECRITE EN DUR (« 0.1.0 »), qui ne bouge jamais ; il n'y a pas de render.yaml dans
# le depot, aucune cle API Render dans l'environnement, et les endpoints qui auraient montre
# le changement repondent 401. Autrement dit : AUCUN deploiement backend n'etait verifiable,
# ni celui-la, ni les suivants.
#
# Render pose RENDER_GIT_COMMIT et RENDER_GIT_BRANCH dans l'environnement de chaque
# deploiement : il suffit de les rendre. Le repli par git ne sert qu'en local (une image
# deployee n'emporte pas .git).
#
# ⚠ CALCULE UNE SEULE FOIS, AU CHARGEMENT. Lancer un sous-processus a chaque appel de
#   /health serait payer un fork pour une sonde appelee en boucle par le moniteur -- et un
#   git absent ferait echouer la sonde au lieu de l'informer.
# ⚠ ON RESTE COURT : la sonde check_gti_health tronque le corps a 500 caracteres pour ses
#   alertes. Le commit est donc rendu en 12 caracteres, pas en 40.
# ⚠ CE BLOC N'ENLEVE RIEN : ok, service et version restent, le moniteur ne lit que le 200.


def _commit_qui_tourne() -> str:
    marque = (os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_COMMIT") or "").strip()
    if not marque:
        try:
            marque = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=5, check=True,
            ).stdout.strip()
        except Exception:
            # Ni variable, ni git : on le DIT, on ne laisse pas croire a un commit.
            return "inconnu"
    return marque[:12] or "inconnu"


COMMIT = _commit_qui_tourne()
BRANCHE = (os.getenv("RENDER_GIT_BRANCH") or "").strip() or "inconnue"
DEMARRE_LE = datetime.now(timezone.utc).isoformat(timespec="seconds")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # Auth par token Bearer (en-tete Authorization), PAS par cookies -> pas besoin de
    # credentials. IMPORTANT : allow_credentials=True + allow_origins=["*"] produit une
    # reponse CORS INVALIDE (Access-Control-Allow-Origin: * avec Allow-Credentials: true),
    # rejetee par les navigateurs (parfois de facon intermittente) -> "Failed to fetch".
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Piege Starlette : une exception NON GEREE produit un 500 SANS en-tetes CORS
    # (ServerErrorMiddleware est au-dessus de CORSMiddleware) -> le navigateur affiche
    # "No Access-Control-Allow-Origin header present" au lieu de l'erreur. On garde le
    # 500 AVEC en-tete CORS, mais on NE FUITE PLUS le detail au client : le traceback
    # complet part dans les logs serveur (avec une ref), le client ne recoit qu'un
    # message generique + la ref pour retrouver l'erreur dans les logs.
    ref = uuid.uuid4().hex[:8]
    logger.error("Unhandled error [ref=%s] %s %s", ref, request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erreur interne du serveur (ref: {ref})"},
        headers={"Access-Control-Allow-Origin": "*"},
    )


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "gti-backend",
        "version": "0.1.0",
        # Le seul champ qui dit vraiment ce qui tourne : « version » est en dur.
        "commit": COMMIT,
        "branche": BRANCHE,
        "demarre_le": DEMARRE_LE,
    }


app.include_router(admin_users_router)
app.include_router(annonces_router)
app.include_router(appointments_router)
app.include_router(dvf_router)
app.include_router(emails_router)
app.include_router(geo_router)
app.include_router(espace_router)
app.include_router(google_workspace_router)
app.include_router(hektor_diffusion_router)
app.include_router(notifications_router)
app.include_router(visite_router)
