
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
API_TOKEN = '8311250772:AAEG4WWfEFf3axJitF3xgPsVe7ozjMwwE2I'
CRYPTO_PAY_TOKEN = '523191:AAboyI61aKwD8GmdufeKXn1kdCfwPWyDh82'
ADMIN_ID = 8524326478
ITEM_PRICE = 500  # <<< ИЗМЕНИЛ ЦЕНУ НА 500 ₽

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Хранилище данных (вместо БД для примера)
user_likes = {}
user_cart = {} # Храним количество выбранного товара {user_id: количество}

# --- ФУНКЦИИ КРИПТОБОТА ---

async def create_crypto_invoice(amount_rub):
    """Создает счет в CryptoBot (через фиат RUB)"""
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    payload = {
        "amount": str(amount_rub),
        "fiat": "RUB",
        "currency_type": "fiat",
        "accepted_assets": "USDT,TON,BTC,ETH,LTC,BNB",
        "description": "Оплата фишинг-ссылки",
        "allow_comments": False
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data['result']['pay_url']
            else:
                logging.error(f"Ошибка CryptoBot: {await resp.text()}")
                return None

# --- КЛАВИАТУРЫ ---

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("🎣 Все категории", "📦 Наличие товара", "🏪 О магазине", "👤 Профиль", "📜 Правила", "🆘 Помощь", "⚙️ сервис")
    return keyboard

def get_categories_keyboard():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("🔥Фишинг Ссылка🔥", callback_data="category_phishing"))

def get_phishing_category_keyboard(user_id):
    heart = "💚" if user_likes.get(user_id) == "liked" else "🤍"
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("25.01.26 обновление🔥 Фишинг Ссылка", callback_data="phishing_update"),
        InlineKeyboardButton(heart, callback_data="toggle_like"),
        InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories")
    )
    return keyboard

def get_phishing_update_keyboard(user_id):
    heart = "💚" if user_likes.get(user_id) == "liked" else "🤍"
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(f"Фишинг | {ITEM_PRICE} ₽ | ∞", callback_data="buy_phishing"))
    keyboard.row(InlineKeyboardButton("Назад", callback_data="back_to_phishing_category"),
                 InlineKeyboardButton(heart, callback_data="toggle_like"))
    keyboard.add(InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories"))
    return keyboard

def get_buy_menu_keyboard(user_id):
    heart = "💚" if user_likes.get(user_id) == "liked" else "🤍"
    qty = user_cart.get(user_id, 1)
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    keyboard.row(
        InlineKeyboardButton("➖", callback_data="qty_minus"),
        InlineKeyboardButton(f"{qty} шт.", callback_data="none"),
        InlineKeyboardButton("➕", callback_data="qty_plus")
    )
    
    keyboard.add(InlineKeyboardButton("Оплатить через Cryptobot", callback_data="pay_crypto"))
    keyboard.row(
        InlineKeyboardButton("Назад", callback_data="phishing_update"),
        InlineKeyboardButton(heart, callback_data="toggle_like")
    )
    keyboard.add(InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories"))
    return keyboard

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ---

async def delete_and_send(callback_query, text, markup):
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except:
        pass
    return await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup, parse_mode='HTML')

# --- ОБРАБОТЧИКИ ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("🌟")
    await message.answer("👋 Добро пожаловать!\nИспользуйте кнопки ниже:", reply_markup=get_main_keyboard())

@dp.message_handler(lambda m: m.text == "🎣 Все категории")
async def all_cats(message: types.Message):
    await message.answer("Выберите категорию:", reply_markup=get_categories_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'category_phishing')
async def cat_phishing(callback_query: types.CallbackQuery):
    text = "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n📃 <b>Описание:</b>\n"
    await delete_and_send(callback_query, text, get_phishing_category_keyboard(callback_query.from_user.id))

@dp.callback_query_handler(lambda c: c.data == 'phishing_update')
async def item_update(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    text = (
        f"📃 <b>Категория:</b> 25.01.26 обновление🔥 Фишинг Ссылка🔥\n"
        f"📃 <b>Описание:</b> ⭐Моментальный взлом жир Аккаунтов ⭐\n\n"
        f"Для оплаты T Bank 2200702042193321. В сообщениях перевода ИД ТГ\n"
        f"После оплаты Бот Автоматически выдаст ссылку..."
    )
    await delete_and_send(callback_query, text, get_phishing_update_keyboard(user_id))

# --- ЛОГИКА ПОКУПКИ И КРИПТОБОТА ---

@dp.callback_query_handler(lambda c: c.data == 'buy_phishing')
async def buy_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_cart[user_id] = 1 # Сброс на 1 шт при входе
    
    text = (
        f"📃 <b>Товар:</b> Фишинг\n"
        f"💰 <b>Цена:</b> {ITEM_PRICE} ₽\n"
        f"📃 <b>Описание:</b>\n\n"
        f"Выберите количество товара, которое хотите купить:"
    )
    await delete_and_send(callback_query, text, get_buy_menu_keyboard(user_id))

@dp.callback_query_handler(lambda c: c.data.startswith('qty_'))
async def change_qty(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    current_qty = user_cart.get(user_id, 1)
    
    if callback_query.data == "qty_plus":
        user_cart[user_id] = current_qty + 1
    elif callback_query.data == "qty_minus" and current_qty > 1:
        user_cart[user_id] = current_qty - 1
    
    # Обновляем сообщение (удаление + отправка)
    qty = user_cart[user_id]
    text = (
        f"📃 <b>Товар:</b> Фишинг\n"
        f"💰 <b>Цена:</b> {ITEM_PRICE * qty} ₽ ({qty} шт.)\n"
        f"📃 <b>Описание:</b>\n\n"
        f"Выберите количество товара, которое хотите купить:"
    )
    await delete_and_send(callback_query, text, get_buy_menu_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'pay_crypto')
async def process_pay(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    qty = user_cart.get(user_id, 1)
    total_rub = qty * ITEM_PRICE
    
    await callback_query.answer("Генерирую счет...")
    
    pay_url = await create_crypto_invoice(total_rub)
    
    if pay_url:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💳 Оплатить (CryptoBot)", url=pay_url))
        markup.add(InlineKeyboardButton("🔙 Назад к выбору количества", callback_data="buy_phishing"))
        
        await delete_and_send(callback_query, f"✅ Счет на {total_rub} ₽ готов!\nНажмите кнопку ниже, чтобы выбрать валюту и оплатить.", markup)
    else:
        await callback_query.answer("Ошибка API CryptoBot. Попробуйте позже.", show_alert=True)

# --- ЛАЙКИ И НАВИГАЦИЯ ---

@dp.callback_query_handler(lambda c: c.data == 'toggle_like')
async def toggle_like(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_likes[user_id] = "unliked" if user_likes.get(user_id) == "liked" else "liked"
    
    await callback_query.answer("Статус избранного обновлен")
    
    msg_text = callback_query.message.text
    if "Выберите количество" in msg_text: # Находимся в меню покупки
        qty = user_cart.get(user_id, 1)
        text = f"📃 <b>Товар:</b> Фишинг\n💰 <b>Цена:</b> {ITEM_PRICE * qty} ₽ ({qty} шт.)\n📃 <b>Описание:</b>\n\nВыберите количество товара, которое хотите купить:"
        markup = get_buy_menu_keyboard(user_id)
    elif "обновление" in msg_text: # Находимся в описании товара
        text = msg_text # Оставляем текущий текст
        markup = get_phishing_update_keyboard(user_id)
    else: # Находимся в категории
        text = "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n📃 <b>Описание:</b>\n"
        markup = get_phishing_category_keyboard(user_id)
        
    await delete_and_send(callback_query, text, markup)

@dp.callback_query_handler(lambda c: c.data == 'back_to_categories')
async def back_all(callback_query: types.CallbackQuery):
    await delete_and_send(callback_query, "Выберите категорию:", get_categories_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'back_to_phishing_category')
async def back_phishing_cat(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    text = "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n📃 <b>Описание:</b>\n"
    await delete_and_send(callback_query, text, get_phishing_category_keyboard(user_id))

@dp.message_handler(lambda m: m.text in ["📦 Наличие товара", "🏪 О магазине", "👤 Профиль", "📜 Правила", "🆘 Помощь", "⚙️ сервис"])
async def other_buttons(message: types.Message):
    await message.answer(f"Раздел '{message.text}' скоро будет доступен.")

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer("Воспользуйтесь кнопками меню или отправьте /start", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
