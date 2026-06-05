import httpx
from config import settings

BASE_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def enviar_mensaje(chat_id: str, texto: str, parse_mode: str = "Markdown") -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": texto,
                "parse_mode": parse_mode,
            },
            timeout=10,
        )
    return response.status_code == 200


async def descargar_archivo(file_id: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/getFile",
            params={"file_id": file_id},
            timeout=10,
        )
        response.raise_for_status()
        file_path = response.json()["result"]["file_path"]

        download_url = f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}"
        file_response = await client.get(download_url, timeout=30)
        file_response.raise_for_status()

    return file_response.content


async def registrar_webhook(url_dominio: str) -> dict:
    webhook_url = f"{url_dominio}/webhook/telegram"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/setWebhook",
            json={"url": webhook_url},
            timeout=10,
        )
    return response.json()