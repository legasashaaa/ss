

import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
API_TOKEN = '8311250772:AAF40iq3SqG77igp7d4uMwL2dSgSfLtWw54'
CRYPTO_PAY_TOKEN = '523191:AAboyI61aKwD8GmdufeKXn1kdCfwPWyDh82'
ADMIN_ID = 8524326478
ITEM_PRICE = 500  # Цена за 1 шт.

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Хранилище (в памяти)
user_likes = {}
user_cart = {} # {user_id: количество}

# --- ФУНКЦИИ CRYPTOBOT ---

async def create_crypto_invoice(amount_rub):
    """Создает счет в CryptoBot на сумму в рублях"""
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
                logging.error(f"Ошибка CryptoBot API: {await resp.text()}")
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
    keyboard.add(InlineKeyboardButton(f"Фишинг | {ITEM_PRICE} ₽ | ∞", callback_data="open_buy_menu"))
    keyboard.row(InlineKeyboardButton("Назад", callback_data="category_phishing"),
                 InlineKeyboardButton(heart, callback_data="toggle_like"))
    keyboard.add(InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories"))
    return keyboard

def get_buy_menu_keyboard(user_id):
    heart = "💚" if user_likes.get(user_id) == "liked" else "🤍"
    qty = user_cart.get(user_id, 1)
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Ряд выбора количества
    keyboard.row(
        InlineKeyboardButton("➖", callback_data="qty_minus"),
        InlineKeyboardButton(f"{qty} шт.", callback_data="none"),
        InlineKeyboardButton("➕", callback_data="qty_plus")
    )
    
    # Кнопка оплаты
    keyboard.add(InlineKeyboardButton("Оплатить через Cryptobot", callback_data="pay_crypto"))
    
    # Назад и Сердечко
    keyboard.row(
        InlineKeyboardButton("Назад", callback_data="phishing_update"),
        InlineKeyboardButton(heart, callback_data="toggle_like")
    )
    
    # Назад ко всем категориям
    keyboard.add(InlineKeyboardButton("Назад ко всем категориям", callback_data="back_to_categories"))
    return keyboard

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ---

async def delete_and_send(chat_id, message_id, text, markup):
    """Удаляет старое сообщение и шлет новое"""
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass
    return await bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

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
    user_id = callback_query.from_user.id
    text = "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n📃 <b>Описание:</b>\n"
    await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, text, get_phishing_category_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'phishing_update')
async def item_detail(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    text = (
        f"📃 <b>Категория:</b> 25.01.26 обновление🔥 Фишинг Ссылка🔥\n"
        f"📃 <b>Описание:</b> ⭐Моментальный взлом жир Аккаунтов ⭐\n\n"
        f"Для оплаты T Bank 2200702042193321. В сообщениях перевода ИД ТГ\n"
        f"После оплаты Бот Автоматически выдаст ссылку..."
    )
    await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, text, get_phishing_update_keyboard(user_id))
    await callback_query.answer()

# --- МЕНЮ ПОКУПКИ ---

@dp.callback_query_handler(lambda c: c.data == 'open_buy_menu')
async def open_buy_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_cart[user_id] = 1 # Сбрасываем количество на 1
    
    text = (
        f"📃 <b>Товар:</b> Фишинг\n"
        f"💰 <b>Цена:</b> {ITEM_PRICE} ₽\n"
        f"📃 <b>Описание:</b>\n\n"
        f"Выберите количество товара, которое хотите купить:"
    )
    await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, text, get_buy_menu_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('qty_'))
async def update_qty(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    qty = user_cart.get(user_id, 1)
    
    if callback_query.data == "qty_plus":
        qty += 1
    elif callback_query.data == "qty_minus" and qty > 1:
        qty -= 1
    
    user_cart[user_id] = qty
    total = qty * ITEM_PRICE
    
    text = (
        f"📃 <b>Товар:</b> Фишинг\n"
        f"💰 <b>Цена:</b> {total} ₽ ({qty} шт.)\n"
        f"📃 <b>Описание:</b>\n\n"
        f"Выберите количество товара, которое хотите купить:"
    )
    # Используем edit_message_reply_markup чтобы кнопки не дергались сильно, или delete_and_send по желанию
    # Но по ТЗ "всегда удаляем", так что:
    await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, text, get_buy_menu_keyboard(user_id))
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'pay_crypto')
async def pay_crypto(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    qty = user_cart.get(user_id, 1)
    total_rub = qty * ITEM_PRICE
    
    await callback_query.answer("Генерирую счет...")
    
    pay_url = await create_crypto_invoice(total_rub)
    
    if pay_url:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Оплатить в CryptoBot", url=pay_url))
        markup.add(InlineKeyboardButton("🔙 Назад к выбору", callback_data="open_buy_menu"))
        
        await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, 
                              f"✅ Счет на {total_rub} ₽ создан!\nПерейдите по кнопке ниже, чтобы оплатить.", markup)
    else:
        await callback_query.answer("Ошибка CryptoBot. Попробуйте позже.", show_alert=True)

# --- ЛАЙКИ И НАВИГАЦИЯ ---

@dp.callback_query_handler(lambda c: c.data == 'toggle_like')
async def process_toggle_like(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_likes[user_id] = "unliked" if user_likes.get(user_id) == "liked" else "liked"
    await callback_query.answer("Изменено")
    
    # Обновляем экран в зависимости от текста
    msg_text = callback_query.message.text
    if "Выберите количество" in msg_text:
        qty = user_cart.get(user_id, 1)
        text = f"📃 <b>Товар:</b> Фишинг\n💰 <b>Цена:</b> {ITEM_PRICE * qty} ₽\n📃 <b>Описание:</b>\n\nВыберите количество товара, которое хотите купить:"
        await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, text, get_buy_menu_keyboard(user_id))
    elif "обновление" in msg_text:
        await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, msg_text, get_phishing_update_keyboard(user_id))
    else:
        text = "📃 <b>Категория:</b> 🔥Фишинг Ссылка🔥\n📃 <b>Описание:</b>\n"
        await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, text, get_phishing_category_keyboard(user_id))

@dp.callback_query_handler(lambda c: c.data == 'back_to_categories')
async def back_to_cats(callback_query: types.CallbackQuery):
    await delete_and_send(callback_query.message.chat.id, callback_query.message.message_id, "Выберите категорию:", get_categories_keyboard())
    await callback_query.answer()

# Остальные кнопки главного меню
@dp.message_handler(lambda m: m.text in ["📦 Наличие товара", "🏪 О магазине", "👤 Профиль", "📜 Правила", "🆘 Помощь", "⚙️ сервис"])
async def handle_others(message: types.Message):
    await message.answer(f"Раздел {message.text} находится в разработке.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
