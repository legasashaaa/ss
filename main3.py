import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Настройки бота
API_TOKEN = '8311250772:AAGwkOPMv3QkD5r1dJcvm7jpLtEJoNPFWmk'
ADMIN_ID = 8524326478

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота, диспетчера и хранилища состояний
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Хранилище для лайков пользователей (раздельное для категорий и товаров)
user_likes = {}

# Создание главной клавиатуры
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )
    
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

# Клавиатура для "Выберите категорию"
def get_categories_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔥Фишинг Ссылка🔥", callback_data="category_phishing")
    )
    return keyboard

# Клавиатура для категории Фишинг Ссылка
def get_phishing_category_keyboard(user_id):
    # Проверяем состояние лайка для категории
    is_liked = user_likes.get(f"{user_id}_category") == "liked_category"
    heart_state = "💚" if is_liked else "🤍"
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # 1. Первая кнопка (занимает всю ширину)
    keyboard.add(
        InlineKeyboardButton("25.01.26 обновление🔥 Фишинг Ссылка", callback_data="phishing_update")
    )
    
    # 2. Вторая строка: Назад (слева), Сердечко (справа)
    keyboard.row(
        InlineKeyboardButton("Назад", callback_data="back_to_categories"),
        InlineKeyboardButton("", callback_data="empty"),
        InlineKeyboardButton(heart_state, callback_data="toggle_like_category")
    )
    
    # 3. Кнопка "Назад ко всем категориям" по центру внизу
    keyboard.add(
        InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories")
    )
    
    return keyboard

# Клавиатура для товара обновление
def get_phishing_update_keyboard(user_id):
    # Проверяем состояние лайка для товара
    is_liked = user_likes.get(f"{user_id}_update") == "liked_update"
    heart_state = "💚" if is_liked else "🤍"
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # 1. Кнопка "Фишинг | 150 ₽ | ∞" по центру (занимает всю ширину)
    keyboard.add(
        InlineKeyboardButton("Фишинг | 150 ₽ | ∞", callback_data="buy_phishing")
    )
    
    # 2. Вторая строка: Назад (слева), Сердечко (справа)
    keyboard.row(
        InlineKeyboardButton("Назад", callback_data="back_to_phishing_category"),
        InlineKeyboardButton("", callback_data="empty"),
        InlineKeyboardButton(heart_state, callback_data="toggle_like_update")
    )
    
    # 3. Кнопка "Назад ко всем категориям" по центру внизу
    keyboard.add(
        InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories")
    )
    
    return keyboard

# Функция для удаления и отправки нового сообщения (решает проблему с расположением кнопок)
async def delete_and_send_new(message_or_callback, text, reply_markup=None, parse_mode='HTML'):
    if isinstance(message_or_callback, types.CallbackQuery):
        chat_id = message_or_callback.message.chat.id
        message_id = message_or_callback.message.message_id
        
        try:
            # Удаляем старое сообщение
            await bot.delete_message(chat_id, message_id)
        except Exception as e:
            logging.error(f"Ошибка удаления сообщения: {e}")
        
        # Отправляем новое сообщение
        await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
        await message_or_callback.answer()
    else:
        # Для обычных сообщений
        chat_id = message_or_callback.chat.id
        await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Отправляем эмодзи 🌟
    await message.answer("🌟")
    
    # Отправляем приветственное сообщение
    welcome_text = (
        "👋 Добро пожаловать в FishingScamming Bot!\n\n"
        "Это бот, в котором можно приобрести фишинг-ссылки для скама аккаунтов Pubg Mobile\n\n"
        "👇 Используйте кнопки ниже для работы с ботом"
    )
    
    await message.answer(welcome_text, parse_mode='HTML', reply_markup=get_main_keyboard())
    
    # Уведомление админу о новом пользователе
    if user_id != ADMIN_ID:
        admin_notification = (
            f"🆕 Новый пользователь:\n"
            f"ID: {user_id}\n"
            f"Username: @{username if username else 'Нет username'}\n"
            f"Имя: {message.from_user.first_name}"
        )
        await bot.send_message(ADMIN_ID, admin_notification)

# Обработчик кнопки "Все категории"
@dp.message_handler(lambda message: message.text == "🎣 Все категории")
async def all_categories(message: types.Message):
    text = "Выберите категорию:"
    
    await message.answer(text, reply_markup=get_categories_keyboard())

# Обработчик нажатия на категорию Фишинг Ссылка
@dp.callback_query_handler(lambda c: c.data == 'category_phishing')
async def process_phishing_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    text = (
        "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n"
        "📃 <b>Описание:</b>\n"
    )
    
    await delete_and_send_new(
        callback_query,
        text,
        get_phishing_category_keyboard(user_id)
    )

# Обработчик нажатия на обновление
@dp.callback_query_handler(lambda c: c.data == 'phishing_update')
async def process_phishing_update(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    text = (
        "📃 <b>Категория:</b> 25.01.26 обновление🔥 Фишинг Ссылка🔥\n"
        "📃 <b>Описание:</b> ⭐Моментальный взлом жир Аккаунтов ⭐\n\n"
        "Для оплаты T Bank 2200702042193321    В сообщениях перевода прописать свой  ИД ТГ\n"
        "После оплаты Бот Автоматически выдаст ссылку..."
    )
    
    await delete_and_send_new(
        callback_query,
        text,
        get_phishing_update_keyboard(user_id)
    )

# Обработчик пустой кнопки (для выравнивания)
@dp.callback_query_handler(lambda c: c.data == 'empty')
async def process_empty_button(callback_query: types.CallbackQuery):
    await callback_query.answer()

# Обработчик переключения лайка для категории
@dp.callback_query_handler(lambda c: c.data == 'toggle_like_category')
async def process_toggle_like_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    key = f"{user_id}_category"
    
    # Определяем текущее состояние и показываем соответствующее уведомление
    current_state = user_likes.get(key)
    if current_state == "liked_category":
        # Удаляем из избранного
        user_likes[key] = None
        notification_text = "Категория удалена из избранного"
    else:
        # Добавляем в избранное
        user_likes[key] = "liked_category"
        notification_text = "Категория добавлена в избранное"
    
    # Показываем уведомление вверху экрана
    await callback_query.answer(notification_text)
    
    # Обновляем сообщение с тем же текстом, но новым сердечком
    text = (
        "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n"
        "📃 <b>Описание:</b>\n"
    )
    
    await delete_and_send_new(
        callback_query,
        text,
        get_phishing_category_keyboard(user_id)
    )

# Обработчик переключения лайка для товара
@dp.callback_query_handler(lambda c: c.data == 'toggle_like_update')
async def process_toggle_like_update(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    key = f"{user_id}_update"
    
    # Определяем текущее состояние и показываем соответствующее уведомление
    current_state = user_likes.get(key)
    if current_state == "liked_update":
        # Удаляем из избранного
        user_likes[key] = None
        notification_text = "Товар удалён из избранного"
    else:
        # Добавляем в избранное
        user_likes[key] = "liked_update"
        notification_text = "Товар добавлен в избранное"
    
    # Показываем уведомление вверху экрана
    await callback_query.answer(notification_text)
    
    # Обновляем сообщение с тем же текстом, но новым сердечком
    text = (
        "📃 <b>Категория:</b> 25.01.26 обновление🔥 Фишинг Ссылка🔥\n"
        "📃 <b>Описание:</b> ⭐Моментальный взлом жир Аккаунтов ⭐\n\n"
        "Для оплаты T Bank 2200702042193321    В сообщениях перевода прописать свой  ИД ТГ\n"
        "После оплаты Бот Автоматически выдаст ссылку..."
    )
    
    await delete_and_send_new(
        callback_query,
        text,
        get_phishing_update_keyboard(user_id)
    )

# Обработчик возврата к категориям
@dp.callback_query_handler(lambda c: c.data == 'back_to_categories')
async def process_back_to_categories(callback_query: types.CallbackQuery):
    text = "Выберите категорию:"
    
    # Показываем уведомление "Загрузка…"
    await callback_query.answer("Загрузка…")
    
    await delete_and_send_new(
        callback_query,
        text,
        get_categories_keyboard()
    )

# Обработчик возврата к категории фишинга
@dp.callback_query_handler(lambda c: c.data == 'back_to_phishing_category')
async def process_back_to_phishing_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    text = (
        "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n"
        "📃 <b>Описание:</b>\n"
    )
    
    await delete_and_send_new(
        callback_query,
        text,
        get_phishing_category_keyboard(user_id)
    )

# Обработчик покупки фишинга
@dp.callback_query_handler(lambda c: c.data == 'buy_phishing')
async def process_buy_phishing(callback_query: types.CallbackQuery):
    await callback_query.answer("Товар добавлен в корзину! Для покупки пишите в ЛС.")

# Обработчик остальных кнопок главного меню (только удаляем сообщения без текста)
@dp.message_handler(lambda message: message.text in [
    "📦 Наличие товара", 
    "🏪 О магазине", 
    "👤 Профиль", 
    "📜 Правила", 
    "🆘 Помощь", 
    "⚙️ сервис"
])
async def handle_other_buttons(message: types.Message):
    # Просто удаляем предыдущее сообщение без отправки нового
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logging.error(f"Ошибка удаления сообщения: {e}")

# Обработчик остальных сообщений
@dp.message_handler()
async def echo_message(message: types.Message):
    error_text = "К сожалению я не смог распознать Вашу команду. Воспользуйтесь кнопками в меню или отправьте /start"
    
    await message.answer(error_text, reply_markup=get_main_keyboard())

# Запуск бота
if __name__ == '__main__':
    logging.info("Бот FishingScamming запущен!")
    executor.start_polling(dp, skip_updates=True)