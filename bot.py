import os
import json
import threading
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CONFIG_PATH = "user_config.json"
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"

app_flask = Flask(__name__)
user_data = {}

# ✅ 전역 Telegram Application 객체
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ✅ 핸들러 정의
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕하세요! SRT 예약을 시작합니다.\n"
        "다음 정보를 줄바꿈 없이 한 줄에 입력해주세요:\n"
        "전화번호 비밀번호 출발역 도착역 날짜 시작시간 종료시간\n"
        "예시: 01012345678 abcd1234 수서 부산 2025/04/15 08:00 09:00"
    )
    user_data[update.effective_chat.id] = {"step": "bulk"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📨 메시지 수신:", update.message.text)
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

        await update.message.reply_text("✅ 설정 완료! /go 를 입력하면 예약 시작합니다.")
        user_data[chat_id]["step"] = "done"

async def go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚄 예약을 시작합니다!")
    import subprocess
    subprocess.Popen(["python3", "final.py"])

# ✅ 핸들러 등록
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("go", go))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ✅ Flask로 webhook 처리
@app_flask.post(f'/{BOT_TOKEN}')
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK"

# ✅ dispatcher를 별도 쓰레드에서 실행 (run_polling 대신)
def run_app():
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    # Flask 서버는 따로 실행
    threading.Thread(target=lambda: app_flask.run(host="0.0.0.0", port=5000)).start()

    # Telegram Application은 Webhook 모드로 실행
    run_app()