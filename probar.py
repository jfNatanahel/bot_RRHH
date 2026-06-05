from dotenv import load_dotenv
load_dotenv()

import telegram_bot.messenger as m
async def fake_enviar(chat_id, texto, **kwargs):
    print(f"\n[TELEGRAM → {chat_id}]:\n{texto}\n")
m.enviar_mensaje = fake_enviar

import asyncio
from langgraph_flow import procesar_candidato

with open("cv_prueba.pdf", "rb") as f:
    cv_bytes = f.read()

estado = asyncio.run(procesar_candidato(
    cv_bytes=cv_bytes,
    client_id="demo",
    chat_id="test_local",
))

print("=== RESULTADO ===")
print("Nombre:", estado.get("nombre"))
print("Score draft:", estado.get("score_draft"))
print("Score final:", estado.get("score_final"))
print("Decisión:", estado.get("decision"))
print("Razonamiento:", (estado.get("score_reasoning") or "")[:300])