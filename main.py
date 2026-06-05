import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database.models import init_db
from observability import setup_langsmith, get_logger
from api.routers.webhook import router as webhook_router
from api.routers.admin import router as admin_router

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup y shutdown de la aplicación."""
    # Startup
    logger.info("Iniciando TalentFilter AI...")

    # Crear directorio de datos si no existe
    os.makedirs("./data/chroma", exist_ok=True)

    # Inicializar base de datos SQLite
    init_db()
    logger.info("Base de datos inicializada.")

    # Configurar LangSmith
    setup_langsmith()
    logger.info("LangSmith configurado.")

    logger.info("TalentFilter AI listo ✓")
    yield

    # Shutdown
    logger.info("Apagando TalentFilter AI...")


app = FastAPI(
    title="TalentFilter AI",
    description="Agente de headhunting autónomo — pipeline de evaluación de candidatos.",
    version="1.0.0",
    lifespan=lifespan,
)

# Routers
app.include_router(webhook_router, prefix="/webhook", tags=["Telegram"])
app.include_router(admin_router, tags=["Admin"])


@app.get("/health")
async def health():
    """Endpoint de health check para Cloudflare / monitoreo."""
    return {"status": "ok", "service": "talentfilter-ai"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)