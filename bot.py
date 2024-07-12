import random
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

API_TOKEN = '7294993191:AAEFCphfC1PraUbSkD8IyWvTEg6qGGyvAtQ'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

Base = declarative_base()
engine = create_engine("sqlite:///my_game_bot.db")
Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    gram_balance = Column(Float, default=0)
    gcoin_balance = Column(Float, default0)
    health = Column(Integer, default=0)
    strength = Column(Integer, default=0)
    endurance = Column(Integer, default=0)
    block = Column(Integer, default=0)
    charisma = Column(Integer, default=0)
    intuition = Column(Integer, default=0)
    speed = Column(Integer, default=0)
    business = relationship("Business", back_populates="owner")

class Business(Base):
    __tablename__ = 'businesses'
    id = Column(Integer, primary_key=True)
    type = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="business")
    income = Column(Float, default=0)
    price = Column(Float)

class PromoCode(Base):
    __tablename__ = 'promocodes'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    reward = Column(Float)
    is_active = Column(Boolean, default=True)

Base.metadata.create_all(engine)

def get_user(username: str):
    user = session.query(User).filter_by(username=username).first()
    if not user:
        user = User(username=username)
        session.add(user)
        session.commit()
    return user

def get_upgrade_cost(stat_level):
    return 10 + stat_level * 10

def create_upgrade_keyboard(user):
    keyboard = InlineKeyboardMarkup(row_width=3)
    stats = [("Здоровье", "health", user.health), ("Сила", "strength", user.strength),
             ("Выносливость", "endurance", user.endurance), ("Блок", "block", user.block),
             ("Харизма", "charisma", user.charisma), ("Интуиция", "intuition", user.intuition), ("Скорость", "speed", user.speed)]
    for stat, callback, level in stats:
        cost = get_upgrade_cost(level)
        keyboard.insert(InlineKeyboardButton(text=f"+1 за {cost}", callback_data=f"upgrade_{callback}_{cost}"))
    return keyboard

@dp.message_handler(commands=['stats'])
async def show_stats(message: types.Message):
    user = get_user(message.from_user.username)
    stats_text = (f"Ваши характеристики\n"
                  f"Здоровье: {user.health}\n"
                  f"Сила: {user.strength}\n"
                  f"Выносливость: {user.endurance}\n"
                  f"Блок: {user.block}\n"
                  f"Харизма: {user.charisma}\n"
                  f"Интуиция: {user.intuition}\n"
                  f"Скорость: {user.speed}\n\n"
                  f"Здесь вы можете их прокачать.\n\n"
                  f"Баланс: {user.gram_balance} GRAM")
    keyboard = create_upgrade_keyboard(user)
    await message.answer(stats_text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('upgrade_'))
async def upgrade_stat(callback_query: types.CallbackQuery):
    data = callback_query.data.split('_')
    stat = data[1]
    price = int(data[2])
    user = get_user(callback_query.from_user.username)

    if user.gram_balance >= price:
        user.gram_balance -= price
        setattr(user, stat, getattr(user, stat) + 1)
        session.commit()
        await callback_query.answer(f"Вы успешно улучшили {stat}!")
    else:
        await callback_query.answer("Недостаточно средств на счету!")

    await show_stats(callback_query.message)

@dp.message_handler(commands=['duel'])
async def start_duel(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /duel <username>")
        return

    opponent_username = parts[1]
    user = get_user(message.from_user.username)
    opponent = session.query(User).filter_by(username=opponent_username).first()

    if not opponent:
        await message.answer(f"Пользователь {opponent_username} не найден.")
        return

    user_score = user.strength + user.speed + user.intuition + random.randint(0, 10)
    opponent_score = opponent.strength + opponent.speed + opponent.intuition + random.randint(0, 10)

    if user_score > opponent_score:
        result = f"Вы победили в дуэли против {opponent_username}!"
    elif user_score < opponent_score:
        result = f"Вы проиграли дуэль против {opponent_username}."
    else:
        result = f"Дуэль с {opponent_username} закончилась вничью."

    await message.answer(result)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
