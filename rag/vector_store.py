import os
import json
import pickle
import faiss
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import settings

FAISS_DIR = settings.chroma_persist_dir  # reusamos el mismo path del .env


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.gemini_api_key,
        task_type="retrieval_document",
    )


def _get_paths(collection_name: str) -> tuple[str, str]:
    """Devuelve las rutas del índice FAISS y los textos asociados."""
    base = os.path.join(FAISS_DIR, collection_name)
    return f"{base}.index", f"{base}.texts.json"


def cargar_job_profile(collection_name: str, profile_text: str, metadata: dict = None):
    """
    Embeddea y guarda un job profile en el índice FAISS del cliente.
    Si ya existe el índice, agrega el nuevo documento.
    """
    embeddings_model = get_embeddings()
    vector = embeddings_model.embed_query(profile_text)
    vector_np = np.array([vector], dtype="float32")

    index_path, texts_path = _get_paths(collection_name)
    os.makedirs(FAISS_DIR, exist_ok=True)

    # Cargar índice existente o crear uno nuevo
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        with open(texts_path, "r", encoding="utf-8") as f:
            textos = json.load(f)
    else:
        index = faiss.IndexFlatIP(len(vector))  # Inner Product = similitud coseno con vectores normalizados
        textos = []

    # Normalizar vector para similitud coseno
    faiss.normalize_L2(vector_np)
    index.add(vector_np)
    textos.append({"text": profile_text, "metadata": metadata or {}})

    # Guardar
    faiss.write_index(index, index_path)
    with open(texts_path, "w", encoding="utf-8") as f:
        json.dump(textos, f, ensure_ascii=False, indent=2)


def buscar_similitud(collection_name: str, cv_texto: str, k: int = 3) -> tuple[float, str]:
    """
    Busca los fragmentos del job profile más similares al CV.
    Retorna (score_promedio, fragmentos_concatenados).
    """
    index_path, texts_path = _get_paths(collection_name)

    if not os.path.exists(index_path):
        return 0.0, "No se encontró perfil de puesto cargado para este cliente."

    embeddings_model = get_embeddings()
    vector = embeddings_model.embed_query(cv_texto)
    vector_np = np.array([vector], dtype="float32")
    faiss.normalize_L2(vector_np)

    index = faiss.read_index(index_path)
    with open(texts_path, "r", encoding="utf-8") as f:
        textos = json.load(f)

    k_real = min(k, index.ntotal)
    scores, indices = index.search(vector_np, k_real)

    resultados = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            resultados.append((float(score), textos[idx]["text"]))

    if not resultados:
        return 0.0, "Sin resultados de búsqueda semántica."

    score_promedio = sum(s for s, _ in resultados) / len(resultados)
    fragmentos = "\n\n---\n\n".join(
        f"[Similitud: {score:.2f}]\n{texto}"
        for score, texto in resultados
    )

    return round(score_promedio, 4), fragmentos