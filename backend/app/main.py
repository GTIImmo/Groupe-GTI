from __future__ import annotations

import logging
import uuid

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
