from pydantic import BaseModel, Field
from typing import Optional


class PerfilExtraido(BaseModel):
    """Salida del Agente 1 — Pre-screening."""
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    anios_experiencia: Optional[int] = None
    tecnologias: list[str] = Field(default_factory=list)
    ultimo_cargo: Optional[str] = None
    nivel_ingles: Optional[str] = None   # "nativo", "avanzado", "intermedio", "básico", "no especificado"
    incompleto: bool = False             # True si faltan campos críticos
    campos_faltantes: list[str] = Field(default_factory=list)


class ResultadoScoring(BaseModel):
    """Salida del Agente 2 — Scoring crítico."""
    puntaje: int = Field(ge=1, le=100)
    justificacion: str
    puntos_fuertes: list[str] = Field(default_factory=list)
    puntos_debiles: list[str] = Field(default_factory=list)
    analisis_carta: Optional[str] = None   # Resultado del sentiment sobre la carta de presentación


class ResultadoSelfCorrection(BaseModel):
    """Salida del Agente 3 — Self-Correction."""
    puntaje_ajustado: int = Field(ge=1, le=100)
    hubo_ajuste: bool
    notas_correccion: str