#!/usr/bin/env python3
import asyncio
import sqlite3
import logging
from datetime import datetime

print("🔄 Загрузка модулей...")

try:
    from aiogram import Bot, Dispatcher, F
    from aiogram.filters import Command
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
    print("✅ Модули загружены")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите aiogram: pip install aiogram")
    exit(1)

# Логирование
logging.basicConfig(level=logging.INFO)

# ============ НАСТРОЙКИ ============
BOT_TOKEN = "8388656767:AAGSolSzttm1oaLGF2Hn0oSA7m1poz18WDc"  # ← ЗАМЕНИТЕ НА СВОЙ ТОКЕН!
GROUP_ID = -1003599580759
RULES_LINK = "https://t.me/+f_SxmqqvP-81ODcx"

# Проверка токена
if BOT_TOKEN == "ВАШ_ТОКЕН_БОТА" or len(BOT_TOKEN) < 40:
    print("=" * 50)
    print("❌ ОШИБКА: Вы не указали токен бота!")
    print("=" * 50)
    print("1. Получите токен у @BotFather в Telegram")
    print("2. Откройте файл bot.py")
    print("3. Замените 'ВАШ_ТОКЕН_БОТА' на реальный токен")
    print("=" * 50)
    exit(1)

print(f"✅ Токен установлен: {BOT_TOKEN[:10]}...")

# ============ ID ТЕМ В ГРУППЕ ============
TOPICS = {
    'anketa': 3,
    'rules': 4,
    'chat': 2,
}

# ============ ИНИЦИАЛИЗАЦИЯ ============
print("🔄 Инициализация бота...")
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
print("✅ Бот инициализирован")

# ============ БАЗА ДАННЫХ ============

def init_db():
    print("🔄 Инициализация базы данных...")
    conn = sqlite3.connect('anketas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anketas (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT NOT NULL,
            age TEXT NOT NULL,
            region TEXT NOT NULL,
            real_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            marital_status TEXT NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных готова")

def save_anketa(user_data):
    conn = sqlite3.connect('anketas.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO anketas 
        (user_id, nickname, age, region, real_name, gender, marital_status, username, first_name, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data['user_id'],
        user_data['nickname'],
        user_data['age'],
        user_data['region'],
        user_data['real_name'],
        user_data['gender'],
        user_data['marital_status'],
        user_data.get('username'),
        user_data.get('first_name'),
        datetime.now()
    ))
    conn.commit()
    conn.close()

def get_anketa(user_id):
    conn = sqlite3.connect('anketas.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT nickname, age, region, real_name, gender, marital_status, username, first_name, user_id
        FROM anketas WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'nickname': result[0],
            'age': result[1],
            'region': result[2],
            'real_name': result[3],
            'gender': result[4],
            'marital_status': result[5],
            'username': result[6],
            'first_name': result[7],
            'user_id': result[8]
        }
    return None

def delete_anketa_db(user_id):
    conn = sqlite3.connect('anketas.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM anketas WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_anketas_count():
    conn = sqlite3.connect('anketas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM anketas')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ============ СОСТОЯНИЯ ============
class CharacterForm(StatesGroup):
    nickname = State()
    age = State()
    region = State()
    real_name = State()
    gender = State()
    marital_status = State()

# ============ КЛАВИАТУРЫ ============

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Создать анкету")],
            [KeyboardButton(text="📋 Моя анкета"), KeyboardButton(text="❌ Удалить анкету")],
            [KeyboardButton(text="📜 Правила"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

def get_gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨 Мужской"), KeyboardButton(text="👩 Женский")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_marital_male():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💍 Женат"), KeyboardButton(text="🤵 Не женат")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_marital_female():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💍 Замужем"), KeyboardButton(text="👰 Не замужем")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def get_rules_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Читать правила", url=RULES_LINK)]
    ])

# ============ ФОРМАТИРОВАНИЕ АНКЕТЫ ============

def format_anketa(data):
    return f"""
    
║ 📝АНКЕТА ПЕРСОНАЖА ║
 

🎮 Игровой ник: {data['nickname']}
🎂 Возраст: {data['age']} лет
🌍 Регион: {data['region']}
👤 Имя: {data['real_name']}
⚧ Пол: {data['gender']}
💑 Статус: {data['marital_status']}

━━━━━━━━━━━━━━━━━━━━━━━
👤 Telegram: @{data['username'] or 'скрыт'}
🆔 ID: {data['user_id']}
━━━━━━━━━━━━━━━━━━━━━━━

✨ WIXYEEZ FAMILY ✨
    """

# ============ КОМАНДА START ============

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return
    
    await state.clear()
    
    welcome = """

║ 🎮 WIXYEEZ FAMILY 🎮 ║


👋 Добро пожаловать!

Вас приветствует семья 
✨ WIXYEEZ FAMILY ✨

━━━━━━━━━━━━━━━━━━━━━━━

📌 Выберите действие из меню!

━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    await message.answer(welcome, reply_markup=get_main_menu())

# ============ СОЗДАНИЕ АНКЕТЫ ============

@dp.message(F.text == "📝 Создать анкету")
async def start_anketa(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return
    await state.set_state(CharacterForm.nickname)
    await message.answer(
        "📝 СОЗДАНИЕ АНКЕТЫ\n\n❓ Введите ваш игровой ник:",
        reply_markup=get_cancel_keyboard()
    )

@dp.message(CharacterForm.nickname)
async def process_nickname(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
        return
    await state.update_data(nickname=message.text)
    await state.set_state(CharacterForm.age)
    await message.answer("❓ Сколько вам лет?", reply_markup=get_cancel_keyboard())

@dp.message(CharacterForm.age)
async def process_age(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
        return
    await state.update_data(age=message.text)
    await state.set_state(CharacterForm.region)
    await message.answer("❓ Укажите ваш регион:", reply_markup=get_cancel_keyboard())

@dp.message(CharacterForm.region)
async def process_region(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
        return
    await state.update_data(region=message.text)
    await state.set_state(CharacterForm.real_name)
    await message.answer("❓ Как вас зовут в жизни?", reply_markup=get_cancel_keyboard())

@dp.message(CharacterForm.real_name)
async def process_real_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
        return
    await state.update_data(real_name=message.text)
    await state.set_state(CharacterForm.gender)
    await message.answer("❓ Ваш пол:", reply_markup=get_gender_keyboard())

@dp.message(CharacterForm.gender)
async def process_gender(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
        return
    
    if "Мужской" in message.text:
        await state.update_data(gender="👨 Мужской")
        await state.set_state(CharacterForm.marital_status)
        await message.answer("❓ Семейное положение:", reply_markup=get_marital_male())
    elif "Женский" in message.text:
        await state.update_data(gender="👩 Женский")
        await state.set_state(CharacterForm.marital_status)
        await message.answer("❓ Семейное положение:", reply_markup=get_marital_female())
    else:
        await message.answer("❌ Выберите пол из кнопок")

@dp.message(CharacterForm.marital_status)
async def process_marital(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
        return
    
    await state.update_data(marital_status=message.text)
    data = await state.get_data()
    
    user_data = {
        'user_id': message.from_user.id,
        'nickname': data['nickname'],
        'age': data['age'],
        'region': data['region'],
        'real_name': data['real_name'],
        'gender': data['gender'],
        'marital_status': data['marital_status'],
        'username': message.from_user.username,
        'first_name': message.from_user.first_name
    }
    
    save_anketa(user_data)
    anketa = format_anketa(user_data)
    
    try:
        await bot.send_message(
            chat_id=GROUP_ID,
            text=anketa,
            message_thread_id=TOPICS['anketa']
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📜 Прочитать правила!", url=RULES_LINK)]
        ])
        
        await message.answer(
            "✅ АНКЕТА СОЗДАНА!\n\n"
            "📨 Отправлена в группу\n"
            "💾 Сохранена в базе\n\n"
            "⚠️ Обязательно прочитайте правила!",
            reply_markup=keyboard
        )
        
        await message.answer("Главное меню:", reply_markup=get_main_menu())
        
    except Exception as e:
        await message.answer(
            f"⚠️ Анкета сохранена, но ошибка отправки в группу:\n{e}",
            reply_markup=get_main_menu()
        )
    
    await state.clear()

# ============ МОЯ АНКЕТА ============

@dp.message(F.text == "📋 Моя анкета")
async def show_anketa(message: Message):
    if message.chat.type != "private":
        return
    
    data = get_anketa(message.from_user.id)
    if data:
        await message.answer(format_anketa(data), reply_markup=get_main_menu())
    else:
        await message.answer("❌ У вас нет анкеты!", reply_markup=get_main_menu())

# ============ УДАЛИТЬ АНКЕТУ ============

@dp.message(F.text == "❌ Удалить анкету")
async def delete_anketa(message: Message):
    if message.chat.type != "private":
        return
    
    if get_anketa(message.from_user.id):
        delete_anketa_db(message.from_user.id)
        await message.answer("✅ Анкета удалена!", reply_markup=get_main_menu())
    else:
        await message.answer("❌ Нечего удалять!", reply_markup=get_main_menu())

# ============ ПРАВИЛА ============

@dp.message(F.text == "📜 Правила")
async def show_rules(message: Message):
    if message.chat.type != "private":
        return
    await message.answer("📜 Правила семьи:", reply_markup=get_rules_keyboard())

# ============ ПОМОЩЬ ============

@dp.message(F.text == "❓ Помощь")
async def show_help(message: Message):
    if message.chat.type != "private":
        return
    await message.answer(
        "❓ ПОМОЩЬ\n\n"
        "📝 Создать анкету - заполнить анкету\n"
        "📋 Моя анкета - посмотреть свою анкету\n"
        "❌ Удалить - удалить анкету\n\n"
        "💬 В группе ответьте на сообщение\n"
        "   словом 'Описание' для просмотра анкеты",
        reply_markup=get_main_menu()
    )

# ============ ОПИСАНИЕ В ГРУППЕ ============

@dp.message(F.text.lower().contains("описание"))
async def check_anketa(message: Message):
    if message.chat.type == "private":
        return
    
    if not message.reply_to_message:
        await message.reply("💡 Ответьте на сообщение пользователя")
        return
    
    target = message.reply_to_message.from_user
    data = get_anketa(target.id)
    
    if data:
        await message.reply(format_anketa(data))
    else:
        bot_info = await bot.get_me()
        await message.reply(
            f"❌ Анкета {target.first_name} не найдена\n"
            f"💡 Напишите боту: @{bot_info.username}"
        )

# ============ ЗАПУСК ============

async def main():
    init_db()
    
    print("=" * 50)
    print("🎮 БОТ WIXYEEZ FAMILY ЗАПУЩЕН!")
    print("=" * 50)
    print(f"📊 Анкет в базе: {get_anketas_count()}")
    print("💡 Напишите /start боту в Telegram")
    print("=" * 50)
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
