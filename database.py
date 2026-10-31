import sqlite3
import json
from datetime import date

DB_NAME = "tarot_bot.db"

# 🎁 Приветственный бонус для новых пользователей
WELCOME_BONUS = 3.0
DEFAULT_BALANCE = 10.0

# 🎁 Бонус за приглашённого друга
REFERRAL_BONUS = 2.0
# 🎁 Бонус новому другу, пришедшему по реф. ссылке
REFERRAL_NEW_USER_BONUS = 2.0
# 👥 Максимум успешных приглашений на одного пользователя
MAX_REFERRALS = 2
# 🎁 Ежедневный бонус
DAILY_BONUS = 1.0


def _get_columns(cursor, table: str):
    """Возвращает множество названий колонок существующей таблицы."""
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def _safe_add_column(cursor, table: str, column: str, coltype: str):
    """Безопасно добавляет колонку, если её нет. Ничего не делает, если есть."""
    cols = _get_columns(cursor, table)
    if column not in cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def _ensure_table(cursor, table: str, create_sql: str):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not cursor.fetchone():
        cursor.execute(create_sql)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- Основная таблица пользователей ---
    _ensure_table(cursor, "users", '''
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            balance REAL DEFAULT 10.0,
            last_free_fortune DATE,
            chat_active INTEGER DEFAULT 0,
            current_cards TEXT
        )
    ''')

    # --- История чата ---
    _ensure_table(cursor, "chat_history", '''
        CREATE TABLE chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            text TEXT
        )
    ''')

    # --- 🆕 Реферальная система ---
    _ensure_table(cursor, "referrals", '''
        CREATE TABLE referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            invited_id INTEGER,
            is_referral_active INTEGER DEFAULT 0,
            rewarded INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- 🆕 Платежи (заявки на пополнение) ---
    _ensure_table(cursor, "payments", '''
        CREATE TABLE payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            tokens REAL,
            amount_rub REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- 🆕 Безопасная миграция колонок users ---
    _safe_add_column(cursor, "users", "last_daily_bonus", "DATE")
    _safe_add_column(cursor, "users", "referral_count", "INTEGER DEFAULT 0")
    _safe_add_column(cursor, "users", "referred_by", "INTEGER")

    conn.commit()
    conn.close()


def get_user(user_id, first_name="Пользователь", referred_by=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        # 🎁 Новый пользователь:
        # если пришёл по реферальной ссылке — получает только 2 токена
        # иначе — базовый баланс + приветственный бонус
        if referred_by:
            initial_balance = REFERRAL_NEW_USER_BONUS
        else:
            initial_balance = DEFAULT_BALANCE + WELCOME_BONUS

        cursor.execute(
            "INSERT INTO users (user_id, first_name, balance, referred_by) VALUES (?, ?, ?, ?)",
            (user_id, first_name, initial_balance, referred_by)
        )
        conn.commit()

        # Создаём запись о реферале (без награды — начислится после расклада)
        if referred_by:
            try:
                cursor.execute(
                    "INSERT INTO referrals (referrer_id, invited_id, is_referral_active, rewarded) VALUES (?, ?, 0, 0)",
                    (referred_by, user_id)
                )
                conn.commit()
            except Exception as e:
                print(f"[referrals] insert failed: {e}")

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


# =============== 🎁 ЕЖЕДНЕВНЫЙ БОНУС ===============

def can_get_daily_bonus(user_id):
    """True, если сегодня бонус ещё не получали."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT last_daily_bonus FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()

    if res and res[0]:
        try:
            if date.fromisoformat(res[0]) == date.today():
                return False
        except (ValueError, TypeError):
            return True
    return True


def mark_daily_bonus_used(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET last_daily_bonus = ? WHERE user_id = ?",
        (date.today().isoformat(), user_id)
    )
    conn.commit()
    conn.close()


def claim_daily_bonus(user_id):
    """Пытается начислить ежедневный бонус. Возвращает True, если начислен."""
    if not can_get_daily_bonus(user_id):
        return False
    update_balance(user_id, DAILY_BONUS)
    mark_daily_bonus_used(user_id)
    return True


# =============== 📅 БЕСПЛАТНЫЙ РАСКЛАД ===============

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
            return True
    return True


def mark_free_fortune_used(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_free_fortune = ? WHERE user_id = ?", (date.today().isoformat(), user_id))
    conn.commit()
    conn.close()


# =============== 💬 ЧАТ ===============

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


# =============== 👥 РЕФЕРАЛЫ ===============

def get_referral_count(user_id):
    """Сколько успешных (оплаченных раскладом) приглашений у пользователя."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT referral_count FROM users WHERE user_id = ?", (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0


def activate_referral(invited_id):
    """
    Вызывается при первом успешном раскладе приглашённого.
    - Помечает реферал активным.
    - Если реферер ещё не исчерпал лимит (MAX_REFERRALS), начисляет ему бонус.
    Возвращает (referrer_id, rewarded_bool).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT referrer_id, is_referral_active, rewarded FROM referrals WHERE invited_id = ?",
        (invited_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None, False

    referrer_id, is_active, rewarded = row
    if is_active or rewarded:
        conn.close()
        return referrer_id, False

    # Активируем реферал
    cursor.execute(
        "UPDATE referrals SET is_referral_active = 1 WHERE invited_id = ?",
        (invited_id,)
    )

    # Проверяем лимит реферера
    cursor.execute("SELECT referral_count FROM users WHERE user_id = ?", (referrer_id,))
    cnt_row = cursor.fetchone()
    ref_count = cnt_row[0] if cnt_row and cnt_row[0] else 0

    rewarded_now = False
    if ref_count < MAX_REFERRALS:
        cursor.execute(
            "UPDATE users SET balance = balance + ?, referral_count = referral_count + 1 WHERE user_id = ?",
            (REFERRAL_BONUS, referrer_id)
        )
        cursor.execute(
            "UPDATE referrals SET rewarded = 1 WHERE invited_id = ?",
            (invited_id,)
        )
        rewarded_now = True

    conn.commit()
    conn.close()
    return referrer_id, rewarded_now


def get_referrer_of(user_id):
    """Возвращает referred_by (кто пригласил) или None."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


# =============== 💳 ПЛАТЕЖИ ===============

def create_payment(user_id, user_name, tokens, amount_rub):
    """Создаёт заявку на пополнение. Возвращает payment_id."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO payments (user_id, user_name, tokens, amount_rub, status) VALUES (?, ?, ?, ?, 'pending')",
        (user_id, user_name, tokens, amount_rub)
    )
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return payment_id


def get_payment(payment_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, user_name, tokens, amount_rub, status FROM payments WHERE id = ?",
        (payment_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0], "user_id": row[1], "user_name": row[2],
        "tokens": row[3], "amount_rub": row[4], "status": row[5]
    }


def confirm_payment(payment_id):
    """Подтверждает платёж: начисляет токены. Возвращает dict или None."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, tokens, status FROM payments WHERE id = ?", (payment_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    user_id, tokens, status = row
    if status != "pending":
        conn.close()
        return {"status": status, "user_id": user_id, "tokens": tokens}

    cursor.execute(
        "UPDATE payments SET status = 'confirmed' WHERE id = ?", (payment_id,)
    )
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?", (tokens, user_id)
    )
    conn.commit()
    conn.close()
    return {"status": "confirmed", "user_id": user_id, "tokens": tokens}


def cancel_payment(payment_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE payments SET status = 'cancelled' WHERE id = ? AND status = 'pending'",
        (payment_id,)
    )
    conn.commit()
    conn.close()


# 🚀 Инициализация при импорте
init_db()
