from .graph import compiled_graph
from .state import CandidateState


async def procesar_candidato(
    cv_bytes: bytes,
    client_id: str,
    chat_id: str,
) -> CandidateState:
    estado_inicial: CandidateState = {
        "cv_bytes": cv_bytes,
        "client_id": client_id,
        "chat_id": chat_id,
        "cv_texto": None,
        "cv_hash": None,
        "nombre": None,
        "email": None,
        "telefono": None,
        "anios_experiencia": None,
        "tecnologias": None,
        "ultimo_cargo": None,
        "nivel_ingles": None,
        "incompleto": None,
        "campos_faltantes": None,
        "completeness_retries": 0,
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

    estado_final = await compiled_graph.ainvoke(estado_inicial)
    return estado_final