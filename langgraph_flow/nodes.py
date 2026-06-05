from .state import CandidateState
from ingestion import extraer_texto_pdf, calcular_hash
from agents import (
    agente_prescreening,
    agente_scoring,
    agente_selfcorrection,
    generar_resumen_reclutador,
    PerfilExtraido,
    ResultadoScoring,
    ResultadoSelfCorrection,
)
from rag import buscar_similitud
from database import candidate_exists, create_candidate, get_session
from config import settings, get_client
from telegram_bot.messenger import enviar_mensaje


async def node_ingest_cv(state: CandidateState) -> dict:
    # Si cv_texto ya viene cargado (sesión enriquecida), no reextraer
    if state.get("cv_texto"):
        return {}
    try:
        cv_texto = extraer_texto_pdf(state["cv_bytes"])
        cv_hash = calcular_hash(cv_texto)
        return {"cv_texto": cv_texto, "cv_hash": cv_hash}
    except Exception as e:
        return {"error": f"Error extrayendo PDF: {str(e)}"}


async def node_check_duplicate(state: CandidateState) -> dict:
    # Si completeness_retries > 0 es una sesión de reintento, no verificar duplicado
    if state.get("completeness_retries", 0) > 0:
        return {}
    db = next(get_session())
    if candidate_exists(db, state["cv_hash"]):
        return {"decision": "duplicate"}
    return {}


async def node_prescreening(state: CandidateState) -> dict:
    try:
        perfil = agente_prescreening(state["cv_texto"])
        return {
            "nombre": perfil.nombre,
            "email": perfil.email,
            "telefono": perfil.telefono,
            "anios_experiencia": perfil.anios_experiencia,
            "tecnologias": perfil.tecnologias,
            "ultimo_cargo": perfil.ultimo_cargo,
            "nivel_ingles": perfil.nivel_ingles,
            "incompleto": perfil.incompleto,
            "campos_faltantes": perfil.campos_faltantes,
        }
    except Exception as e:
        return {"error": f"Error en pre-screening: {str(e)}"}


async def node_ask_missing_info(state: CandidateState) -> dict:
    faltantes = state.get("campos_faltantes", [])
    lista = "\n".join(f"• {f}" for f in faltantes)
    mensaje = (
        f"Hola! Recibí tu CV ✅\n\n"
        f"Para completar tu evaluación necesito:\n{lista}\n\n"
        f"Por favor respondé en un solo mensaje."
    )
    await enviar_mensaje(state["chat_id"], mensaje)
    retries = state.get("completeness_retries", 0)
    return {"completeness_retries": retries + 1, "incompleto": False}


async def node_rag_evaluation(state: CandidateState) -> dict:
    try:
        client_config = get_client(state["client_id"])
        collection = client_config["chroma_collection"]
        rag_score, rag_fragmentos = buscar_similitud(collection, state["cv_texto"])
        return {"rag_score": rag_score, "rag_fragmentos": rag_fragmentos}
    except Exception as e:
        return {"rag_score": 0.0, "rag_fragmentos": f"Error RAG: {str(e)}"}


async def node_scoring(state: CandidateState) -> dict:
    try:
        perfil = PerfilExtraido(
            nombre=state.get("nombre"),
            email=state.get("email"),
            telefono=state.get("telefono"),
            anios_experiencia=state.get("anios_experiencia"),
            tecnologias=state.get("tecnologias", []),
            ultimo_cargo=state.get("ultimo_cargo"),
            nivel_ingles=state.get("nivel_ingles"),
        )
        resultado = agente_scoring(
            cv_texto=state["cv_texto"],
            perfil=perfil,
            perfil_puesto=state.get("rag_fragmentos", ""),
            rag_score=state.get("rag_score", 0.0),
            rag_fragmentos=state.get("rag_fragmentos", ""),
        )
        return {
            "score_draft": resultado.puntaje,
            "score_reasoning": resultado.justificacion,
            "puntos_fuertes": resultado.puntos_fuertes,
            "puntos_debiles": resultado.puntos_debiles,
        }
    except Exception as e:
        return {"error": f"Error en scoring: {str(e)}"}


async def node_selfcorrection(state: CandidateState) -> dict:
    try:
        scoring_draft = ResultadoScoring(
            puntaje=state["score_draft"],
            justificacion=state["score_reasoning"],
            puntos_fuertes=state.get("puntos_fuertes", []),
            puntos_debiles=state.get("puntos_debiles", []),
        )
        resultado = agente_selfcorrection(
            cv_texto=state["cv_texto"],
            scoring_draft=scoring_draft,
        )
        return {
            "score_final": resultado.puntaje_ajustado,
            "correction_notes": resultado.notas_correccion,
        }
    except Exception as e:
        return {"score_final": state.get("score_draft", 0), "correction_notes": f"Error: {str(e)}"}


async def node_notify_recruiter(state: CandidateState) -> dict:
    try:
        perfil = PerfilExtraido(
            nombre=state.get("nombre"),
            email=state.get("email"),
            telefono=state.get("telefono"),
            anios_experiencia=state.get("anios_experiencia"),
            tecnologias=state.get("tecnologias", []),
            ultimo_cargo=state.get("ultimo_cargo"),
            nivel_ingles=state.get("nivel_ingles"),
        )
        scoring = ResultadoScoring(
            puntaje=state["score_draft"],
            justificacion=state["score_reasoning"],
            puntos_fuertes=state.get("puntos_fuertes", []),
            puntos_debiles=state.get("puntos_debiles", []),
        )
        correction = ResultadoSelfCorrection(
            puntaje_ajustado=state["score_final"],
            hubo_ajuste=state["score_final"] != state["score_draft"],
            notas_correccion=state["correction_notes"],
        )
        resumen = generar_resumen_reclutador(perfil, scoring, correction)

        client_config = get_client(state["client_id"])
        recruiter_chat_id = client_config.get("recruiter_chat_id") or settings.recruiter_chat_id
        await enviar_mensaje(recruiter_chat_id, f"🎯 *Candidato aprobado*\n\n{resumen}")
        await enviar_mensaje(
            state["chat_id"],
            "¡Excelentes noticias! 🎉 Tu perfil fue seleccionado. Un reclutador te contactará pronto."
        )
        return {"decision": "approved", "resumen_reclutador": resumen}
    except Exception as e:
        return {"error": f"Error notificando reclutador: {str(e)}"}


async def node_talent_bank(state: CandidateState) -> dict:
    try:
        db = next(get_session())
        create_candidate(db, {
            "cv_hash": state["cv_hash"],
            "client_id": state["client_id"],
            "nombre": state.get("nombre"),
            "email": state.get("email"),
            "telefono": state.get("telefono"),
            "anios_experiencia": state.get("anios_experiencia"),
            "tecnologias": state.get("tecnologias", []),
            "ultimo_cargo": state.get("ultimo_cargo"),
            "nivel_ingles": state.get("nivel_ingles"),
            "rag_score": state.get("rag_score"),
            "score_draft": state.get("score_draft"),
            "score_final": state.get("score_final"),
            "score_reasoning": state.get("score_reasoning"),
            "correction_notes": state.get("correction_notes"),
            "decision": "talent_bank",
        })
        await enviar_mensaje(
            state["chat_id"],
            "Gracias por postularte 🙏 Tu perfil quedó en nuestro banco de talentos. ¡Mucho éxito!"
        )
        return {"decision": "talent_bank"}
    except Exception as e:
        return {"error": f"Error guardando en banco de talentos: {str(e)}"}


async def node_handle_duplicate(state: CandidateState) -> dict:
    await enviar_mensaje(
        state["chat_id"],
        "Ya recibimos tu CV anteriormente 📋 Te contactaremos si tu perfil es el indicado."
    )
    return {}


async def node_handle_error(state: CandidateState) -> dict:
    await enviar_mensaje(
        state["chat_id"],
        "Hubo un problema procesando tu CV 😔 Por favor intentá de nuevo en unos minutos."
    )
    return {}