from fastapi import APIRouter, Request, HTTPException
from telegram_bot.messenger import descargar_archivo, enviar_mensaje
from langgraph_flow import procesar_candidato
from observability import get_logger

router = APIRouter()
logger = get_logger("webhook")

DEFAULT_CLIENT_ID = "demo"

# Estado en memoria: chat_id → estado pendiente del candidato
# Guarda el cv_texto extraído mientras esperamos datos faltantes
sesiones_pendientes: dict[str, dict] = {}


@router.post("/telegram")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if "message" not in data:
        return {"status": "ok"}

    message = data["message"]
    chat_id = str(message["chat"]["id"])

    # ── El candidato envió un PDF ─────────────────────────────
    if "document" in message:
        doc = message["document"]

        if doc.get("mime_type") != "application/pdf":
            await enviar_mensaje(chat_id, "Por favor enviá tu CV en formato PDF 📄")
            return {"status": "ok"}

        await enviar_mensaje(chat_id, "Recibí tu CV ✅ Estoy analizándolo, en unos momentos te respondo...")

        try:
            cv_bytes = await descargar_archivo(doc["file_id"])
        except Exception as e:
            logger.error(f"Error descargando archivo: {e}")
            await enviar_mensaje(chat_id, "No pude descargar tu archivo 😔 Por favor intentá de nuevo.")
            return {"status": "ok"}

        try:
            estado_final = await procesar_candidato(
                cv_bytes=cv_bytes,
                client_id=DEFAULT_CLIENT_ID,
                chat_id=chat_id,
            )

            # Si quedó incompleto y hay reintentos disponibles, guardar sesión
            if estado_final.get("incompleto") and estado_final.get("campos_faltantes"):
                sesiones_pendientes[chat_id] = {
                    "cv_texto": estado_final.get("cv_texto"),
                    "cv_hash": estado_final.get("cv_hash"),
                    "campos_faltantes": estado_final.get("campos_faltantes"),
                    "completeness_retries": estado_final.get("completeness_retries", 0),
                }

            decision = estado_final.get('decision')
            logger.info(f"Pipeline completado (enriquecido) chat_id={chat_id} decision={decision}")
            if not decision:
                await enviar_mensaje(chat_id, "Hubo un problema procesando tu información 😔 Por favor enviá tu CV nuevamente.")
        except Exception as e:
            logger.error(f"Error en pipeline chat_id={chat_id}: {e}")
            await enviar_mensaje(chat_id, "Ocurrió un error procesando tu CV 😔 Intentá de nuevo en unos minutos.")

    # ── El candidato envió texto ──────────────────────────────
    elif "text" in message:
        texto = message["text"]

        if texto.startswith("/start"):
            await enviar_mensaje(
                chat_id,
                "¡Hola! 👋 Soy el sistema de evaluación de candidatos.\n\n"
                "Para postularte, simplemente *enviá tu CV en formato PDF*.\n"
                "El proceso es automático y recibirás una respuesta en minutos."
            )
            return {"status": "ok"}

        # ¿Hay una sesión pendiente para este chat_id?
        if chat_id in sesiones_pendientes:
            sesion = sesiones_pendientes.pop(chat_id)  # consumir la sesión

            # Enriquecer el cv_texto con la info que mandó el candidato
            cv_enriquecido = sesion["cv_texto"] + f"\n\n[DATOS ADICIONALES DEL CANDIDATO]\n{texto}"

            await enviar_mensaje(chat_id, "Gracias, completando tu evaluación... ⏳")

            try:
                import io
                # Reconvertir texto enriquecido a bytes para reusar el pipeline
                # Usamos un hack: guardamos el texto directamente en el estado
                from langgraph_flow.graph import compiled_graph
                from langgraph_flow.state import CandidateState

                estado_inicial: CandidateState = {
                    "cv_bytes": b"",
                    "client_id": DEFAULT_CLIENT_ID,
                    "chat_id": chat_id,
                    "cv_texto": cv_enriquecido,       # texto ya enriquecido
                    "cv_hash": sesion["cv_hash"],      # hash original para deduplicación
                    "nombre": None,
                    "email": None,
                    "telefono": None,
                    "anios_experiencia": None,
                    "tecnologias": None,
                    "ultimo_cargo": None,
                    "nivel_ingles": None,
                    "incompleto": None,
                    "campos_faltantes": None,
                    "completeness_retries": sesion.get("completeness_retries", 1),
                    "rag_score": None,
                    "rag_fragmentos": None,
                    "perfil_puesto": None,
                    "score_draft": None,
                    "score_reasoning": None,
                    "puntos_fuertes": None,
                    "puntos_debiles": None,
                    "score_final": None,
                    "correction_notes": None,
                    "decision": None,
                    "resumen_reclutador": None,
                    "error": None,
                }

                # Saltar ingest_cv y check_duplicate, ir directo a prescreening
                estado_final = await compiled_graph.ainvoke(
                    estado_inicial,
                    {"override_start": "prescreening"}  # LangGraph respeta el estado inicial
                )

                logger.info(f"Pipeline completado (enriquecido) chat_id={chat_id} decision={estado_final.get('decision')}")

            except Exception as e:
                logger.error(f"Error procesando datos adicionales chat_id={chat_id}: {e}")
                await enviar_mensaje(chat_id, "Ocurrió un error 😔 Por favor enviá tu CV nuevamente.")
        else:
            await enviar_mensaje(
                chat_id,
                "Para postularte enviá tu CV en formato PDF 📄"
            )

    return {"status": "ok"}