"""
Registro de clientes activos.
Cada cliente tiene un client_id, el chat_id de su reclutador en Telegram
y el nombre de la colección Chroma donde viven sus job profiles.

En fase MVP+ esto migra a la base de datos. Por ahora es un dict estático.
"""

CLIENTS: dict[str, dict] = {
    "demo": {
        "name": "Demo Company",
        "recruiter_chat_id": None,        # Si es None, usa RECRUITER_CHAT_ID del .env
        "chroma_collection": "demo_jobs",
        "score_threshold": None,          # Si es None, usa SCORE_THRESHOLD del .env
    },
    # Agregar nuevos clientes acá:
    # "cliente_abc": {
    #     "name": "ABC Corp",
    #     "recruiter_chat_id": "123456789",
    #     "chroma_collection": "abc_jobs",
    #     "score_threshold": 80,
    # },
}


def get_client(client_id: str) -> dict:
    """Devuelve la config del cliente o la config por defecto si no existe."""
    return CLIENTS.get(client_id, CLIENTS["demo"])