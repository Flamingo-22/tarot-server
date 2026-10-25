import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
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

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ПОЛНЫЙ СПИСОК КАРТ (78 ШТУК) ---
ALL_TAROT_CARDS = [
    # Старшие Арканы (22)
    "Шут", "Маг", "Верховная Жрица", "Императрица", "Император", "Иерофант",
    "Влюбленные", "Колесница", "Сила", "Отшельник", "Колесо Фортуны", "Справедливость",
    "Повешенный", "Смерть", "Умеренность", "Дьявол", "Башня", "Звезда", "Луна", "Солнце", "Суд", "Мир",
    # Младшие Арканы: Жезлы (14)
    "Туз Жезлов", "Двойка Жезлов", "Тройка Жезлов", "Четверка Жезлов", "Пятерка Жезлов", "Шестерка Жезлов", "Семерка Жезлов", "Восьмерка Жезлов", "Девятка Жезлов", "Десятка Жезлов", "Паж Жезлов", "Рыцарь Жезлов", "Королева Жезлов", "Король Жезлов",
    # Младшие Арканы: Кубки (14)
    "Туз Кубков", "Двойка Кубков", "Тройка Кубков", "Четверка Кубков", "Пятерка Кубков", "Шестерка Кубков", "Семерка Кубков", "Восьмерка Кубков", "Девятка Кубков", "Десятка Кубков", "Паж Кубков", "Рыцарь Кубков", "Королева Кубков", "Король Кубков",
    # Младшие Арканы: Мечи (14)
    "Туз Мечей", "Двойка Мечей", "Тройка Мечей", "Четверка Мечей", "Пятерка Мечей", "Шестерка Мечей", "Семерка Мечей", "Восьмерка Мечей", "Девятка Мечей", "Десятка Мечей", "Паж Мечей", "Рыцарь Мечей", "Королева Мечей", "Король Мечей",
    # Младшие Арканы: Пентакли (14)
    "Туз Пентаклей", "Двойка Пентаклей", "Тройка Пентаклей", "Четверка Пентаклей", "Пятерка Пентаклей", "Шестерка Пентаклей", "Семерка Пентаклей", "Восьмерка Пентаклей", "Девятка Пентаклей", "Десятка Пентаклей", "Паж Пентаклей", "Рыцарь Пентаклей", "Королева Пентаклей", "Король Пентаклей"
]

class ChatRequest(BaseModel):
    user_id: int
    user_name: str
    text: str

class FortuneRequest(BaseModel):
    user_id: int
    user_name: str
    question: str
    cards: list

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

# Новый эндпоинт для получения баланса
@app.get("/api/balance/{user_id}")
async def get_balance(user_id: int):
    balance = db.get_user_balance(user_id)
    return {"balance": balance}

@app.post("/api/fortune")
async def get_fortune(data: FortuneRequest):
    # Создаем пользователя, если его нет
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

    # ЗАГАДОЧНЫЙ ПРОМПТ ДЛЯ ИИ
    prompt = f"""Пользователь спрашивает: '{data.question}'.
Выпали карты: {', '.join(data.cards)}.

Ты — глубокий и загадочный таролог. Твоя задача — дать толкование, которое звучит мудро и оставляет пространство для размышлений. 
Не давай прямых и однозначных ответов (вроде "да" или "нет"). Используй метафоры, говори о скрытых энергиях и внутренних ощущениях клиента. 
Ответ должен быть на русском, объемом 150-200 слов. Разбери карты в контексте вопроса и дай совет, который заставит человека задуматься."""

    messages = [
        {"role": "system", "text": "Ты — таролог. Ты говоришь загадками и помогаешь человеку самому найти ответ."},
        {"role": "user", "text": prompt}
    ]
    
    reading = ask_yandex_gpt(messages)

    # Сохраняем в чат
    db.clear_chat(data.user_id)
    db.save_message(data.user_id, "user", f"Вопрос: {data.question}. Карты: {', '.join(data.cards)}")
    db.save_message(data.user_id, "assistant", reading)
    db.set_chat_status(data.user_id, True, data.cards)
    
    return {"status": "ok", "reading": reading, "cost": cost_msg, "new_balance": db.get_user_balance(data.user_id)}

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
    
    messages = [{"role": "system", "text": "Ты таролог. Продолжай диалог с клиентом, опираясь на предыдущий расклад. Твои ответы должны быть туманными и глубокими."}]
    for msg in history:
        messages.append({"role": msg["role"], "text": msg["text"]})
    
    reply = ask_yandex_gpt(messages)
    db.save_message(data.user_id, "assistant", reply)
    
    return {"status": "ok", "reply": reply, "new_balance": db.get_user_balance(data.user_id)}

# --- БОТ ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    args = message.text.split()
    referrer_id = None
    
    # Обработка реферальной ссылки
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            if referrer_id != message.from_user.id:
                db.update_balance(referrer_id, 1.0)
                try:
                    await bot.send_message(referrer_id, "🎉 По вашей ссылке пришел друг! Вам начислен 1 токен.")
                except:
                    pass
        except ValueError:
            pass

    db.get_user(message.from_user.id, message.from_user.first_name)
    
    web_app = WebAppInfo(url=WEBAPP_URL)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Открыть гадалку", web_app=web_app)],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="balance")]
    ])
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\nЯ твой проводник в мир Таро. Загадай вопрос, и карты дадут ответ.\n\n"
        f"🎁 Твой первый расклад сегодня — бесплатный!", 
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: types.CallbackQuery):
    balance = db.get_user_balance(callback.from_user.id)
    await callback.message.answer(f"💰 Ваш баланс: {balance} токенов.\n\n1 токен = 10 руб.")
    await callback.answer()

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
