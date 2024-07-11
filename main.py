import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from collections import defaultdict

# Замените на свой токен, полученный у @BotFather
TOKEN = '7294993191:AAEFCphfC1PraUbSkD8IyWvTEg6qGGyvAtQ'

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Данные пользователей
users_data = defaultdict(lambda: {
    'balance': 100000,  # начальный баланс GRAM
    'businesses': {
        'Бизнес': {'level': 1, 'income': 1000},
        'Ферма': {'level': 1, 'income': 500},
        'Карьер': {'level': 1, 'income': 750}
    },
    'clan': None,
    'rating': 0,
    'limits': 'unlimited'  # лимиты: unlimited (безлимит) или 50000 GRAM
})

# Данные кланов
clans_data = defaultdict(lambda: {
    'members': [],
    'level': 1
})

# Данные для казино
casino_games = defaultdict(lambda: {
    'bet_amount': 0,
    'user_choice': None
})

# Функция для генерации случайного числа для игры в казино
def generate_random_number():
    return random.randint(0, 100)

# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    update.message.reply_text(f'Привет! Добро пожаловать в игру. Ваш баланс: {users_data[user_id]["balance"]} GRAM.')

# Обработчик команды /balance
def balance(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    update.message.reply_text(f'Ваш баланс: {users_data[user_id]["balance"]} GRAM.')

# Обработчик команды /send
def send(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    args = context.args
    if len(args) != 2:
        update.message.reply_text('Использование: /send <получатель> <сумма>')
        return
    
    recipient = args[0]
    amount = int(args[1])
    if amount <= 0 or amount > users_data[user_id]['balance']:
        update.message.reply_text('Недопустимая сумма для перевода.')
        return
    
    users_data[user_id]['balance'] -= amount
    users_data[recipient]['balance'] += amount
    update.message.reply_text(f'Вы перевели {amount} GRAM пользователю {recipient}.')

# Обработчик команды /buy_limits
def buy_limits(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    args = context.args
    if len(args) != 1 or args[0] not in ['unlimited', '50000']:
        update.message.reply_text('Использование: /buy_limits <unlimited/50000>')
        return
    
    cost = 50000
    if args[0] == 'unlimited':
        cost = 0
    
    if users_data[user_id]['balance'] < cost:
        update.message.reply_text('Недостаточно средств для покупки лимитов.')
        return
    
    users_data[user_id]['balance'] -= cost
    users_data[user_id]['limits'] = args[0]
    update.message.reply_text(f'Вы успешно купили лимиты "{args[0]}".')

# Обработчик команды /businesses
def businesses(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    businesses_info = users_data[user_id]['businesses']
    text = "Ваши бизнесы:\n"
    for business, info in businesses_info.items():
        text += f"{business}: Уровень {info['level']}, Доход {info['income']} GRAM\n"
    update.message.reply_text(text)

# Обработчик команды /upgrade
def upgrade(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    args = context.args
    if len(args) != 1:
        update.message.reply_text('Использование: /upgrade <Бизнес>')
        return
    
    business = args[0]
    if business not in users_data[user_id]['businesses']:
        update.message.reply_text('Неверный бизнес.')
        return
    
    cost = users_data[user_id]['businesses'][business]['level'] * 5000
    if users_data[user_id]['balance'] < cost:
        update.message.reply_text('Недостаточно средств для улучшения.')
        return
    
    users_data[user_id]['balance'] -= cost
    users_data[user_id]['businesses'][business]['level'] += 1
    users_data[user_id]['businesses'][business]['income'] += 500
    update.message.reply_text(f'Вы улучшили {business} до уровня {users_data[user_id]["businesses"][business]["level"]}.')

# Обработчик команды /casino
def casino(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    keyboard = [
        [InlineKeyboardButton("Чётное", callback_data='even'),
         InlineKeyboardButton("Нечётное", callback_data='odd')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите чётное или нечётное:', reply_markup=reply_markup)
    casino_games[user_id]['bet_amount'] = 0
    casino_games[user_id]['user_choice'] = None

# Обработчик ответов от кнопок в казино
def casino_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == 'even' or query.data == 'odd':
        casino_games[user_id]['user_choice'] = query.data
        query.message.reply_text('Введите сумму ставки:')
        context.user_data['next_step'] = 'get_bet_amount'

# Обработчик сообщений после выбора суммы ставки в казино
def casino_bet_amount(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    try:
        bet_amount = int(update.message.text)
        if bet_amount <= 0 or bet_amount > users_data[user_id]['balance']:
            update.message.reply_text('Недопустимая сумма для ставки.')
            return
        
        casino_games[user_id]['bet_amount'] = bet_amount
        random_number = generate_random_number()
        win_amount = bet_amount * 2 if random_number % 2 == 0 else 0
        if casino_games[user_id]['user_choice'] == 'odd':
            win_amount = bet_amount * 2 if random_number % 2 != 0 else 0
        
        users_data[user_id]['balance'] += win_amount
        update.message.reply_text(f'Вы угадали! Вы выиграли {win_amount} GRAM. Ваш баланс: {users_data[user_id]["balance"]} GRAM.')
    except ValueError:
        update.message.reply_text('Введите целое число.')

# Обработчик команды /spin
def spin(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if users_data[user_id]['balance'] < 100:
        update.message.reply_text('Недостаточно средств для игры в спин.')
        return
    
    users_data[user_id]['balance'] -= 100
    result = random.choice(['Вы выиграли 500 GRAM!', 'Вы выиграли 1000 GRAM!', 'Ничего не выиграли.'])
    update.message.reply_text(result + f' Ваш баланс: {users_data[user_id]["balance"]} GRAM.')

# Обработчик команды /tournament
def tournament(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    participants = random.sample(list(users_data.keys()), 5)  # выбираем случайные 5 участников турнира
    # имитация результатов турнира (случайное присвоение мест)
    random.shuffle(participants)
    results = {
        participants[0]: 100000,
        participants[1]: 70000,
        participants[2]: 50000
    }
    for i, user_id in enumerate(participants[:3]):
        users_data[user_id]['balance'] += results[user_id]
        update.message.reply_text(f'Место {i+1}: {context.bot.get_chat(user_id).first_name}, выигрыш {results[user_id]} GRAM.')

# Обработчик команды /rating
def rating(update: Update, context: CallbackContext) -> None:
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]['balance'], reverse=True)
    text = "Топ-10 игроков по балансу:\n"
    for i, (user_id, data) in enumerate(sorted_users[:10]):
        user_name = context.bot.get_chat(user_id).first_name
        text += f"{i+1}. {user_name}: {data['balance']} GRAM\n"
    update.message.reply_text(text)

def main() -> None:
    # Создаем объект Updater и передаем ему токен вашего бота.
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Регистрируем обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("balance", balance))
    dispatcher.add_handler(CommandHandler("send", send))
    dispatcher.add_handler(CommandHandler("buy_limits", buy_limits))
    dispatcher.add_handler(CommandHandler("businesses", businesses))
    dispatcher.add_handler(CommandHandler("upgrade", upgrade))
    dispatcher.add_handler(CommandHandler("casino", casino))
    dispatcher.add_handler(CommandHandler("spin", spin))
    dispatcher.add_handler(CommandHandler("tournament", tournament))
    dispatcher.add_handler(CommandHandler("rating", rating))

    # Регистрируем обработчики для кнопок в казино
    dispatcher.add_handler(CallbackQueryHandler(casino_button, pattern='^even$|^odd$'))

    # Регистрируем обработчики для сообщений после кнопок в казино
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, casino_bet_amount))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
