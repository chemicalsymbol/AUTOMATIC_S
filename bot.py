import os
import json
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_URL = f"https://{HOSTNAME}/{BOT_TOKEN}"

print(f"[DEBUG] 현재 BOT_TOKEN: {BOT_TOKEN}")
print(f"[DEBUG] WEBHOOK_URL: {WEBHOOK_URL}")

application = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 /start 호출됨")
    await update.message.reply_text("✅ 봇 작동 확인 완료!")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

def register_webhook():
    res = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
    )
    print("🌐 Webhook 등록 응답:", res.json())

if __name__ == "__main__":
    register_webhook()
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
    )