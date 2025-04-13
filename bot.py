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

# 🌱 환경변수 로드
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_URL = f"https://{HOSTNAME}/{BOT_TOKEN}"

print(f"[DEBUG] BOT_TOKEN: {BOT_TOKEN}")
print(f"[DEBUG] WEBHOOK_URL: {WEBHOOK_URL}")

# ✅ Flask 앱 객체
app = Flask(__name__)

# ✅ Telegram Bot Application 객체
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ✅ Telegram 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 /start 호출됨")
    await update.message.reply_text("✅ 봇 작동 확인 완료!")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

# ✅ Telegram Webhook 처리 엔드포인트
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    print("📥 Webhook 호출됨")
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
        return "OK"
    except Exception as e:
        print(f"❌ 처리 중 오류: {e}")
        return "ERROR", 500

# ✅ Telegram Webhook 등록 (Render 배포 시 1회 실행)
def register_webhook():
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
        res = requests.get(url)
        print("🌐 Webhook 등록 응답:", res.json())
    except Exception as e:
        print(f"❌ Webhook 등록 실패: {e}")

# ✅ gunicorn 실행 환경에서 이 부분만 실행됨
if __name__ == "__main__":
    register_webhook()