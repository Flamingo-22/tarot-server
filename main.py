import os
import requests
import random
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

# --- СЛОВАРЬ ССЫЛОК НА КАРТИНКИ (ВСЕ 78 КАРТ) ---
BASE_IMG_URL = "https://raw.githubusercontent.com/ecsplendid/Rider-Waite-Tarot/master/cards/"

CARD_IMAGES = {
    "Шут": "00_fool.jpg", "Маг": "01_magician.jpg", "Верховная Жрица": "02_high_priestess.jpg",
    "Императрица": "03_empress.jpg", "Император": "04_emperor.jpg", "Иерофант": "05_hierophant.jpg",
    "Влюбленные": "06_lovers.jpg", "Колесница": "07_chariot.jpg", "Сила": "08_strength.jpg",
    "Отшельник": "09_hermit.jpg", "Колесо Фортуны": "10_wheel_of_fortune.jpg", "Справедливость": "11_justice.jpg",
    "Повешенный": "12_hanged_man.jpg", "Смерть": "13_death.jpg", "Умеренность": "14_temperance.jpg",
    "Дьявол": "15_devil.jpg", "Башня": "16_tower.jpg", "Звезда": "17_star.jpg", "Луна": "18_moon.jpg",
    "Солнце": "19_sun.jpg", "Суд": "20_judgement.jpg", "Мир": "21_world.jpg",
    "Туз Жезлов": "wands01.jpg", "Двойка Жезлов": "wands02.jpg", "Тройка Жезлов": "wands03.jpg",
    "Четверка Жезлов": "wands04.jpg", "Пятерка Жезлов": "wands05.jpg", "Шестерка Жезлов": "wands06.jpg",
    "Семерка Жезлов": "wands07.jpg", "Восьмерка Жезлов": "wands08.jpg", "Девятка Жезлов": "wands09.jpg",
    "Десятка Жезлов": "wands10.jpg", "Паж Жезлов": "wands11.jpg", "Рыцарь Жезлов": "wands12.jpg",
    "Королева Жезлов": "wands13.jpg", "Король Жезлов": "wands14.jpg",
    "Туз Кубков": "cups01.jpg", "Двойка Кубков": "cups02.jpg", "Тройка Кубков": "cups03.jpg",
    "Четверка Кубков": "cups04.jpg", "Пятерка Кубков": "cups05.jpg", "Шестерка Кубков": "cups06.jpg",
    "Семерка Кубков": "cups07.jpg", "Восьмерка Кубков": "cups08.jpg", "Девятка Кубков": "cups09.jpg",
    "Десятка Кубков": "cups10.jpg", "Паж Кубков": "cups11.jpg", "Рыцарь Кубков": "cups12.jpg",
    "Королева Кубков": "cups13.jpg", "Король Кубков": "cups14.jpg",
    "Туз Мечей": "swords01.jpg", "Двойка Мечей": "swords02.jpg", "Тройка Мечей": "swords03.jpg",
    "Четверка Мечей": "swords04.jpg", "Пятерка Мечей": "swords05.jpg", "Шестерка Мечей": "swords06.jpg",
    "Семерка Мечей": "swords07.jpg", "Восьмерка Мечей": "swords08.jpg", "Девятка Мечей": "swords09.jpg",
    "Десятка Мечей": "swords10.jpg", "Паж Мечей": "swords11.jpg", "Рыцарь Мечей": "swords12.jpg",
    "Королева Мечей": "swords13.jpg", "Король Мечей": "swords14.jpg",
    "Туз Пентаклей": "pentacles01.jpg", "Двойка Пентаклей": "pentacles02.jpg", "Тройка Пентаклей": "pentacles03.jpg",
    "Четверка Пентаклей": "pentacles04.jpg", "Пятерка Пентаклей": "pentacles05.jpg", "Шестерка Пентаклей": "pentacles06.jpg",
    "Семерка Пентаклей": "pentacles07.jpg", "Восьмерка Пентаклей": "pentacles08.jpg", "Девятка Пентаклей": "pentacles09.jpg",
    "Десятка Пентаклей": "pentacles10.jpg", "Паж Пентаклей": "pentacles11.jpg", "Рыцарь Пентаклей": "pentacles12.jpg",
    "Королева Пентаклей": "pentacles13.jpg", "Король Пентаклей": "pentacles14.jpg"
}

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

@app.get("/api/balance/{user_id}")
async def get_balance(user_id: int):
    balance = db.get_user_balance(user_id)
    return {"balance": balance}

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

    # ВЫБИРАЕМ 3 СЛУЧАЙНЫЕ КАРТЫ ИЗ 78
    selected_cards = random.sample(ALL_TAROT_CARDS, 3)

    prompt = f"""Пользователь спрашивает: '{data.question}'.
Выпали карты: {', '.join(selected_cards)}.

Ты — глубокий и загадочный таролог. Твоя задача — дать толкование, которое звучит мудро и оставляет пространство для размышлений. 
Не давай прямых и однозначных ответов (вроде "да" или "нет"). Используй метафоры, говори о скрытых энергиях и внутренних ощущениях клиента. 
Ответ должен быть на русском, объемом 150-200 слов. Разбери карты в контексте вопроса и дай совет, который заставит человека задуматься."""

    messages = [
        {"role": "system", "text": "Ты — таролог. Ты говоришь загадками и помогаешь человеку самому найти ответ."},
        {"role": "user", "text": prompt}
    ]
    
    reading = ask_yandex_gpt(messages)

    db.clear_chat(data.user_id)
    db.save_message(data.user_id, "user", f"Вопрос: {data.question}. Карты: {', '.join(selected_cards)}")
    db.save_message(data.user_id, "assistant", reading)
    db.set_chat_status(data.user_id, True, selected_cards)
    
    # Формируем список карт с картинками для отправки на сайт
    cards_data = []
    for card in selected_cards:
        image_filename = CARD_IMAGES.get(card, "back.jpg")
        cards_data.append({
            "name": card,
            "image": BASE_IMG_URL + image_filename
        })

    return {
        "status": "ok", 
        "reading": reading, 
        "cost": cost_msg, 
        "new_balance": db.get_user_balance(data.user_id),
        "cards": cards_data  # <--- ОТПРАВЛЯЕМ КАРТИНКИ НА САЙТ
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
