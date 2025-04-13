import os
import json
import asyncio
import requests
from flask import Flask, request
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

print(f"[DEBUG] BOT_TOKEN: {BOT_TOKEN}")
print(f"[DEBUG] WEBHOOK_URL: {WEBHOOK_URL}")

# Flask 서버
app = Flask(__name__)

# Telegram Application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# 핸들러 등록
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 /start 호출됨")
    await update.message.reply_text("✅ 봇 작동 확인!")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

# Webhook 라우트
@app.post(f"/{BOT_TOKEN}")
def telegram_webhook():
    print("📥 Webhook 호출됨")
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
        return "OK"
    except Exception as e:
        print(f"❌ Webhook 처리 실패: {e}")
        return "ERROR", 500

# Webhook 등록
def register_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
    res = requests.get(url)
    print("🌐 Webhook 등록 응답:", res.json())

if __name__ == "__main__":
    register_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
