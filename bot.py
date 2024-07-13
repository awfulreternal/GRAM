import telebot
import sqlite3
import time
import random

API_TOKEN = '7294993191:AAHKGun4DVdrlUyMUDmJTtKhk7Dn_UD52Uc'
bot = telebot.TeleBot(API_TOKEN)

# Подключаемся к базе данных
try:
    conn = sqlite3.connect('users.db', check_same_thread=False)
except sqlite3.Error as e:
    print(f"Ошибка подключения к базе данных: {e}")

# Создаем таблицу пользователей, если она не существует, и добавляем столбец bank, если его нет
try:
    with conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            balance TEXT DEFAULT '5000',
            bank TEXT DEFAULT '0',
            clan_id TEXT DEFAULT NULL,
            transfer_limit TEXT DEFAULT 'безлимит на передачу'
        )
        ''')
        conn.execute("ALTER TABLE users ADD COLUMN bank TEXT DEFAULT '0'")
except sqlite3.Error as e:
    print(f"Ошибка создания таблицы или добавления столбца: {e}")

# Функция для обновления баланса пользователя
def update_balance(user_id, new_balance):
    try:
        with conn:
            conn.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
    except sqlite3.Error as e:
        print(f"Ошибка обновления баланса: {e}")

# Функция для форматирования баланса
def format_balance(balance):
    try:
        balance = float(balance)
        if balance >= 1e20:
            return f"{balance:.0e}"
        else:
            return f"{balance:.0f}"
    except ValueError:
        return balance

# Обновляем баланс игрока с ID 1 на 30,000,000 (для тестирования)
update_balance(1, '30000000')

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    telegram_id = message.from_user.id
    try:
        with conn:
            cursor = conn.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()

        if user is None:
            with conn:
                conn.execute('INSERT INTO users (telegram_id) VALUES (?)', (telegram_id,))
            bot.send_message(telegram_id, "Добро пожаловать!\nGRAM - это виртуальная валюта. У нас можно играть в игры.\nВалюту можно передавать другим пользователям.\nЗапустив бот, вы принимаете пользовательское соглашение на пользование ботом.")
        else:
            bot.send_message(telegram_id, "Вы уже зарегистрированы.")
    except sqlite3.Error as e:
        bot.send_message(telegram_id, f"Ошибка базы данных: {e}")

# Обработчик команды профиль
@bot.message_handler(func=lambda message: message.text.lower() == 'профиль')
def handle_profile(message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    try:
        with conn:
            cursor = conn.execute('SELECT id, balance, bank, clan_id, transfer_limit FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()

        if user:
            bot_user_id, balance, bank, clan_id, transfer_limit = user
            formatted_balance = format_balance(balance)
            formatted_bank = format_balance(bank)
            profile_link = f"<a href='https://t.me/{username}'>{username}</a>"
            clan_display = clan_id if clan_id else '-'
            profile_message = f"{profile_link}, ваш профиль:\n🪪 ID: {bot_user_id}\n🏆 Статус: Обычный\n💰 Баланс: {formatted_balance} грамм\n🏦 Банк: {formatted_bank} грамм\n🏰 Клан: {clan_display}\n💸 Лимит на передачу: {transfer_limit}"
            bot.send_message(telegram_id, profile_message, parse_mode='HTML', disable_web_page_preview=True)
        else:
            bot.send_message(telegram_id, "Профиль не найден. Пожалуйста, используйте команду /start для регистрации.")
    except sqlite3.Error as e:
        bot.send_message(telegram_id, f"Ошибка базы данных: {e}")

# Обработчик команды баланс или б
@bot.message_handler(func=lambda message: message.text.lower() in ['баланс', 'б'])
def handle_balance(message):
    telegram_id = message.from_user.id
    try:
        with conn:
            cursor = conn.execute('SELECT balance FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()

        if user:
            balance = user[0]
            formatted_balance = format_balance(balance)
            bot.send_message(telegram_id, f"💰 Баланс GRAM: {formatted_balance}")
        else:
            bot.send_message(telegram_id, "Профиль не найден. Пожалуйста, используйте команду /start для регистрации.")
    except sqlite3.Error as e:
        bot.send_message(telegram_id, f"Ошибка базы данных: {e}")

# Обработчик команды команды
@bot.message_handler(func=lambda message: message.text.lower() == 'команды')
def handle_commands(message):
    commands_list = (
        "/start - Начало работы с ботом и регистрация",
        "профиль - Показать ваш профиль",
        "баланс или б - Показать ваш текущий баланс",
        "команды - Показать список всех команд",
        "казино (сумма) - Сыграть в казино"
    )
    bot.send_message(message.chat.id, "Доступные команды:\n" + "\n".join(commands_list))

# Обработчик команды казино
@bot.message_handler(func=lambda message: message.text.lower().startswith('казино'))
def handle_casino(message):
    telegram_id = message.from_user.id
    try:
        amount = float(message.text.split()[1])
        with conn:
            cursor = conn.execute('SELECT balance FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()

        if user:
            balance = float(user[0])
            if amount > balance:
                bot.send_message(telegram_id, "Недостаточно средств для ставки.")
            else:
                if random.choice([True, False]):
                    new_balance = balance + amount
                    bot.send_message(telegram_id, f"Поздравляем! Вы выиграли {amount} грамм. Ваш новый баланс: {format_balance(new_balance)}")
                else:
                    new_balance = balance - amount
                    bot.send_message(telegram_id, f"К сожалению, вы проиграли {amount} грамм. Ваш новый баланс: {format_balance(new_balance)}")
                update_balance(user[0], str(new_balance))
        else:
            bot.send_message(telegram_id, "Профиль не найден. Пожалуйста, используйте команду /start для регистрации.")
    except (IndexError, ValueError):
        bot.send_message(telegram_id, "Пожалуйста, укажите сумму для ставки. Пример: казино 100")
    except sqlite3.Error as e:
        bot.send_message(telegram_id, f"Ошибка базы данных: {e}")

# Функция для запуска бота с повторными попытками в случае таймаута
def start_bot():
    while True:
        try:
            bot.polling()
        except Exception as e:
            print(f"Ошибка при запуске бота: {e}")
            time.sleep(15)  # Ждем 15 секунд перед повторной попыткой

start_bot()
