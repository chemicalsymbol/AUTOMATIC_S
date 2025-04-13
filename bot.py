import os
import json
import asyncio
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_URL = f"https://{HOSTNAME}/{BOT_TOKEN}"

print(f"[DEBUG] 현재 BOT_TOKEN: {BOT_TOKEN}")
print(f"[DEBUG] WEBHOOK_URL: {WEBHOOK_URL}")

application = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 /start 호출됨")
    await update.message.reply_text("✅ 봇이 작동 중입니다!")

async def go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚄 예약 시작!")
    import subprocess
    subprocess.Popen(["python3", "final.py"])

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("go", go))
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