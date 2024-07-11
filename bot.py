import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# Ваш токен Telegram бота
TOKEN = '7294993191:AAEFCphfC1PraUbSkD8IyWvTEg6qGGyvAtQ'

# Начальная точка для логов
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Инициализация Updater и Dispatcher для обработки команд
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Словарь для хранения данных пользователей
user_data = {}

# Основная валюта GRAM
GRAM = 'GRAM'

# Начальный баланс GRAM
INITIAL_BALANCE = 5000

# Словарь с бизнесами и их уровнями для каждого пользователя
businesses = {
    'Бизнес': 1,
    'Ферма': 1,
    'Карьер': 1
}

# Словарь с бонусами для донат статусов
donate_bonuses = {
    'Silver': {'bonus': 1.1, 'cost': 1000},
    'Gold': {'bonus': 1.2, 'cost': 2000},
    'Platinum': {'bonus': 1.5, 'cost': 5000}
}

# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {
            'gram': INITIAL_BALANCE,
            'clan': None,
            'businesses': businesses.copy(),
            'donate_status': None
        }
    update.message.reply_text(f"Добро пожаловать в игру GRAM, ваш баланс: {user_data[user_id]['gram']} {GRAM}")

# Команда /top
def top(update: Update, context: CallbackContext) -> None:
    top_list = sorted(user_data.items(), key=lambda x: x[1]['gram'], reverse=True)[:10]
    top_message = "Топ игроков по количеству GRAM:\n"
    for idx, (user_id, data) in enumerate(top_list, start=1):
        top_message += f"{idx}. {update.effective_user.first_name}: {data['gram']} {GRAM}\n"
    update.message.reply_text(top_message)

# Команда /business
def business(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for business_name, level in user_data[update.effective_user.id]['businesses'].items():
        keyboard.append([InlineKeyboardButton(f"{business_name} (Уровень {level})", callback_data=business_name)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите бизнес для улучшения:', reply_markup=reply_markup)

# Обработчик коллбэков от кнопок выбора бизнеса
def business_choice(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    business_name = query.data
    if business_name in user_data[user_id]['businesses']:
        user_data[user_id]['businesses'][business_name] += 1
        query.answer(f"Вы улучшили бизнес {business_name} до уровня {user_data[user_id]['businesses'][business_name]}!")

# Команда /donate
def donate(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for status, info in donate_bonuses.items():
        keyboard.append([InlineKeyboardButton(f"{status} (+{info['bonus']}x бонус) - {info['cost']} {GRAM}",
                                              callback_data=status)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите донат статус для покупки:', reply_markup=reply_markup)

# Обработчик коллбэков от кнопок выбора донат статуса
def donate_choice(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    status = query.data
    if status in donate_bonuses:
        if user_data[user_id]['gram'] >= donate_bonuses[status]['cost']:
            user_data[user_id]['gram'] -= donate_bonuses[status]['cost']
            user_data[user_id]['donate_status'] = status
            query.answer(f"Вы купили донат статус {status} с бонусом x{donate_bonuses[status]['bonus']}!")
        else:
            query.answer("У вас недостаточно GRAM для покупки!")

# Команда /tournament
def tournament(update: Update, context: CallbackContext) -> None:
    places = {
        1: 100000,
        2: 50000
    }
    place = random.randint(1, 2)
    user_id = update.effective_user.id
    user_data[user_id]['gram'] += places[place]
    update.message.reply_text(f"Поздравляем! Вы заняли {place} место и получили {places[place]} {GRAM}!")

# Обработчик неизвестных команд
def unknown(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Извините, такая команда не поддерживается.")

# Добавление обработчиков команд
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("top", top))
dispatcher.add_handler(CommandHandler("business", business))
dispatcher.add_handler(CommandHandler("donate", donate))
dispatcher.add_handler(CommandHandler("tournament", tournament))
dispatcher.add_handler(CallbackQueryHandler(business_choice))
dispatcher.add_handler(CallbackQueryHandler(donate_choice))

# Обработчик неизвестных команд
dispatcher.add_handler(MessageHandler(Filters.command, unknown))

# Запуск бота
def main() -> None:
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
