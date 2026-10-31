import sqlite3
import json
from datetime import date

DB_NAME = "tarot_bot.db"

# 🎁 Приветственный бонус для новых пользователей
WELCOME_BONUS = 3.0
DEFAULT_BALANCE = 10.0

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            balance REAL DEFAULT 10.0,
            last_free_fortune DATE,
            chat_active INTEGER DEFAULT 0,
            current_cards TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            text TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id, first_name="Пользователь"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        # 🎁 Новый пользователь: базовый баланс + приветственный бонус
        initial_balance = DEFAULT_BALANCE + WELCOME_BONUS
        cursor.execute(
            "INSERT INTO users (user_id, first_name, balance) VALUES (?, ?, ?)",
            (user_id, first_name, initial_balance)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

    conn.close()
    return user

def get_user_balance(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def add_balance_manual(user_id, amount, admin_id=None):
    """Ручное начисление админом. Возвращает новый баланс или None, если юзер не найден."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    new_balance = row[0] + amount
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()
    print(f"[ADMIN {admin_id}] Начислено {amount} токенов пользователю {user_id}. Новый баланс: {new_balance}")
    return new_balance

def can_get_free_fortune(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT last_free_fortune FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()

    if res and res[0]:
        try:
            if date.fromisoformat(res[0]) == date.today():
                return False
        except (ValueError, TypeError):
            # если в БД дата в битом формате — считаем, что бесплатный расклад доступен
            return True
    return True

def mark_free_fortune_used(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_free_fortune = ? WHERE user_id = ?", (date.today().isoformat(), user_id))
    conn.commit()
    conn.close()

def save_message(user_id, role, text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (user_id, role, text) VALUES (?, ?, ?)", (user_id, role, text))
    conn.commit()
    conn.close()

def get_chat_history(user_id, limit=6):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role, text FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "text": r[1]} for r in reversed(rows)]

def clear_chat(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def set_chat_status(user_id, active, cards=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if active:
        cards_json = json.dumps(cards) if cards else None
        cursor.execute("UPDATE users SET chat_active = 1, current_cards = ? WHERE user_id = ?", (cards_json, user_id))
    else:
        cursor.execute("UPDATE users SET chat_active = 0, current_cards = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()
