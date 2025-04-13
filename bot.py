import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import requests
from dotenv import load_dotenv
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import subprocess

load_dotenv()

CONFIG_PATH = "user_config.json"
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
user_data = {}

async def send_telegram(message, chat_id=None):
    token = os.getenv("TELEGRAM_TOKEN")
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
    subprocess.Popen(["python", "final.py"])

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("go", go))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram 봇 실행 중...")
    app.run_polling()