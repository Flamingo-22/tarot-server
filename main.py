import os
import requests
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import asyncio
import database as db

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "toochat-orders-1066139530-7xk9")

# 🔐 Telegram user_id администратора (задать в env на Render)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ALL_TAROT_CARDS = [
    "Шут", "Маг", "Верховная Жрица", "Императрица", "Император", "Иерофант",
    "Влюбленные", "Колесница", "Сила", "Отшельник", "Колесо Фортуны", "Справедливость",
    "Повешенный", "Смерть", "Умеренность", "Дьявол", "Башня", "Звезда", "Луна", "Солнце", "Суд", "Мир",
    "Туз Жезлов", "Двойка Жезлов", "Тройка Жезлов", "Четверка Жезлов", "Пятерка Жезлов", "Шестерка Жезлов",
    "Семерка Жезлов", "Восьмерка Жезлов", "Девятка Жезлов", "Десятка Жезлов", "Паж Жезлов", "Рыцарь Жезлов",
    "Королева Жезлов", "Король Жезлов",
    "Туз Кубков", "Двойка Кубков", "Тройка Кубков", "Четверка Кубков", "Пятерка Кубков", "Шестерка Кубков",
    "Семерка Кубков", "Восьмерка Кубков", "Девятка Кубков", "Десятка Кубков", "Паж Кубков", "Рыцарь Кубков",
    "Королева Кубков", "Король Кубков",
    "Туз Мечей", "Двойка Мечей", "Тройка Мечей", "Четверка Мечей", "Пятерка Мечей", "Шестерка Мечей",
    "Семерка Мечей", "Восьмерка Мечей", "Девятка Мечей", "Десятка Мечей", "Паж Мечей", "Рыцарь Мечей",
    "Королева Мечей", "Король Мечей",
    "Туз Пентаклей", "Двойка Пентаклей", "Тройка Пентаклей", "Четверка Пентаклей", "Пятерка Пентаклей",
    "Шестерка Пентаклей", "Семерка Пентаклей", "Восьмерка Пентаклей", "Девятка Пентаклей", "Десятка Пентаклей",
    "Паж Пентаклей", "Рыцарь Пентаклей", "Королева Пентаклей", "Король Пентаклей"
]

# 🌐 Базовый URL картинок. Меняется в env, без правки кода.
BASE_IMG_URL = os.getenv(
    "BASE_IMG_URL",
    "https://cdn.jsdelivr.net/gh/Flamingo-22/tarot-cards@main/"
)
# 🂠 Красивая «рубашка» — на случай, если фото не загрузилось
CARD_BACK_URL = os.getenv("CARD_BACK_URL", BASE_IMG_URL + "back.jpg")

CARD_IMAGES = {
    # Старшие Арканы
    "Шут": "Major_Arcana/Major_00.jpg",
    "Маг": "Major_Arcana/Major_01.jpg",
    "Верховная Жрица": "Major_Arcana/Major_02.jpg",
    "Императрица": "Major_Arcana/Major_03.jpg",
    "Император": "Major_Arcana/Major_04.jpg",
    "Иерофант": "Major_Arcana/Major_05.jpg",
    "Влюбленные": "Major_Arcana/Major_06.jpg",
    "Колесница": "Major_Arcana/Major_07.jpg",
    "Сила": "Major_Arcana/Major_08.jpg",
    "Отшельник": "Major_Arcana/Major_09.jpg",
    "Колесо Фортуны": "Major_Arcana/Major_10.jpg",
    "Справедливость": "Major_Arcana/Major_11.jpg",
    "Повешенный": "Major_Arcana/Major_12.jpg",
    "Смерть": "Major_Arcana/Major_13.jpg",
    "Умеренность": "Major_Arcana/Major_14.jpg",
    "Дьявол": "Major_Arcana/Major_15.jpg",
    "Башня": "Major_Arcana/Major_16.jpg",
    "Звезда": "Major_Arcana/Major_17.jpg",
    "Луна": "Major_Arcana/Major_18.jpg",
    "Солнце": "Major_Arcana/Major_19.jpg",
    "Суд": "Major_Arcana/Major_20.jpg",
    "Мир": "Major_Arcana/Major_21.jpg",
    # Жезлы
    "Туз Жезлов": "Wands/Wands_01.jpg",
    "Двойка Жезлов": "Wands/Wands_02.jpg",
    "Тройка Жезлов": "Wands/Wands_03.jpg",
    "Четверка Жезлов": "Wands/Wands_04.jpg",
    "Пятерка Жезлов": "Wands/Wands_05.jpg",
    "Шестерка Жезлов": "Wands/Wands_06.jpg",
    "Семерка Жезлов": "Wands/Wands_07.jpg",
    "Восьмерка Жезлов": "Wands/Wands_08.jpg",
    "Девятка Жезлов": "Wands/Wands_09.jpg",
    "Десятка Жезлов": "Wands/Wands_10.jpg",
    "Паж Жезлов": "Wands/Wands_11.jpg",
    "Рыцарь Жезлов": "Wands/Wands_12.jpg",
    "Королева Жезлов": "Wands/Wands_13.jpg",
    "Король Жезлов": "Wands/Wands_14.jpg",
    # Кубки
    "Туз Кубков": "Cups/Cups_01.jpg",
    "Двойка Кубков": "Cups/Cups_02.jpg",
    "Тройка Кубков": "Cups/Cups_03.jpg",
    "Четверка Кубков": "Cups/Cups_04.jpg",
    "Пятерка Кубков": "Cups/Cups_05.jpg",
    "Шестерка Кубков": "Cups/Cups_06.jpg",
    "Семерка Кубков": "Cups/Cups_07.jpg",
    "Восьмерка Кубков": "Cups/Cups_08.jpg",
    "Девятка Кубков": "Cups/Cups_09.jpg",
    "Десятка Кубков": "Cups/Cups_10.jpg",
    "Паж Кубков": "Cups/Cups_11.jpg",
    "Рыцарь Кубков": "Cups/Cups_12.jpg",
    "Королева Кубков": "Cups/Cups_13.jpg",
    "Король Кубков": "Cups/Cups_14.jpg",
    # Мечи
    "Туз Мечей": "Swords/Swords_01.jpg",
    "Двойка Мечей": "Swords/Swords_02.jpg",
    "Тройка Мечей": "Swords/Swords_03.jpg",
    "Четверка Мечей": "Swords/Swords_04.jpg",
    "Пятерка Мечей": "Swords/Swords_05.jpg",
    "Шестерка Мечей": "Swords/Swords_06.jpg",
    "Семерка Мечей": "Swords/Swords_07.jpg",
    "Восьмерка Мечей": "Swords/Swords_08.jpg",
    "Девятка Мечей": "Swords/Swords_09.jpg",
    "Десятка Мечей": "Swords/Swords_10.jpg",
    "Паж Мечей": "Swords/Swords_11.jpg",
    "Рыцарь Мечей": "Swords/Swords_12.jpg",
    "Королева Мечей": "Swords/Swords_13.jpg",
    "Король Мечей": "Swords/Swords_14.jpg",
    # Пентакли
    "Туз Пентаклей": "Pents/Pents_01.jpg",
    "Двойка Пентаклей": "Pents/Pents_02.jpg",
    "Тройка Пентаклей": "Pents/Pents_03.jpg",
    "Четверка Пентаклей": "Pents/Pents_04.jpg",
    "Пятерка Пентаклей": "Pents/Pents_05.jpg",
    "Шестерка Пентаклей": "Pents/Pents_06.jpg",
    "Семерка Пентаклей": "Pents/Pents_07.jpg",
    "Восьмерка Пентаклей": "Pents/Pents_08.jpg",
    "Девятка Пентаклей": "Pents/Pents_09.jpg",
    "Десятка Пентаклей": "Pents/Pents_10.jpg",
    "Паж Пентаклей": "Pents/Pents_11.jpg",
    "Рыцарь Пентаклей": "Pents/Pents_12.jpg",
    "Королева Пентаклей": "Pents/Pents_13.jpg",
    "Король Пентаклей": "Pents/Pents_14.jpg",
}

class ChatRequest(BaseModel):
    user_id: int
    user_name: str
    text: str

class FortuneRequest(BaseModel):
    user_id: int
    user_name: str
    question: str
    cards: list = []

class PayRequest(BaseModel):
    user_id: int
    user_name: str

def ask_yandex_gpt(messages):
    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
            "completionOptions": {"stream": False, "temperature": 0.85, "maxTokens": 600},
            "messages": messages
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()["result"]["alternatives"][0]["message"]["text"]
        return "Карты сегодня молчат. Попробуйте позже."
    except Exception as e:
        return f"Ошибка ИИ: {e}"

def send_ntfy_notification(message: str):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode("utf-8"), timeout=10)
    except Exception:
        pass

def card_image_url(card_name: str) -> str:
    path = CARD_IMAGES.get(card_name)
    if not path:
        return CARD_BACK_URL
    return BASE_IMG_URL + path

@app.get("/api/balance/{user_id}")
async def get_balance(user_id: int):
    return {"balance": db.get_user_balance(user_id)}

@app.get("/api/card-back")
async def get_card_back():
    return {"url": CARD_BACK_URL}

@app.post("/api/fortune")
async def get_fortune(data: FortuneRequest):
    user = db.get_user(data.user_id, data.user_name)
    balance = user[2]
    is_free = db.can_get_free_fortune(data.user_id)

    if not is_free and balance < 1:
        return {"status": "error", "message": "Бесплатное гадание на сегодня использовано. Пополните баланс!"}

    if is_free:
        db.mark_free_fortune_used(data.user_id)
        cost_msg = "🎁 Бесплатный расклад"
    else:
        db.update_balance(data.user_id, -1)
        cost_msg = "💸 Списано 1 токен"

    selected_cards = random.sample(ALL_TAROT_CARDS, 3)

    prompt = f"""Пользователь спрашивает: '{data.question}'.
Выпали карты: {', '.join(selected_cards)}.

Ты — глубокий и загадочный таролог. Дай толкование мудро, с метафорами. 150-200 слов. Не давай однозначных "да/нет"."""

    messages = [
        {"role": "system", "text": "Ты — таролог. Ты говоришь загадками."},
        {"role": "user", "text": prompt}
    ]

    reading = ask_yandex_gpt(messages)

    db.clear_chat(data.user_id)
    db.save_message(data.user_id, "user", f"Вопрос: {data.question}. Карты: {', '.join(selected_cards)}")
    db.save_message(data.user_id, "assistant", reading)
    db.set_chat_status(data.user_id, True, selected_cards)

    cards_data = []
    for card in selected_cards:
        cards_data.append({
            "name": card,
            "image": card_image_url(card)
        })

    return {
        "status": "ok",
        "reading": reading,
        "cost": cost_msg,
        "new_balance": db.get_user_balance(data.user_id),
        "cards": cards_data
    }

@app.post("/api/chat")
async def chat_with_tarot(data: ChatRequest):
    user = db.get_user(data.user_id, data.user_name)
    balance = user[2]
    chat_active = user[4]

    if not chat_active:
        if balance < 3:
            return {"status": "error", "message": "Для начала чата нужно 3 токена."}
        db.update_balance(data.user_id, -3)
        db.set_chat_status(data.user_id, True)

    db.save_message(data.user_id, "user", data.text)
    history = db.get_chat_history(data.user_id, limit=6)

    messages = [{"role": "system", "text": "Ты таролог. Продолжай диалог, опираясь на расклад."}]
    for msg in history:
        messages.append({"role": msg["role"], "text": msg["text"]})

    reply = ask_yandex_gpt(messages)
    db.save_message(data.user_id, "assistant", reply)

    return {"status": "ok", "reply": reply, "new_balance": db.get_user_balance(data.user_id)}

@app.post("/api/pay")
async def notify_payment(data: PayRequest):
    send_ntfy_notification(f"Гость {data.user_id} ({data.user_name}) заявил об оплате. Проверьте перевод.")
    return {"status": "ok", "message": "Уведомление отправлено."}

CARD_NUMBER = "2200 0101 0250 1486"

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            if referrer_id != message.from_user.id:
                db.update_balance(referrer_id, 1.0)
                try:
                    await bot.send_message(referrer_id, "🎉 По вашей ссылке пришел друг! Вам начислен 1 токен.")
                except Exception:
                    pass
        except ValueError:
            pass

    db.get_user(message.from_user.id, message.from_user.first_name)
    web_app = WebAppInfo(url=WEBAPP_URL)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Открыть гадалку", web_app=web_app)],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="balance")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup")]
    ])
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\nЗагадай вопрос, и карты дадут ответ.\n\n"
        f"🎁 Первый расклад сегодня — бесплатный!\n"
        f"✨ Новым гостям дарим 3 приветственных токена.",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: types.CallbackQuery):
    b = db.get_user_balance(callback.from_user.id)
    await callback.message.answer(f"💰 Ваш баланс: {b} токенов.\n\n1 токен = 10 руб.")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "topup")
async def show_topup(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid")]
    ])
    await callback.message.answer(
        f"💳 Переведите любую сумму на карту:\n\n`{CARD_NUMBER}`\n\n1 токен = 10 руб.\n\nПосле перевода нажмите кнопку.",
        parse_mode="Markdown", reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "paid")
async def confirm_payment(callback: types.CallbackQuery):
    send_ntfy_notification(f"Гость {callback.from_user.id} ({callback.from_user.first_name}) заявил об оплате. Проверьте перевод.")
    await callback.message.answer("✅ Уведомление отправлено. После проверки баланс будет зачислен.")
    await callback.answer()

# 🔐 Админ-команда: /add_balance <user_id> <amount>
@dp.message(Command("add_balance"))
async def admin_add_balance(message: types.Message):
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав на эту команду.")
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: `/add_balance <user_id> <amount>`", parse_mode="Markdown")
        return

    try:
        target_id = int(parts[1])
        amount = float(parts[2])
    except ValueError:
        await message.answer("❌ user_id должен быть числом, amount — числом. Пример: `/add_balance 123456789 5`", parse_mode="Markdown")
        return

    new_balance = db.add_balance_manual(target_id, amount, admin_id=message.from_user.id)
    if new_balance is None:
        await message.answer(f"⚠️ Пользователь с ID {target_id} не найден в базе.")
        return

    await message.answer(f"✅ Начислено {amount} токенов пользователю {target_id}.\nНовый баланс: {new_balance}")

    try:
        await bot.send_message(
            target_id,
            f"💎 Вам начислено {amount} токенов!\nТекущий баланс: {new_balance}.\nСпасибо, что с нами ✨"
        )
    except Exception:
        pass

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
