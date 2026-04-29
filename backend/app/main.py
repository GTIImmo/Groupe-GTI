from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.admin_users import router as admin_users_router
from .routers.appointments import router as appointments_router
from .routers.hektor_diffusion import router as hektor_diffusion_router
from .routers.notifications import router as notifications_router


app = FastAPI(title="GTI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "gti-backend",
        "version": "0.1.0",
    }


app.include_router(admin_users_router)
app.include_router(appointments_router)
app.include_router(hektor_diffusion_router)
app.include_router(notifications_router)
