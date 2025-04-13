import os
import json
import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, request

CONFIG_PATH = "user_config.json"
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"  # Render에서 자동 제공

app_flask = Flask(__name__)  # Flask 앱 for Webhook
user_data = {}

async def send_telegram(message, chat_id=None):
    token = BOT_TOKEN
    if not chat_id:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕하세요! SRT 예약을 시작합니다.\n다음 정보를 줄바꿈 없이 한 줄에 입력해주세요:\n전화번호 비밀번호 출발역 도착역 날짜 시작시간 종료시간\n예시: 01012345678 abcd1234 수서 부산 2025/04/15 08:00 09:00"
    )
    user_data[update.effective_chat.id] = {"step": "bulk"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    data = user_data.get(chat_id, {})
    step = data.get("step")

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

        await update.message.reply_text("✅ 설정이 완료되었습니다! /go 를 입력하면 예약을 시작합니다.")
        user_data[chat_id]["step"] = "done"

async def go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚄 예약을 시작합니다! 잠시만 기다려주세요...")
    import subprocess
    subprocess.Popen(["python3", "final.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Flask에 요청 오면 Telegram dispatcher로 넘김
@app_flask.post(f'/{BOT_TOKEN}')
def webhook():
    from telegram import Update
    from telegram.ext import Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("go", go))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK"

if __name__ == '__main__':
    import threading

    # Flask 서버 실행
    threading.Thread(target=lambda: app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()

    # Telegram Webhook 등록
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}")
    print(f"✅ Webhook 연결됨: {WEBHOOK_URL}")