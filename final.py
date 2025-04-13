
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import requests
from dotenv import load_dotenv
import os

load_dotenv()

CONFIG_PATH = "user_config.json"

async def send_telegram(message):
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)
    token = config.get("telegram_token")
    chat_id = config.get("telegram_chat_id")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message})

async def run():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    PHONE = config["phone"]
    PW = config["password"]
    DEPARTURE = config["departure"]
    ARRIVAL = config["arrival"]
    TARGET_DATE_TEXT = config["date"]
    TARGET_START_HOUR, TARGET_START_MINUTE = map(int, config["start_time"].split(":"))
    TARGET_END_HOUR, TARGET_END_MINUTE = map(int, config["end_time"].split(":"))
    TARGET_START_HOUR2 = TARGET_START_HOUR
    if TARGET_START_HOUR % 2 != 0:
        TARGET_START_HOUR2 -= 1  # 짝수 기준 시간으로 맞춤

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 로그인
        await page.goto("https://etk.srail.kr/cmc/01/selectLoginForm.do")
        await page.click("#srchDvCd3")
        await page.fill("#srchDvNm03", PHONE)
        await page.fill("#hmpgPwdCphd03", PW)
        await page.click('input[type="submit"].loginSubmit:not([disabled])')
        await asyncio.sleep(2)

        if "selectLoginForm" in page.url:
            await send_telegram("❌ 로그인 실패")
            return

        print("✅ 로그인 성공")

        while True:
            try:
                await page.goto("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000")
                await page.wait_for_selector("#dptRsStnCdNm")

                await page.fill("#dptRsStnCdNm", "")
                await page.type("#dptRsStnCdNm", DEPARTURE)
                await asyncio.sleep(1.5)  # 자동완성 제안이 뜰 시간을 줌
                await page.keyboard.press("ArrowDown")  # 첫 번째 자동완성 항목으로 이동
                await page.keyboard.press("Tab")  # 선택 및 확정

                await page.fill("#arvRsStnCdNm", "")
                await page.type("#arvRsStnCdNm", ARRIVAL)
                await asyncio.sleep(1.5)
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Tab")

                date_value = await page.eval_on_selector(
                    "#dptDt",
                    f'''(select) => {{
                                const options = Array.from(select.options);
                                const match = options.find(o => o.textContent.includes("{TARGET_DATE_TEXT}"));
                                return match ? match.value : null;
                            }}'''
                )

                if not date_value:
                    await send_telegram(f"❌ 날짜 '{TARGET_DATE_TEXT}' 선택 불가")
                    return

                await page.select_option("#dptDt", date_value)
                await page.select_option("#dptTm", f"{TARGET_START_HOUR2:02}")

                await page.click('input[type="submit"][value="조회하기"]')

                await page.wait_for_selector("div.tbl_wrap.th_thead tbody tr", timeout=10000)

                rows = await page.query_selector_all("div.tbl_wrap.th_thead tbody tr")

                for row in rows:
                    cells = await row.query_selector_all("td")
                    if len(cells) < 7:
                        continue

                    train_no = (await cells[2].inner_text()).strip()
                    dep_time_raw = (await cells[3].inner_text()).strip()
                    dep_time = dep_time_raw.split('\n')[-1].strip()[:5]
                    dep_hour, dep_min = map(int, dep_time.split(":"))
                    general_status = (await cells[6].inner_text()).strip()

                    in_range = False
                    if (dep_hour > TARGET_START_HOUR or (
                            dep_hour == TARGET_START_HOUR and dep_min >= TARGET_START_MINUTE)) and \
                            (dep_hour < TARGET_END_HOUR or (
                                    dep_hour == TARGET_END_HOUR and dep_min <= TARGET_END_MINUTE)):
                        in_range = True

                    if in_range and "예약" in general_status:
                        await asyncio.sleep(1)
                        btn = await cells[6].query_selector("a")
                        if btn:
                            await btn.click()
                            await send_telegram(f"🎯 예약 시도됨! 열차 {train_no} | 출발 {dep_time}")
                            print("🎯 예약 클릭 완료, 페이지 전환 대기 중...")

                            # ✅ 페이지가 예약 페이지로 바뀌었는지 확인
                            await asyncio.sleep(2)
                            return

                print("❌ 조건에 맞는 열차 없음. 60초 후 재시도")
                await asyncio.sleep(60)

            except Exception as e:
                print("⚠️ 오류 발생, 30초 후 재시도:", e)
                await send_telegram("⚠️ 오류 발생. 재시도 중...")
                await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(run())
