import asyncio
import httpx
import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DOMINIO = "https://bot.natanahel-dev.lat"

async def main():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json={"url": f"{DOMINIO}/webhook/telegram"})
        print(r.json())

asyncio.run(main())