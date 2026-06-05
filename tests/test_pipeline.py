"""
Tests básicos del pipeline.
Correr con: pytest tests/ -v

Para tests de integración reales (llaman a Gemini):
    pytest tests/ -v -m integration
"""
import pytest
from unittest.mock import patch, MagicMock
from ingestion.pdf_extractor import _limpiar_texto, _truncar, calcular_hash


# ─── Tests de ingestion ───────────────────────────────────────

def test_limpieza_texto_elimina_saltos_multiples():
    texto = "Línea 1\n\n\n\nLínea 2"
    resultado = _limpiar_texto(texto)
    assert "\n\n\n" not in resultado


def test_truncado_respeta_limite():
    texto_largo = "x" * 30000
    resultado = _truncar(texto_largo)
    assert len(resultado) <= 24100  # MAX_CHARS + sufijo


def test_hash_es_determinista():
    texto = "CV de prueba con contenido fijo"
    assert calcular_hash(texto) == calcular_hash(texto)


def test_hash_diferente_para_textos_distintos():
    assert calcular_hash("CV A") != calcular_hash("CV B")


# ─── Tests de schemas ────────────────────────────────────────

def test_perfil_extraido_detecta_campos_faltantes():
    from agents.schemas import PerfilExtraido
    perfil = PerfilExtraido(
        nombre=None,
        email="test@test.com",
        tecnologias=["Python"],
        anios_experiencia=3,
    )
    # El schema no valida completitud automáticamente — eso lo hace el agente
    assert perfil.email == "test@test.com"
    assert perfil.nombre is None


def test_resultado_scoring_valida_rango():
    from agents.schemas import ResultadoScoring
    with pytest.raises(Exception):
        ResultadoScoring(puntaje=150, justificacion="test")


# ─── Tests de config ─────────────────────────────────────────

def test_get_client_devuelve_demo_para_cliente_inexistente():
    from config.clients import get_client
    result = get_client("cliente_que_no_existe")
    assert result["chroma_collection"] == "demo_jobs"


# ─── Test de integración (requiere GEMINI_API_KEY) ───────────

@pytest.mark.integration
def test_pipeline_completo_con_cv_de_prueba():
    """
    Test end-to-end del pipeline. Requiere:
    - GEMINI_API_KEY válida en .env
    - Job profile cargado para cliente 'demo'
    Correr con: pytest tests/ -v -m integration
    """
    import asyncio
    from langgraph_flow import procesar_candidato

    CV_PRUEBA = b"""
    %PDF-1.4 (simulado para test)
    Juan Perez - Software Developer
    Email: juan@example.com
    5 años de experiencia en Python, FastAPI, Docker, PostgreSQL.
    Inglés avanzado. Último cargo: Senior Backend Developer en TechCorp.
    """

    # Usar bytes directamente sin PDF real para test
    with patch("ingestion.pdf_extractor.PdfReader") as mock_pdf:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = CV_PRUEBA.decode()
        mock_pdf.return_value.pages = [mock_page]

        estado = asyncio.run(procesar_candidato(
            cv_bytes=CV_PRUEBA,
            client_id="demo",
            chat_id="12345",
        ))

    assert estado.get("decision") in ("approved", "talent_bank", "duplicate")
    assert estado.get("score_final") is not None