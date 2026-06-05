from typing import Optional, TypedDict


class CandidateState(TypedDict):
    cv_bytes: bytes
    client_id: str
    chat_id: str
    cv_texto: Optional[str]
    cv_hash: Optional[str]
    nombre: Optional[str]
    email: Optional[str]
    telefono: Optional[str]
    anios_experiencia: Optional[int]
    tecnologias: Optional[list]
    ultimo_cargo: Optional[str]
    nivel_ingles: Optional[str]
    incompleto: Optional[bool]
    campos_faltantes: Optional[list]
    completeness_retries: int
    rag_score: Optional[float]
    rag_fragmentos: Optional[str]
    perfil_puesto: Optional[str]
    score_draft: Optional[int]
    score_reasoning: Optional[str]
    puntos_fuertes: Optional[list]
    puntos_debiles: Optional[list]
    score_final: Optional[int]
    correction_notes: Optional[str]
    decision: Optional[str]
    resumen_reclutador: Optional[str]
    error: Optional[str]