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

# Импортируем нашу базу данных
import database as db

app = FastAPI()

# Разрешаем запросы с твоего GitHub Pages
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

# --- МОДЕЛИ ДАННЫХ ---
class ChatRequest(BaseModel):
    user_id: int
    user_name: str
    text: str

class FortuneRequest(BaseModel):
    user_id: int
    user_name: str
    question: str
    cards: list

# --- ФУНКЦИЯ ИИ ---
def ask_yandex_gpt(messages):
    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
            "completionOptions": {"stream": False, "temperature": 0.8, "maxTokens": 600},
            "messages": messages
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()["result"]["alternatives"][0]["message"]["text"]
        else:
            # ВОЗВРАЩАЕМ ТОЧНЫЙ ОТВЕТ ОТ ЯНДЕКСА
            return f"ОШИБКА ЯНДЕКСА (Код {response.status_code}): {response.text}"
    except Exception as e:
        return f"ОШИБКА СЕРВЕРА: {e}"

# --- API ДЛЯ РАСКЛАДА ---
@app.post("/api/fortune")
async def get_fortune(data: FortuneRequest):
    user = db.get_user(data.user_id, data.user_name)
    balance = user[2]
    is_free = db.can_get_free_fortune(data.user_id)

    if not is_free and balance < 1:
        return {"status": "error", "message": "Недостаточно токенов. Пополните баланс."}

    # Списание
    if is_free:
        db.mark_free_fortune_used(data.user_id)
        cost_msg = "🎁 Бесплатный расклад"
    else:
        db.update_balance(data.user_id, -1)
        cost_msg = "💸 Списано 1 токен"

    # Генерация ответа
    prompt = f"Пользователь спрашивает: '{data.question}'. Выпали карты: {', '.join(data.cards)}. Сделай тарологический расклад."
    messages = [
        {"role": "system", "text": "Ты опытный таролог."},
        {"role": "user", "text": prompt}
    ]
    reading = ask_yandex_gpt(messages)

    # Сохраняем в историю
    db.clear_chat(data.user_id)
    db.save_message(data.user_id, "user", f"Вопрос: {data.question}. Карты: {', '.join(data.cards)}")
    db.save_message(data.user_id, "assistant", reading)
    db.set_chat_status(data.user_id, True, data.cards)
    
    return {"status": "ok", "reading": reading, "cost": cost_msg}

# --- API ДЛЯ ЧАТА ---
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
    
    messages = [{"role": "system", "text": "Ты таролог. Продолжай диалог с клиентом, опираясь на предыдущий расклад."}]
    for msg in history:
        messages.append({"role": msg["role"], "text": msg["text"]})
    
    reply = ask_yandex_gpt(messages)
    db.save_message(data.user_id, "assistant", reply)
    
    return {"status": "ok", "reply": reply}

# --- БОТ ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    db.get_user(message.from_user.id, message.from_user.first_name)
    web_app = WebAppInfo(url=WEBAPP_URL)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Открыть гадалку", web_app=web_app)],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="balance")]
    ])
    await message.answer(f"Привет, {message.from_user.first_name}! 👋\nОткрой гадалку, чтобы начать.", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    await callback.message.answer(f"💰 Ваш баланс: {user[2]} токенов.")
    await callback.answer()

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
