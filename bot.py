import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_URL = f"https://{HOSTNAME}/{BOT_TOKEN}"

print(f"[DEBUG] BOT_TOKEN: {BOT_TOKEN}")
print(f"[DEBUG] WEBHOOK_URL: {WEBHOOK_URL}")

app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    print("📥 Webhook 호출됨")
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
        return "OK"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return "ERROR", 500

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 /start 호출됨")
    await update.message.reply_text("✅ 작동 중입니다!")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

def register_webhook():
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
        res = requests.get(url)
        print("🌐 Webhook 등록 결과:", res.json())
    except Exception as e:
        print("❌ Webhook 등록 실패:", e)

register_webhook()
