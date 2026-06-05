from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config import settings
from .schemas import PerfilExtraido

CAMPOS_CRITICOS = ["nombre", "email", "anios_experiencia", "tecnologias"]

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
Sos un extractor de datos experto en CVs. Tu ÚNICA tarea es extraer información estructurada.
No evalúes ni opines. Solo extrae lo que está explícitamente escrito en el CV.

Devolvé SOLO un JSON válido con esta estructura exacta:
{{
  "nombre": "string o null",
  "email": "string o null",
  "telefono": "string o null",
  "anios_experiencia": número entero o null,
  "tecnologias": ["lista", "de", "tecnologías"],
  "ultimo_cargo": "string o null",
  "nivel_ingles": "nativo|avanzado|intermedio|básico|no especificado"
}}

Reglas:
- anios_experiencia: calculá desde el primer trabajo hasta hoy. Si no hay fechas, estimá por cantidad de roles.
- tecnologias: incluí lenguajes, frameworks, bases de datos, herramientas cloud. Máximo 15.
- nivel_ingles: si no se menciona explícitamente, poné "no especificado".
- No inventes datos. Si no está en el CV, poné null.
"""),
    ("user", "CV:\n{cv_texto}")
])


def agente_prescreening(cv_texto: str) -> PerfilExtraido:
    """
    Agente 1: extrae datos estructurados del CV.
    Devuelve un PerfilExtraido con flag de completitud.
    """
    model = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )
    parser = JsonOutputParser()
    chain = _PROMPT | model | parser

    raw = chain.invoke({"cv_texto": cv_texto})

    perfil = PerfilExtraido(**raw)

    # Detectar campos críticos faltantes
    faltantes = []
    if not perfil.nombre:
        faltantes.append("nombre completo")
    if not perfil.email:
        faltantes.append("email de contacto")
    if perfil.anios_experiencia is None:
        faltantes.append("años de experiencia")
    if not perfil.tecnologias:
        faltantes.append("tecnologías o habilidades principales")
    if perfil.nivel_ingles == "no especificado":
        faltantes.append("nivel de inglés")

    perfil.incompleto = len(faltantes) > 0
    perfil.campos_faltantes = faltantes

    return perfil