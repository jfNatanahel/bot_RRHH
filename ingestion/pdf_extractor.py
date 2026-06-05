import hashlib
import re
from pypdf import PdfReader


MAX_CHARS = 24000  # ~8000 tokens para Gemini Flash


def extraer_texto_pdf(ruta_o_bytes) -> str:
    """
    Extrae texto de un PDF dado su ruta en disco o sus bytes crudos.
    Retorna el texto limpio y truncado al límite seguro.
    """
    if isinstance(ruta_o_bytes, (bytes, bytearray)):
        import io
        reader = PdfReader(io.BytesIO(ruta_o_bytes))
    else:
        reader = PdfReader(ruta_o_bytes)

    paginas = []
    for page in reader.pages:
        texto = page.extract_text()
        if texto:
            paginas.append(texto)

    texto_completo = "\n".join(paginas)
    return _limpiar_texto(_truncar(texto_completo))


def _limpiar_texto(texto: str) -> str:
    """Elimina artefactos comunes de PDFs: saltos múltiples, chars raros."""
    texto = re.sub(r'\n{3,}', '\n\n', texto)          # colapsar saltos excesivos
    texto = re.sub(r'[ \t]{2,}', ' ', texto)           # colapsar espacios múltiples
    texto = re.sub(r'[^\x20-\x7E\nÁÉÍÓÚáéíóúÑñüÜ]', '', texto)  # eliminar no-ASCII raro
    return texto.strip()


def _truncar(texto: str) -> str:
    """Trunca el texto si supera el límite, priorizando el inicio del CV."""
    if len(texto) <= MAX_CHARS:
        return texto
    return texto[:MAX_CHARS] + "\n\n[... CV truncado por longitud ...]"


def calcular_hash(texto: str) -> str:
    """SHA256 del texto para deduplicación."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()