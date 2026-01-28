import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Настройки бота
API_TOKEN = '8311250772:AAFM2QjFssNg9afqZIB0e0VxL5wSCaSgrws'
ADMIN_ID = 8524326478

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота, диспетчера и хранилища состояний
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Хранилище для лайков пользователей
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
    heart_state = "💚" if user_likes.get(user_id) == "liked" else "🤍"
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("25.01.26 обновление🔥 Фишинг Ссылка", callback_data="phishing_update")
    )
    keyboard.row(
        InlineKeyboardButton(heart_state, callback_data="toggle_like"),
        InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories")
    )
    return keyboard

# Клавиатура для товара обновление
def get_phishing_update_keyboard(user_id):
    heart_state = "💚" if user_likes.get(user_id) == "liked" else "🤍"
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Первая кнопка по середине
    keyboard.add(
        InlineKeyboardButton("Фишинг | 500 ₽ | ∞", callback_data="buy_phishing")
    )
    
    # Вторая и третья кнопки слева и справа снизу
    keyboard.row(
        InlineKeyboardButton("Назад", callback_data="back_to_phishing_category"),
        InlineKeyboardButton(heart_state, callback_data="toggle_like")
    )
    
    # Четвертая кнопка по середине
    keyboard.add(
        InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories")
    )
    
    return keyboard

# Функция для удаления предыдущего сообщения и отправки нового
async def delete_and_send_new(message_or_callback, text, reply_markup=None, parse_mode='HTML'):
    if isinstance(message_or_callback, types.CallbackQuery):
        chat_id = message_or_callback.message.chat.id
        message_id = message_or_callback.message.message_id
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception as e:
            logging.error(f"Ошибка удаления сообщения: {e}")
        await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
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
    
    await message.answer(
        text,
        reply_markup=get_categories_keyboard()
    )

# Обработчик нажатия на категорию Фишинг Ссылка
@dp.callback_query_handler(lambda c: c.data == 'category_phishing')
async def process_phishing_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    text = (
        "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n"
        "📃 <b>Описание:</b>\n\n"
        "25.01.26 обновление🔥 Фишинг Ссылка"
    )
    
    await delete_and_send_new(
        callback_query,
        text,
        get_phishing_category_keyboard(user_id)
    )
    await callback_query.answer()

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
    await callback_query.answer()

# Обработчик переключения лайка
@dp.callback_query_handler(lambda c: c.data == 'toggle_like')
async def process_toggle_like(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Переключаем состояние лайка
    if user_likes.get(user_id) == "liked":
        user_likes[user_id] = "unliked"
    else:
        user_likes[user_id] = "liked"
    
    # Определяем, на каком экране находится пользователь
    message_text = callback_query.message.text
    
    if "📃 <b>Категория:</b> 25.01.26 обновление🔥 Фишинг Ссылка🔥" in message_text:
        # На экране товара
        await delete_and_send_new(
            callback_query,
            message_text,
            get_phishing_update_keyboard(user_id)
        )
    elif "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥" in message_text:
        # На экране категории
        await delete_and_send_new(
            callback_query,
            message_text,
            get_phishing_category_keyboard(user_id)
        )
    
    await callback_query.answer("💚" if user_likes.get(user_id) == "liked" else "🤍")

# Обработчик возврата к категориям
@dp.callback_query_handler(lambda c: c.data == 'back_to_categories')
async def process_back_to_categories(callback_query: types.CallbackQuery):
    text = "Выберите категорию:"
    
    await delete_and_send_new(
        callback_query,
        text,
        get_categories_keyboard()
    )
    await callback_query.answer()

# Обработчик возврата к категории фишинга
@dp.callback_query_handler(lambda c: c.data == 'back_to_phishing_category')
async def process_back_to_phishing_category(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    text = (
        "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n"
        "📃 <b>Описание:</b>\n\n"
        "25.01.26 обновление🔥 Фишинг Ссылка"
    )
    
    await delete_and_send_new(
        callback_query,
        text,
        get_phishing_category_keyboard(user_id)
    )
    await callback_query.answer()

# Обработчик покупки фишинга
@dp.callback_query_handler(lambda c: c.data == 'buy_phishing')
async def process_buy_phishing(callback_query: types.CallbackQuery):
    await callback_query.answer("Товар добавлен в корзину! Для покупки пишите в ЛС.")

# Обработчик кнопки "Наличие товара"
@dp.message_handler(lambda message: message.text == "📦 Наличие товара")
async def stock_info(message: types.Message):
    await delete_and_send_new(
        message,
        "📊 <b>Наличие товара:</b>\n\n"
        "✅ Фишинг-ссылки - В наличии (50+)\n"
        "✅ Email шаблоны - В наличии (30+)\n"
        "✅ Веб-страницы - В наличии (20+)\n"
        "⚠️ Мобильные версии - Ограниченное количество\n"
        "✅ Банковские шаблоны - В наличии (15+)\n\n"
        "Цены и детали уточняйте в ЛС."
    )

# Обработчик кнопки "О магазине"
@dp.message_handler(lambda message: message.text == "🏪 О магазине")
async def about_shop(message: types.Message):
    await delete_and_send_new(
        message,
        "🏪 <b>О магазине FishingScamming:</b>\n\n"
        "Мы специализируемся на предоставлении материалов для:\n"
        "• Обучения кибербезопасности\n"
        "• Тестирования на проникновение\n"
        "• Повышения осведомленности о фишинге\n\n"
        "⏳ Работаем с 2021 года\n"
        "👥 69 активных пользователей\n"
        "⭐ Высокое качество материалов\n"
        "🔒 Конфиденциальность гарантирована"
    )

# Обработчик кнопки "Профиль"
@dp.message_handler(lambda message: message.text == "👤 Профиль")
async def profile_info(message: types.Message):
    user = message.from_user
    await delete_and_send_new(
        message,
        f"👤 <b>Ваш профиль:</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.first_name}\n"
        f"📛 Фамилия: {user.last_name if user.last_name else 'Не указана'}\n"
        f"🔗 Username: @{user.username if user.username else 'Не указан'}\n\n"
        f"📊 Статистика:\n"
        f"• Зарегистрирован: Сегодня\n"
        f"• Заказов: 0\n"
        f"• Баланс: 0 руб."
    )

# Обработчик кнопки "Правила"
@dp.message_handler(lambda message: message.text == "📜 Правила")
async def rules_info(message: types.Message):
    await delete_and_send_new(
        message,
        "📜 <b>Правила использования:</b>\n\n"
        "1. Использовать материалы только в образовательных целях\n"
        "2. Не применять для мошенничества или незаконной деятельности\n"
        "3. Не распространять материалы третьим лицам\n"
        "4. Оплата только через указанные способы\n"
        "5. Возврат средств - по договоренности\n"
        "6. Конфиденциальность данных - гарантирована\n\n"
        "⚠️ Нарушение правил ведет к блокировке!"
    )

# Обработчик кнопки "Помощь"
@dp.message_handler(lambda message: message.text == "🆘 Помощь")
async def help_info(message: types.Message):
    await delete_and_send_new(
        message,
        "🆘 <b>Помощь и поддержка:</b>\n\n"
        "📞 Техподдержка: @admin_username\n"
        "⏰ Время работы: 10:00-22:00 (МСК)\n"
        "📧 Email: support@fishingscamming.com\n\n"
        "<b>Частые вопросы:</b>\n"
        "• Как сделать заказ? - Напишите в ЛС\n"
        "• Способы оплаты? - Карта, крипта\n"
        "• Гарантии? - 100% качество\n"
        "• Сроки? - Моментальная выдача"
    )

# Обработчик кнопки "сервис"
@dp.message_handler(lambda message: message.text == "⚙️ сервис")
async def service_info(message: types.Message):
    await delete_and_send_new(
        message,
        "⚙️ <b>Наши услуги:</b>\n\n"
        "🎣 Создание фишинг-страниц\n"
        "🔐 Взлом аккаунтов (по запросу)\n"
        "📧 Рассылка фишинг-писем\n"
        "🛡️ Консультации по безопасности\n"
        "💻 Настройка серверов\n"
        "📊 Анализ уязвимостей\n\n"
        "Для заказа услуг пишите в ЛС."
    )

# Обработчик остальных сообщений
@dp.message_handler()
async def echo_message(message: types.Message):
    error_text = "К сожалению я не смог распознать Вашу команду. Воспользуйтесь кнопками в меню или отправьте /start"
    
    await delete_and_send_new(
        message,
        error_text,
        get_main_keyboard()
    )

# Запуск бота
if __name__ == '__main__':
    logging.info("Бот FishingScamming запущен!")
    executor.start_polling(dp, skip_updates=True)