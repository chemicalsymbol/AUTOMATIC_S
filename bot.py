import os
import json
import asyncio
import threading
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()

# === 환경변수 ===
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
print(f"[DEBUG] 현재 BOT_TOKEN: {BOT_TOKEN}")
CONFIG_PATH = "user_config.json"
HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_URL = f"https://{HOSTNAME}/{BOT_TOKEN}"

# === Flask 앱 ===
app_flask = Flask(__name__)
user_data = {}

# === Telegram Application ===
application = ApplicationBuilder().token(BOT_TOKEN).build()

# === 핸들러 정의 ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 /start 호출됨")
    await update.message.reply_text(
        "안녕하세요! SRT 예약을 시작합니다.\n"
        "다음 정보를 줄바꿈 없이 한 줄에 입력해주세요:\n"
        "전화번호 비밀번호 출발역 도착역 날짜 시작시간 종료시간\n"
        "예시: 01012345678 abcd1234 수서 부산 2025/04/15 08:00 09:00"
    )
    user_data[update.effective_chat.id] = {"step": "bulk"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📨 사용자 메시지 수신:", update.message.text)
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    step = user_data.get(chat_id, {}).get("step")

    if step == "bulk":
        parts = text.split()
        if len(parts) != 7:
            await update.message.reply_text("❌ 형식이 올바르지 않습니다. 다시 입력해주세요.")
            return

        phone, password, departure, arrival, date, start_time, end_time = parts
        config = {
            "phone": phone,
            "password": password,
            "departure": departure,
            "arrival": arrival,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "telegram_chat_id": str(chat_id)
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        await update.message.reply_text("✅ 설정 완료! /go 를 입력하면 예약을 시작합니다.")
        user_data[chat_id]["step"] = "done"

async def go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚄 예약 실행 요청")
    await update.message.reply_text("🚄 예약을 시작합니다! 잠시만 기다려주세요...")
    import subprocess
    subprocess.Popen(["python3", "final.py"])

# === 핸들러 등록 ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("go", go))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Webhook 수신 ===
@app_flask.post(f'/{BOT_TOKEN}')
def webhook():
    print("📥 Webhook 호출됨")
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
        print("✅ Update 처리 완료")
    except Exception as e:
        print("❌ 처리 중 오류:", e)
    return "OK"

# === Webhook 등록 및 실행 ===
def run_bot_webhook():
    # Webhook 등록
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
        response = requests.get(url)
        print("🌐 Webhook 등록 응답:", response.json())
    except Exception as e:
        print("❌ Webhook 등록 실패:", e)

    # run_webhook (포트 바인딩은 자동 처리)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )

# === 메인 ===
if __name__ == "__main__":
    print("🚀 bot.py 실행 시작")
    threading.Thread(target=lambda: app_flask.run(host="0.0.0.0", port=5000)).start()
    run_bot_webhook()