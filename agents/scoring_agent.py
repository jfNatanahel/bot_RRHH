from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config import settings
from .schemas import PerfilExtraido, ResultadoScoring

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
Sos un Headhunter Senior con 15 años de experiencia. Evaluás candidatos con criterio técnico riguroso.

Tu tarea: asignar un puntaje del 1 al 100 al candidato usando Chain of Thought (CoT).

PROCESO OBLIGATORIO — razonás en este orden antes de dar el número:
1. Analizar la coincidencia técnica (tecnologías del CV vs tecnologías requeridas en el perfil).
2. Evaluar la seniority real (años de experiencia + progresión de carrera + último cargo).
3. Detectar red flags (gaps de empleo, cargos decrecientes, tecnologías desactualizadas sin contexto).
4. Evaluar el nivel de inglés requerido vs declarado.
5. Si hay carta de presentación, analizá si la motivación parece genuina o generada por IA.
6. Calcular el puntaje final ponderando los puntos anteriores.

Criterio de puntaje:
- 90-100: candidato excepcional, supera todos los requisitos.
- 75-89: candidato sólido, cumple la mayoría de requisitos.
- 60-74: candidato aceptable con brechas importantes.
- 40-59: candidato débil, muchas brechas.
- 1-39: no califica.

Devolvé SOLO un JSON válido:
{{
  "puntaje": número del 1 al 100,
  "justificacion": "razonamiento completo paso a paso",
  "puntos_fuertes": ["lista de fortalezas concretas"],
  "puntos_debiles": ["lista de debilidades concretas"],
  "analisis_carta": "análisis de motivación o null si no hay carta"
}}
"""),
    ("user", """
PERFIL DE PUESTO BUSCADO:
{perfil_puesto}

SCORE DE SIMILITUD SEMÁNTICA (RAG, escala 0-1, más alto = más similar):
{rag_score}

FRAGMENTOS RELEVANTES DEL PERFIL QUE COINCIDEN O NO CON EL CV:
{rag_fragmentos}

PERFIL ESTRUCTURADO DEL CANDIDATO:
Nombre: {nombre}
Años de experiencia: {anios_experiencia}
Tecnologías: {tecnologias}
Último cargo: {ultimo_cargo}
Nivel de inglés: {nivel_ingles}

CV COMPLETO:
{cv_texto}
""")
])


def agente_scoring(
    cv_texto: str,
    perfil: PerfilExtraido,
    perfil_puesto: str,
    rag_score: float,
    rag_fragmentos: str,
) -> ResultadoScoring:
    """
    Agente 2: evalúa al candidato con Chain of Thought y devuelve un puntaje 1-100.
    """
    model = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )
    parser = JsonOutputParser()
    chain = _PROMPT | model | parser

    raw = chain.invoke({
        "perfil_puesto": perfil_puesto,
        "rag_score": f"{rag_score:.3f}",
        "rag_fragmentos": rag_fragmentos,
        "nombre": perfil.nombre or "No especificado",
        "anios_experiencia": perfil.anios_experiencia or "No especificado",
        "tecnologias": ", ".join(perfil.tecnologias) if perfil.tecnologias else "No especificadas",
        "ultimo_cargo": perfil.ultimo_cargo or "No especificado",
        "nivel_ingles": perfil.nivel_ingles or "No especificado",
        "cv_texto": cv_texto,
    })

    return ResultadoScoring(**raw)