from fastapi import APIRouter, Header, HTTPException, Body
from pydantic import BaseModel
from telegram_bot.messenger import registrar_webhook
from rag.load_job_profile import main as load_profile_cli
from database.models import init_db, SessionLocal
from database.crud import get_talent_bank
import os

router = APIRouter(prefix="/admin")

ADMIN_KEY = os.getenv("ADMIN_API_KEY", "changeme")


def check_auth(x_api_key: str = Header(None)):
    if x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")


class WebhookRequest(BaseModel):
    url: str


class JobProfileRequest(BaseModel):
    client_id: str
    position_name: str
    profile_text: str


@router.post("/register-webhook")
async def register_webhook(body: WebhookRequest, x_api_key: str = Header(None)):
    check_auth(x_api_key)
    result = await registrar_webhook(body.url)
    return result


@router.post("/load-job-profile")
async def load_job_profile(body: JobProfileRequest, x_api_key: str = Header(None)):
    """Carga un nuevo perfil de puesto vía API REST."""
    check_auth(x_api_key)
    from rag.vector_store import cargar_job_profile
    from database.crud import create_job_profile
    from config.clients import get_client

    client_config = get_client(body.client_id)
    collection_name = client_config["chroma_collection"]

    cargar_job_profile(
        collection_name=collection_name,
        profile_text=body.profile_text,
        metadata={"client_id": body.client_id, "position": body.position_name},
    )

    db = SessionLocal()
    create_job_profile(
        db=db,
        client_id=body.client_id,
        position_name=body.position_name,
        profile_text=body.profile_text,
        chroma_collection=collection_name,
    )
    db.close()

    return {"status": "ok", "collection": collection_name}


@router.get("/talent-bank/{client_id}")
async def talent_bank(client_id: str, x_api_key: str = Header(None)):
    """Lista los candidatos en el banco de talentos de un cliente."""
    check_auth(x_api_key)
    db = SessionLocal()
    candidates = get_talent_bank(db, client_id)
    db.close()
    return [
        {
            "nombre": c.nombre,
            "email": c.email,
            "score_final": c.score_final,
            "ultimo_cargo": c.ultimo_cargo,
            "tecnologias": c.tecnologias,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in candidates
    ]