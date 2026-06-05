from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import settings
from .schemas import PerfilExtraido, ResultadoScoring, ResultadoSelfCorrection


_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
Sos un asistente de RRHH. Generás resúmenes concisos y accionables para reclutadores ocupados.
El mensaje debe ser claro, directo y en menos de 200 palabras. Usá emojis para facilitar lectura rápida.
"""),
    ("user", """
Generá un resumen para el reclutador sobre este candidato que superó el filtro automático.

Candidato: {nombre}
Email: {email}
Puntaje final: {puntaje}/100
Años de experiencia: {anios_experiencia}
Último cargo: {ultimo_cargo}
Tecnologías clave: {tecnologias}
Nivel de inglés: {nivel_ingles}

Por qué es excepcional:
{justificacion}

Puntos fuertes:
{puntos_fuertes}

Notas del auditor:
{notas_correccion}
""")
])


def generar_resumen_reclutador(
    perfil: PerfilExtraido,
    scoring: ResultadoScoring,
    correction: ResultadoSelfCorrection,
) -> str:
    """Genera el resumen abstractivo que se envía al reclutador por Telegram."""
    model = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3,
    )
    chain = _PROMPT | model | StrOutputParser()

    return chain.invoke({
        "nombre": perfil.nombre or "Sin nombre",
        "email": perfil.email or "Sin email",
        "puntaje": correction.puntaje_ajustado,
        "anios_experiencia": perfil.anios_experiencia or "?",
        "ultimo_cargo": perfil.ultimo_cargo or "No especificado",
        "tecnologias": ", ".join(perfil.tecnologias[:8]) if perfil.tecnologias else "No especificadas",
        "nivel_ingles": perfil.nivel_ingles or "No especificado",
        "justificacion": scoring.justificacion,
        "puntos_fuertes": "\n".join(f"• {p}" for p in scoring.puntos_fuertes),
        "notas_correccion": correction.notas_correccion,
    })