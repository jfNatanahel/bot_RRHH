from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config import settings
from .schemas import ResultadoScoring, ResultadoSelfCorrection

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
Sos un auditor crítico de evaluaciones de RRHH. Tu rol es detectar sesgos, errores o inconsistencias
en la evaluación de un agente anterior.

Tu tarea: revisar el puntaje y justificación del evaluador anterior y determinar si es correcto.

Buscás específicamente:
1. ¿El puntaje está inflado por un CV bien redactado pero con poca sustancia real?
2. ¿El puntaje está deflado injustamente por falta de keywords aunque el perfil sea sólido?
3. ¿Hay contradicciones entre la justificación y el puntaje asignado?
4. ¿Se ignoraron red flags evidentes en el CV original?
5. ¿Se penalizó injustamente experiencia en tecnologías similares (no idénticas)?

Si detectás un problema, ajustá el puntaje con justificación clara.
Si el puntaje es correcto, confirmalo sin cambios.

Devolvé SOLO un JSON válido:
{{
  "puntaje_ajustado": número del 1 al 100,
  "hubo_ajuste": true o false,
  "notas_correccion": "explicación del ajuste o confirmación de que el puntaje es correcto"
}}
"""),
    ("user", """
CV ORIGINAL DEL CANDIDATO:
{cv_texto}

EVALUACIÓN DEL AGENTE ANTERIOR:
Puntaje asignado: {puntaje_draft}
Justificación: {justificacion}
Puntos fuertes: {puntos_fuertes}
Puntos débiles: {puntos_debiles}
""")
])


def agente_selfcorrection(
    cv_texto: str,
    scoring_draft: ResultadoScoring,
) -> ResultadoSelfCorrection:
    """
    Agente 3: critica la evaluación del Agente 2 y ajusta el puntaje si es necesario.
    """
    model = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )
    parser = JsonOutputParser()
    chain = _PROMPT | model | parser

    raw = chain.invoke({
        "cv_texto": cv_texto,
        "puntaje_draft": scoring_draft.puntaje,
        "justificacion": scoring_draft.justificacion,
        "puntos_fuertes": "\n".join(f"- {p}" for p in scoring_draft.puntos_fuertes),
        "puntos_debiles": "\n".join(f"- {p}" for p in scoring_draft.puntos_debiles),
    })

    return ResultadoSelfCorrection(**raw)