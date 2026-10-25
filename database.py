import sqlite3
import json
from datetime import date

DB_NAME = "tarot_bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Пользователи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            balance REAL DEFAULT 10.0, -- Дадим 10 токенов на тесты
            last_free_fortune DATE,
            chat_active INTEGER DEFAULT 0,
            current_cards TEXT
        )
    ''')
    # История чата
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
        cursor.execute("INSERT INTO users (user_id, first_name) VALUES (?, ?)", (user_id, first_name))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def can_get_free_fortune(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT last_free_fortune FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    
    if res and res[0]:
        if date.fromisoformat(res[0]) == date.today():
            return False
    return True

def mark_free_fortune_used(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_free_fortune = ? WHERE user_id = ?", (date.today().isoformat(), user_id))
    conn.commit()
    conn.close()

# Работа с чатом
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
    # Возвращаем в хронологическом порядке
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
