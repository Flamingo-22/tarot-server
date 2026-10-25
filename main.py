import os
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import asyncio

# --- ИНИЦИАЛИЗАЦИЯ ---
app = FastAPI()

# Разрешаем запросы с твоего GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Для тестов разрешаем всё
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Берем секреты из переменных окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- API ДЛЯ MINI APP (HTML) ---

class FortuneRequest(BaseModel):
    question: str
    cards: list
    user_id: int
    user_name: str

def get_ai_tarot_reading(question, cards, user_name):
    context = f"""
Пользователь {user_name} задал вопрос: "{question}"
Выпали карты: {', '.join(cards)}.

Ты — опытная таролог. Дай глубокое, но понятное толкование.
- Ответ должен быть на русском языке.
- Будь эмпатичной, но говори правду.
- Разбери каждую карту кратко, а затем дай общий совет по вопросу.
- Объем: около 150-200 слов.
"""
    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
            "completionOptions": {"stream": False, "temperature": 0.8, "maxTokens": 500},
            "messages": [
                {"role": "system", "text": "Ты таролог. Даешь точные и глубокие ответы."},
                {"role": "user", "text": context}
            ]
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()["result"]["alternatives"][0]["message"]["text"]
        else:
            return f"Карты сегодня молчат (Ошибка API: {response.status_code})."
    except Exception as e:
        return f"Произошла ошибка при общении с картами: {e}"

@app.post("/api/fortune")
async def get_fortune(data: FortuneRequest):
    # Здесь в будущем мы добавим проверку баланса и списание токенов
    # А пока просто генерируем ответ
    reading = get_ai_tarot_reading(data.question, data.cards, data.user_name)
    return {"status": "ok", "reading": reading}


# --- ЛОГИКА TELEGRAM БОТА ---

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    web_app = WebAppInfo(url=WEBAPP_URL)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Открыть гадалку", web_app=web_app)],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="balance")],
        [InlineKeyboardButton(text="💳 Пополнить", callback_data="deposit")]
    ])
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\nЯ твой проводник в мир Таро.",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: types.CallbackQuery):
    await callback.message.answer("💰 Ваш баланс: 3 токена (тестовое значение).")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "deposit")
async def show_deposit(callback: types.CallbackQuery):
    await callback.message.answer("💳 Для пополнения переведите на карту: `2204 3212 5674 4475`\nЗатем пришлите скриншот админу.", parse_mode="Markdown")
    await callback.answer()

# Запускаем бота в фоне при старте сервера
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(dp.start_polling(bot))

# Этот блок нужен, если запускать локально
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
