import os
import os
import requests
import random
import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
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

# 📞 Поддержка и отзывы
SUPPORT_USERNAME = "@polinuksisi"
REVIEWS_URL = os.getenv("REVIEWS_URL", "https://t.me/polinuksisi")

# 💳 Реквизиты
CARD_NUMBER = "2200 0101 0250 1486"
CARD_HOLDER = "Иван И."
RUB_PER_TOKEN = 10

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

# 🌐 Базовый URL картинок
BASE_IMG_URL = os.getenv(
    "BASE_IMG_URL",
    "https://cdn.jsdelivr.net/gh/Flamingo-22/tarot-cards@main/"
)
CARD_BACK_URL = os.getenv("CARD_BACK_URL", BASE_IMG_URL + "back.jpg")

CARD_IMAGES = {
    "Шут": "Major_Arcana/Major_00.jpg", "Маг": "Major_Arcana/Major_01.jpg",
    "Верховная Жрица": "Major_Arcana/Major_02.jpg", "Императрица": "Major_Arcana/Major_03.jpg",
    "Император": "Major_Arcana/Major_04.jpg", "Иерофант": "Major_Arcana/Major_05.jpg",
    "Влюбленные": "Major_Arcana/Major_06.jpg", "Колесница": "Major_Arcana/Major_07.jpg",
    "Сила": "Major_Arcana/Major_08.jpg", "Отшельник": "Major_Arcana/Major_09.jpg",
    "Колесо Фортуны": "Major_Arcana/Major_10.jpg", "Справедливость": "Major_Arcana/Major_11.jpg",
    "Повешенный": "Major_Arcana/Major_12.jpg", "Смерть": "Major_Arcana/Major_13.jpg",
    "Умеренность": "Major_Arcana/Major_14.jpg", "Дьявол": "Major_Arcana/Major_15.jpg",
    "Башня": "Major_Arcana/Major_16.jpg", "Звезда": "Major_Arcana/Major_17.jpg",
    "Луна": "Major_Arcana/Major_18.jpg", "Солнце": "Major_Arcana/Major_19.jpg",
    "Суд": "Major_Arcana/Major_20.jpg", "Мир": "Major_Arcana/Major_21.jpg",
    "Туз Жезлов": "Wands/Wands_01.jpg", "Двойка Жезлов": "Wands/Wands_02.jpg",
    "Тройка Жезлов": "Wands/Wands_03.jpg", "Четверка Жезлов": "Wands/Wands_04.jpg",
    "Пятерка Жезлов": "Wands/Wands_05.jpg", "Шестерка Жезлов": "Wands/Wands_06.jpg",
    "Семерка Жезлов": "Wands/Wands_07.jpg", "Восьмерка Жезлов": "Wands/Wands_08.jpg",
    "Девятка Жезлов": "Wands/Wands_09.jpg", "Десятка Жезлов": "Wands/Wands_10.jpg",
    "Паж Жезлов": "Wands/Wands_11.jpg", "Рыцарь Жезлов": "Wands/Wands_12.jpg",
    "Королева Жезлов": "Wands/Wands_13.jpg", "Король Жезлов": "Wands/Wands_14.jpg",
    "Туз Кубков": "Cups/Cups_01.jpg", "Двойка Кубков": "Cups/Cups_02.jpg",
    "Тройка Кубков": "Cups/Cups_03.jpg", "Четверка Кубков": "Cups/Cups_04.jpg",
    "Пятерка Кубков": "Cups/Cups_05.jpg", "Шестерка Кубков": "Cups/Cups_06.jpg",
    "Семерка Кубков": "Cups/Cups_07.jpg", "Восьмерка Кубков": "Cups/Cups_08.jpg",
    "Девятка Кубков": "Cups/Cups_09.jpg", "Десятка Кубков": "Cups/Cups_10.jpg",
    "Паж Кубков": "Cups/Cups_11.jpg", "Рыцарь Кубков": "Cups/Cups_12.jpg",
    "Королева Кубков": "Cups/Cups_13.jpg", "Король Кубков": "Cups/Cups_14.jpg",
    "Туз Мечей": "Swords/Swords_01.jpg", "Двойка Мечей": "Swords/Swords_02.jpg",
    "Тройка Мечей": "Swords/Swords_03.jpg", "Четверка Мечей": "Swords/Swords_04.jpg",
    "Пятерка Мечей": "Swords/Swords_05.jpg", "Шестерка Мечей": "Swords/Swords_06.jpg",
    "Семерка Мечей": "Swords/Swords_07.jpg", "Восьмерка Мечей": "Swords/Swords_08.jpg",
    "Девятка Мечей": "Swords/Swords_09.jpg", "Десятка Мечей": "Swords/Swords_10.jpg",
    "Паж Мечей": "Swords/Swords_11.jpg", "Рыцарь Мечей": "Swords/Swords_12.jpg",
    "Королева Мечей": "Swords/Swords_13.jpg", "Король Мечей": "Swords/Swords_14.jpg",
    "Туз Пентаклей": "Pents/Pents_01.jpg", "Двойка Пентаклей": "Pents/Pents_02.jpg",
    "Тройка Пентаклей": "Pents/Pents_03.jpg", "Четверка Пентаклей": "Pents/Pents_04.jpg",
    "Пятерка Пентаклей": "Pents/Pents_05.jpg", "Шестерка Пентаклей": "Pents/Pents_06.jpg",
    "Семерка Пентаклей": "Pents/Pents_07.jpg", "Восьмерка Пентаклей": "Pents/Pents_08.jpg",
    "Девятка Пентаклей": "Pents/Pents_09.jpg", "Десятка Пентаклей": "Pents/Pents_10.jpg",
    "Паж Пентаклей": "Pents/Pents_11.jpg", "Рыцарь Пентаклей": "Pents/Pents_12.jpg",
    "Королева Пентаклей": "Pents/Pents_13.jpg", "Король Пентаклей": "Pents/Pents_14.jpg",
}

# 🆕 Хранилище для отложенных подтверждений платежей (в памяти процесса)
# {payment_id: asyncio.Task}
PENDING_PAYMENTS = {}


# ================= Pydantic-модели =================

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


# ================= YandexGPT =================

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


async def notify_admin_telegram(text: str):
    """Помимо ntfy — уведомление админу в личку Telegram."""
    if not ADMIN_ID:
        return
    try:
        await bot.send_message(ADMIN_ID, text)
    except Exception as e:
        print(f"[admin notify] {e}")


# ================= REST API (как было) =================

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

    # 🆕 Активация реферала после первого расклада приглашённого
    try:
        referrer_id, rewarded = db.activate_referral(data.user_id)
        if referrer_id and rewarded:
            asyncio.create_task(_notify_referrer_about_reward(referrer_id))
    except Exception as e:
        print(f"[referral activation] {e}")

    return {
        "status": "ok",
        "reading": reading,
        "cost": cost_msg,
        "new_balance": db.get_user_balance(data.user_id),
        "cards": cards_data
    }


async def _notify_referrer_about_reward(referrer_id: int):
    try:
        await bot.send_message(
            referrer_id,
            "🎉 Ваш приглашённый друг сделал первый расклад!\n"
            "Вам начислено +2 токена 💎"
        )
    except Exception as e:
        print(f"[notify referrer] {e}")


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
    """Старый эндпоинт из Mini App — оставлен для совместимости."""
    send_ntfy_notification(f"Гость {data.user_id} ({data.user_name}) заявил об оплате. Проверьте перевод.")
    return {"status": "ok", "message": "Уведомление отправлено."}


# ================= Telegram-клавиатуры =================

def main_menu_keyboard():
    web_app = WebAppInfo(url=WEBAPP_URL)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Открыть гадалку", web_app=web_app)],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="menu_balance")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="menu_topup")],
        [InlineKeyboardButton(text="👥 Пригласить друга", callback_data="menu_referral")],
        [InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="menu_daily")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="menu_reviews"),
         InlineKeyboardButton(text="🆘 Поддержка", callback_data="menu_support")],
    ])


def topup_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 токенов (50 ₽)", callback_data="pay_5"),
         InlineKeyboardButton(text="6 токенов (60 ₽)", callback_data="pay_6")],
        [InlineKeyboardButton(text="10 токенов (100 ₽)", callback_data="pay_10")],
        [InlineKeyboardButton(text="✏️ Своя сумма", callback_data="pay_custom")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_main")],
    ])


def back_to_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_main")]
    ])


def back_to_topup_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_topup")]
    ])


# ================= /start =================

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    args = message.text.split()

    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            candidate = int(args[1].replace("ref_", ""))
            if candidate != message.from_user.id:
                referred_by = candidate
        except ValueError:
            pass

    # 🆕 get_user сам создаст пользователя (с 2 токенами, если по реф. ссылке)
    db.get_user(message.from_user.id, message.from_user.first_name, referred_by=referred_by)

    # 🆕 Ежедневный бонус — начисляется при заходе
    daily_granted = db.claim_daily_bonus(message.from_user.id)
    daily_line = "🎁 Ежедневный бонус: +1 токен!" if daily_granted else "🎁 Ежедневный бонус уже получен сегодня."

    try:
        await message.answer(
            f"✨ Привет, {message.from_user.first_name}!\n\n"
            f"Добро пожаловать в «Мистическое Таро» 🔮\n"
            f"Загадай вопрос — карты дадут ответ. Первый расклад сегодня — бесплатный!\n\n"
            f"{daily_line}",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        print(f"[start] {e}")


# ================= 💰 БАЛАНС =================

@dp.callback_query(lambda c: c.data == "menu_balance")
async def cb_balance(callback: types.CallbackQuery):
    try:
        b = db.get_user_balance(callback.from_user.id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить", callback_data="menu_topup")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_main")],
        ])
        await callback.message.edit_text(
            f"💰 Ваш баланс: *{b}* токенов.\n\n1 токен = 10 руб.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"[cb_balance] {e}")
    await callback.answer()


# ================= 💳 ПОПОЛНЕНИЕ =================

@dp.callback_query(lambda c: c.data == "menu_topup")
async def cb_topup_menu(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text(
            "💳 На сколько токенов хотите пополнить?\n\n"
            f"1 токен = {RUB_PER_TOKEN} руб.",
            reply_markup=topup_keyboard()
        )
    except Exception as e:
        print(f"[cb_topup] {e}")
    await callback.answer()


async def _start_payment_flow(callback: types.CallbackQuery, tokens: float):
    """Создаёт платёж и показывает реквизиты."""
    amount_rub = tokens * RUB_PER_TOKEN
    payment_id = db.create_payment(
        callback.from_user.id, callback.from_user.first_name, tokens, amount_rub
    )

    pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я перевёл", callback_data=f"paid_{payment_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_topup")],
    ])

    try:
        await callback.message.edit_text(
            f"💳 *Реквизиты для оплаты*\n\n"
            f"Карта: `{CARD_NUMBER}`\n"
            f"Получатель: {CARD_HOLDER}\n\n"
            f"Сумма: *{amount_rub} ₽* ({tokens:g} токенов)\n\n"
            f"Переведите указанную сумму и нажмите «✅ Я перевёл».",
            parse_mode="Markdown",
            reply_markup=pay_keyboard
        )
    except Exception as e:
        print(f"[payment flow] {e}")
    await callback.answer()


@dp.callback_query(lambda c: c.data in ("pay_5", "pay_6", "pay_10"))
async def cb_pay_preset(callback: types.CallbackQuery):
    tokens = int(callback.data.replace("pay_", ""))
    await _start_payment_flow(callback, tokens)


@dp.callback_query(lambda c: c.data == "pay_custom")
async def cb_pay_custom(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text(
            "✏️ Напишите число — на сколько токенов хотите пополнить?\n"
            "Например: `7`",
            parse_mode="Markdown",
            reply_markup=back_to_topup_keyboard()
        )
    except Exception as e:
        print(f"[custom] {e}")
    await callback.answer()


@dp.message()
async def handle_custom_amount(message: types.Message):
    """Ловим текстовый ввод суммы токенов (только если число)."""
    if not message.text:
        return
    text = message.text.strip()
    if not text.replace(".", "", 1).isdigit():
        return
    try:
        tokens = float(text)
    except ValueError:
        return
    if tokens <= 0 or tokens > 1000:
        await message.answer("⚠️ Введите число от 1 до 1000.")
        return

    amount_rub = tokens * RUB_PER_TOKEN
    payment_id = db.create_payment(
        message.from_user.id, message.from_user.first_name, tokens, amount_rub
    )

    pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я перевёл", callback_data=f"paid_{payment_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_topup")],
    ])

    try:
        await message.answer(
            f"💳 *Реквизиты для оплаты*\n\n"
            f"Карта: `{CARD_NUMBER}`\n"
            f"Получатель: {CARD_HOLDER}\n\n"
            f"Сумма: *{amount_rub:g} ₽* ({tokens:g} токенов)\n\n"
            f"Переведите указанную сумму и нажмите «✅ Я перевёл».",
            parse_mode="Markdown",
            reply_markup=pay_keyboard
        )
    except Exception as e:
        print(f"[custom payment] {e}")


@dp.callback_query(lambda c: c.data.startswith("paid_"))
async def cb_paid(callback: types.CallbackQuery):
    try:
        payment_id = int(callback.data.replace("paid_", ""))
    except ValueError:
        await callback.answer("Ошибка платежа.")
        return

    payment = db.get_payment(payment_id)
    if not payment:
        await callback.answer("Платёж не найден.", show_alert=True)
        return
    if payment["status"] != "pending":
        await callback.answer("Этот платёж уже обработан.", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            "⏳ Проверяем платёж (3 минуты)...\n"
            "Пожалуйста, подождите — мы уведомим вас о результате."
        )
    except Exception as e:
        print(f"[cb_paid edit] {e}")

    # Уведомления админу
    admin_msg = (
        f"💳 Новый платёж #{payment_id}\n"
        f"Пользователь: {payment['user_name']} (ID: {payment['user_id']})\n"
        f"Сумма: {payment['amount_rub']:g} ₽ ({payment['tokens']:g} токенов)\n"
        f"Переведите /cancel_{payment_id} чтобы отменить, /confirm_{payment_id} — подтвердить досрочно."
    )
    send_ntfy_notification(admin_msg)
    asyncio.create_task(notify_admin_telegram(admin_msg))

    # ⏰ Отложенное подтверждение через 3 минуты
    async def auto_confirm(pid: int):
        await asyncio.sleep(180)
        result = db.confirm_payment(pid)
        if not result or result.get("status") != "confirmed":
            return
        try:
            await bot.send_message(
                result["user_id"],
                f"✅ Оплата подтверждена! Начислено {result['tokens']:g} токенов.\n"
                f"Спасибо, что с нами ✨"
            )
        except Exception as e:
            print(f"[auto confirm notify] {e}")
        send_ntfy_notification(f"✅ Платёж #{pid} автоматически подтверждён.")

    task = asyncio.create_task(auto_confirm(payment_id))
    PENDING_PAYMENTS[payment_id] = task

    await callback.answer("Платёж принят, ожидайте.")


@dp.message(Command(commands=["confirm"]))
async def admin_confirm_payment(message: types.Message):
    """Ручное подтверждение платежа админом: /confirm_<id>"""
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        return
    # aiogram разбирает /confirm_5 как команду confirm с аргументом
    parts = message.text.split("_")
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /confirm_<payment_id>")
        return
    pid = int(parts[1])

    task = PENDING_PAYMENTS.pop(pid, None)
    if task:
        task.cancel()

    result = db.confirm_payment(pid)
    if not result:
        await message.answer(f"Платёж #{pid} не найден.")
        return
    if result.get("status") != "confirmed":
        await message.answer(f"Платёж #{pid} уже в статусе: {result.get('status')}.")
        return

    await message.answer(f"✅ Платёж #{pid} подтверждён вручную.")
    try:
        await bot.send_message(
            result["user_id"],
            f"✅ Оплата подтверждена! Начислено {result['tokens']:g} токенов."
        )
    except Exception:
        pass


@dp.message(Command(commands=["cancel"]))
async def admin_cancel_payment(message: types.Message):
    """Отмена платежа админом: /cancel_<id>"""
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split("_")
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /cancel_<payment_id>")
        return
    pid = int(parts[1])

    task = PENDING_PAYMENTS.pop(pid, None)
    if task:
        task.cancel()

    payment = db.get_payment(pid)
    if not payment:
        await message.answer(f"Платёж #{pid} не найден.")
        return

    db.cancel_payment(pid)
    await message.answer(f"❌ Платёж #{pid} отменён.")
    try:
        await bot.send_message(
            payment["user_id"],
            "❌ К сожалению, платёж не подтверждён. Если вы перевели средства — напишите в поддержку."
        )
    except Exception:
        pass


# ================= 👥 РЕФЕРАЛЫ =================

@dp.callback_query(lambda c: c.data == "menu_referral")
async def cb_referral(callback: types.CallbackQuery):
    try:
        bot_username = (await bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=ref_{callback.from_user.id}"
        count = db.get_referral_count(callback.from_user.id)
        limit = db.MAX_REFERRALS

        text = (
            f"👥 *Приглашайте друзей и получайте токены!*\n\n"
            f"За каждого друга, который сделает первый расклад, вы получаете +2 токена.\n"
            f"Новый друг при регистрации получит 2 токена.\n\n"
            f"Ваша ссылка:\n`{link}`\n\n"
            f"Успешных приглашений: {count}/{limit}\n"
        )
        if count >= limit:
            text += "\n⚠️ Лимит приглашений исчерпан."

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Поделиться", url=f"https://t.me/share/url?url={link}&text=Попробуй%20Мистическое%20Таро!")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_main")],
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        print(f"[cb_referral] {e}")
    await callback.answer()


# ================= 🎁 ЕЖЕДНЕВНЫЙ БОНУС =================

@dp.callback_query(lambda c: c.data == "menu_daily")
async def cb_daily(callback: types.CallbackQuery):
    try:
        granted = db.claim_daily_bonus(callback.from_user.id)
        if granted:
            b = db.get_user_balance(callback.from_user.id)
            await callback.answer("🎁 Ежедневный бонус +1 токен!", show_alert=True)
            try:
                await callback.message.edit_text(
                    f"🎁 Ежедневный бонус получен: *+1 токен!*\n\n"
                    f"💰 Текущий баланс: {b} токенов.\n"
                    f"Возвращайтесь завтра за новым бонусом!",
                    parse_mode="Markdown",
                    reply_markup=back_to_main_keyboard()
                )
            except Exception:
                await callback.message.answer(
                    f"🎁 Ежедневный бонус получен: +1 токен!\nБаланс: {b}",
                    reply_markup=back_to_main_keyboard()
                )
        else:
            await callback.answer("Бонус на сегодня уже получен. Приходите завтра!", show_alert=True)
    except Exception as e:
        print(f"[cb_daily] {e}")


# ================= ⭐ ОТЗЫВЫ / 🆘 ПОДДЕРЖКА =================

@dp.callback_query(lambda c: c.data == "menu_reviews")
async def cb_reviews(callback: types.CallbackQuery):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Перейти к отзывам", url=REVIEWS_URL)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")],
        ])
        await callback.message.edit_text(
            "⭐ *Отзывы*\n\n"
            "Мы будем рады вашему мнению! Поделитесь впечатлениями по ссылке ниже.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"[cb_reviews] {e}")
    await callback.answer()


@dp.callback_query(lambda c: c.data == "menu_support")
async def cb_support(callback: types.CallbackQuery):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆘 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")],
        ])
        await callback.message.edit_text(
            f"🆘 *Поддержка*\n\n"
            f"Возникли вопросы? Напишите нам: {SUPPORT_USERNAME}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        except Exception as e:
        print(f"[cb_support] {e}")
    await callback.answer()


# ================= ⬅️ НАЗАД В ГЛАВНОЕ МЕНЮ =================

@dp.callback_query(lambda c: c.data == "back_main")
async def cb_back_main(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text(
            "🔮 *Мистическое Таро*\n\n"
            "Выберите действие:",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        # Если edit_text не сработал (например, сообщение слишком старое/без изменений) —
        # отправляем новое сообщение с тем же меню, чтобы кнопки не «исчезали»
        print(f"[cb_back_main edit] {e}")
        try:
            await callback.message.answer(
                "🔮 *Мистическое Таро*\n\nВыберите действие:",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
        except Exception as e2:
            print(f"[cb_back_main answer] {e2}")
    await callback.answer()


# ================= 🚀 STARTUP =================

@app.on_event("startup")
async def on_startup():
    # Запускаем поллинг бота в фоне, чтобы FastAPI продолжал работать
    asyncio.create_task(dp.start_polling(bot))
    print("[startup] Bot polling started")


@app.on_event("shutdown")
async def on_shutdown():
    # Отменяем все отложенные задачи платежей, чтобы не было «висящих» корутин
    for pid, task in list(PENDING_PAYMENTS.items()):
        if not task.done():
            task.cancel()
    PENDING_PAYMENTS.clear()

    try:
        await bot.session.close()
    except Exception as e:
        print(f"[shutdown] {e}")
    print("[shutdown] Bot stopped")


# ================= 🏁 ENTRYPOINT =================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
