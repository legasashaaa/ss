import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Настройки бота
API_TOKEN = '8311250772:AAEG4WWfEFf3axJitF3xgPsVe7ozjMwwE2I'
ADMIN_ID = 8524326478

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Хранилище для лайков пользователей
user_likes = {}

# --- КЛАВИАТУРЫ ---

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("🎣 Все категории"),
        KeyboardButton("📦 Наличие товара"),
        KeyboardButton("🏪 О магазине"),
        KeyboardButton("👤 Профиль"),
        KeyboardButton("📜 Правила"),
        KeyboardButton("🆘 Помощь"),
        KeyboardButton("⚙️ сервис")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_categories_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔥Фишинг Ссылка🔥", callback_data="category_phishing")
    )
    return keyboard

# Клавиатура категории (вертикальная)
def get_phishing_category_keyboard(user_id):
    heart_state = "💚" if user_likes.get(user_id) == "liked" else "🤍"
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("25.01.26 обновление🔥 Фишинг Ссылка", callback_data="phishing_update"),
        InlineKeyboardButton(heart_state, callback_data="toggle_like"),
        InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories")
    )
    return keyboard

# Клавиатура товара (специфическое расположение)
def get_phishing_update_keyboard(user_id):
    heart_state = "💚" if user_likes.get(user_id) == "liked" else "🤍"
    keyboard = InlineKeyboardMarkup(row_width=2)
    # 1. Кнопка покупки по центру
    keyboard.add(InlineKeyboardButton("Фишинг | 500 ₽ | ∞", callback_data="buy_phishing"))
    # 2. Назад и Сердечко в ряд
    keyboard.row(
        InlineKeyboardButton("Назад", callback_data="back_to_phishing_category"),
        InlineKeyboardButton(heart_state, callback_data="toggle_like")
    )
    # 3. Назад ко всем категориям снизу
    keyboard.add(InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories"))
    return keyboard

# --- ФУНКЦИЯ УДАЛЕНИЯ И ОТПРАВКИ ---

async def delete_and_send_new(callback_query, text, reply_markup=None):
    """Удаляет старое сообщение и присылает новое"""
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass
    return await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode='HTML')

# --- ОБРАБОТЧИКИ ---

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("🌟")
    welcome_text = (
        "👋 Добро пожаловать в FishingScamming Bot!\n\n"
        "Это бот, в котором можно приобрести фишинг-ссылки для скама аккаунтов Pubg Mobile\n\n"
        "👇 Используйте кнопки ниже для работы с ботом"
    )
    await message.answer(welcome_text, parse_mode='HTML', reply_markup=get_main_keyboard())

@dp.message_handler(lambda message: message.text == "🎣 Все категории")
async def all_categories(message: types.Message):
    await message.answer("Выберите категорию:", reply_markup=get_categories_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'category_phishing')
async def process_phishing_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    text = "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n📃 <b>Описание:</b>\n"
    await delete_and_send_new(callback_query, text, get_phishing_category_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'phishing_update')
async def process_phishing_update(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    text = (
        "📃 <b>Категория:</b> 25.01.26 обновление🔥 Фишинг Ссылка🔥\n"
        "📃 <b>Описание:</b> ⭐Моментальный взлом жир Аккаунтов ⭐\n\n"
        "Для оплаты T Bank 2200702042193321    В сообщениях перевода прописать свой  ИД ТГ\n"
        "После оплаты Бот Автоматически выдаст ссылку..."
    )
    await delete_and_send_new(callback_query, text, get_phishing_update_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'toggle_like')
async def process_toggle_like(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # 1. Переключаем лайк
    if user_likes.get(user_id) == "liked":
        user_likes[user_id] = "unliked"
        notification = "Товар удалён из избранного"
    else:
        user_likes[user_id] = "liked"
        notification = "Товар добавлен в избранное"
    
    await callback_query.answer(notification)

    # 2. Определяем, где мы были, чтобы вернуть ту же клавиатуру и текст
    current_text = callback_query.message.text
    
    # Проверяем наличие ключевого слова "обновление" в тексте сообщения
    if "обновление" in current_text:
        # Мы на странице ТОВАРА
        text = (
            "📃 <b>Категория:</b> 25.01.26 обновление🔥 Фишинг Ссылка🔥\n"
            "📃 <b>Описание:</b> ⭐Моментальный взлом жир Аккаунтов ⭐\n\n"
            "Для оплаты T Bank 2200702042193321    В сообщениях перевода прописать свой  ИД ТГ\n"
            "После оплаты Бот Автоматически выдаст ссылку..."
        )
        markup = get_phishing_update_keyboard(user_id)
    else:
        # Мы на странице КАТЕГОРИИ
        text = "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n📃 <b>Описание:</b>\n"
        markup = get_phishing_category_keyboard(user_id)

    # 3. ВСЕГДА удаляем и присылаем заново
    await delete_and_send_new(callback_query, text, markup)

@dp.callback_query_handler(lambda c: c.data == 'back_to_categories')
async def process_back_to_categories(callback_query: types.CallbackQuery):
    await callback_query.answer("Загрузка…")
    await delete_and_send_new(callback_query, "Выберите категорию:", get_categories_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'back_to_phishing_category')
async def process_back_to_phishing_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    text = "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n📃 <b>Описание:</b>\n"
    await delete_and_send_new(callback_query, text, get_phishing_category_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'buy_phishing')
async def process_buy_phishing(callback_query: types.CallbackQuery):
    await callback_query.answer("Для покупки следуйте инструкции в описании!", show_alert=True)

@dp.message_handler(lambda message: message.text in ["📦 Наличие товара", "🏪 О магазине", "👤 Профиль", "📜 Правила", "🆘 Помощь", "⚙️ сервис"])
async def handle_other_buttons(message: types.Message):
    await message.answer(f"Раздел '{message.text}' скоро будет доступен.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
