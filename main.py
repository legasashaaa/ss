import asyncio
import re
import json
import aiohttp
from datetime import datetime
from telethon import TelegramClient, events, errors
from telethon.tl.types import MessageEntityMention, MessageEntityHashtag
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, Channel, Chat
from telethon.tl.custom import Button
import logging

# ==================== НАСТРОЙКИ ====================
# ВСТАВЬТЕ СВОИ ДАННЫЕ ЗДЕСЬ:
API_ID = 38509244  # Получите на my.telegram.org (цифры)
API_HASH = 'ae8417e55fded8fb8f592d0bc62278c5'  # Получите на my.telegram.org (строка)
BOT_TOKEN = '8055671210:AAGEm_lVaAMYRQfYQ7RcA3krwyjBZauVj3w'  # Получите у @BotFather
SESSION_NAME = '+380994588662'  # Ваша сессия Telethon

# Настройки поиска
MAX_CHATS_PER_SEARCH = 100  # Максимум чатов для поиска
MESSAGES_PER_CHAT = 2000    # Максимум сообщений на чат для анализа
ITEMS_PER_PAGE = 8          # Элементов на странице
CHATS_PER_PAGE = 8          # Чатов на странице
MESSAGES_PER_PAGE = 5       # Сообщений на странице

# Файл с чатами
CHATS_FILE = 'chat.txt'
# ===================================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация клиентов
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Словари для хранения данных
user_states = {}  # Состояния пользователей
search_results = {}  # Результаты поиска
user_data = {}  # Данные пользователей

class UserState:
    def __init__(self, user_id):
        self.user_id = user_id
        self.searching = False
        self.current_username = None
        self.current_keyword = None
        self.waiting_for_keyword = False
        self.current_page = 1
        self.results = []
        self.found_messages = []
        self.chats_list = []

class Paginator:
    def __init__(self, data, items_per_page=10):
        self.data = data
        self.items_per_page = items_per_page
        self.total_pages = (len(data) + items_per_page - 1) // items_per_page if data else 1
    
    def get_page(self, page):
        if not self.data:
            return [], self.total_pages
        start = (page - 1) * self.items_per_page
        end = start + self.items_per_page
        return self.data[start:end], self.total_pages

# Чтение чатов из файла
def load_chats():
    chats = []
    try:
        with open(CHATS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Обработка разных форматов ссылок
                    if 't.me/' in line:
                        # Удаляем префикс https://t.me/
                        username = line.split('t.me/')[-1]
                        if username.startswith('+'):
                            username = username[1:]
                        if '/' in username:
                            username = username.split('/')[0]
                        if username not in chats:
                            chats.append(username)
                    elif line.startswith('@'):
                        username = line[1:]
                        if username not in chats:
                            chats.append(username)
                    else:
                        if line not in chats:
                            chats.append(line)
    except FileNotFoundError:
        logger.error(f"Файл {CHATS_FILE} не найден!")
        # Создаем демо файл
        with open(CHATS_FILE, 'w', encoding='utf-8') as f:
            f.write("@testchat\n@anotherchat\nhttps://t.me/+tmE98W5NO6xlYmQy")
        chats = ["testchat", "anotherchat", "tmE98W5NO6xlYmQy"]
    
    logger.info(f"Загружено {len(chats)} чатов")
    return chats

# Получение состояния пользователя
def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = UserState(user_id)
    return user_states[user_id]

# Сохранение состояния
def save_state(user_id):
    state = get_user_state(user_id)
    data = {
        'current_username': state.current_username,
        'results': state.results,
        'found_messages': state.found_messages,
        'chats_list': state.chats_list,
        'timestamp': datetime.now().isoformat()
    }
    try:
        with open(f'state_{user_id}.json', 'w') as f:
            json.dump(data, f)
    except:
        pass

# Загрузка состояния
def load_state(user_id):
    try:
        with open(f'state_{user_id}.json', 'r') as f:
            data = json.load(f)
            state = get_user_state(user_id)
            state.current_username = data.get('current_username')
            state.results = data.get('results', [])
            state.found_messages = data.get('found_messages', [])
            state.chats_list = data.get('chats_list', [])
            return True
    except:
        return False

# Получение ссылки на чат
def get_chat_link(chat_username):
    if chat_username.startswith('+'):
        return f"https://t.me/{chat_username}"
    elif any(c.isdigit() for c in chat_username):
        return f"https://t.me/+{chat_username}"
    else:
        return f"https://t.me/{chat_username}"

# ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Обработчик команды /start"""
    user_id = event.sender_id
    state = get_user_state(user_id)
    state.searching = False
    state.waiting_for_keyword = False
    
    await event.reply(
        "👋 **Бот-фазер активирован!**\n\n"
        "🚀 **Возможности:**\n"
        "• Поиск пользователя по юзернейму\n"
        "• Статистика по чатам и сообщениям\n"
        "• Поиск конкретных сообщений\n"
        "• Быстрый переход к чатам\n\n"
        "📝 **Использование:**\n"
        "Просто отправьте юзернейм пользователя в формате:\n"
        "`@username` или просто `username`\n\n"
        "⚡ **Быстрый поиск без лимитов!**",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Обработчик команды /help"""
    await event.reply(
        "📖 **Справка по использованию бота:**\n\n"
        "1. **Поиск пользователя:**\n"
        "   Отправьте `@username` или `username`\n\n"
        "2. **После поиска появятся кнопки:**\n"
        "   • 📊 **Чаты пользователя** - список всех чатов со ссылками\n"
        "   • 🔎 **Найти по сообщению** - поиск по ключевому слову\n\n"
        "3. **Навигация:**\n"
        "   Используйте кнопки ⬅️ и ➡️ для перехода по страницам\n\n"
        "4. **Файл чатов:**\n"
        "   Чаты загружаются из файла `chat.txt`\n\n"
        "🔄 **Перезапуск:** /start\n"
        "📞 **Поддержка:** @ваш_аккаунт",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern=r'^(@?[a-zA-Z0-9_]{5,32})$'))
async def search_user_handler(event):
    """Обработчик поиска пользователя"""
    username = event.pattern_match.group(1).lstrip('@')
    user_id = event.sender_id
    state = get_user_state(user_id)
    
    if state.searching:
        await event.reply("⏳ Уже идет поиск! Дождитесь завершения.")
        return
    
    state.searching = True
    state.current_username = username
    state.current_page = 1
    state.results = []
    state.waiting_for_keyword = False
    
    msg = await event.reply(f"🔍 **Начинаю поиск пользователя @{username}...**\n\n"
                           "⏳ Сканирую чаты... Это может занять 1-2 минуты.")
    
    try:
        # Получаем информацию о пользователе
        try:
            user_entity = await client.get_entity(username)
            user_name = getattr(user_entity, 'first_name', '') or getattr(user_entity, 'title', '') or username
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            await msg.edit(f"❌ Пользователь @{username} не найден или недоступен!\n\n"
                          "Проверьте правильность юзернейма.")
            state.searching = False
            return
        
        chats = load_chats()
        if not chats:
            await msg.edit("❌ Список чатов пустой! Добавьте чаты в файл chat.txt")
            state.searching = False
            return
        
        results = []
        total_messages = 0
        scanned_chats = 0
        
        # Ищем пользователя в чатах
        for i, chat in enumerate(chats[:MAX_CHATS_PER_SEARCH]):
            try:
                # Обновляем статус каждые 10 чатов
                if i % 10 == 0:
                    await msg.edit(f"🔍 Сканирую чаты...\n"
                                  f"Обработано: {i}/{min(len(chats), MAX_CHATS_PER_SEARCH)}\n"
                                  f"Найдено: {len(results)} чатов")
                
                try:
                    chat_entity = await client.get_entity(chat)
                    chat_title = getattr(chat_entity, 'title', chat)
                except Exception as e:
                    logger.debug(f"Чат {chat} недоступен: {e}")
                    continue
                
                scanned_chats += 1
                
                # Проверяем, есть ли пользователь в чате
                try:
                    # Быстрая проверка через получение участников
                    participants = await client.get_participants(chat_entity, limit=100)
                    participant_ids = [p.id for p in participants if hasattr(p, 'id')]
                    
                    if hasattr(user_entity, 'id') and user_entity.id in participant_ids:
                        # Считаем сообщения пользователя
                        message_count = 0
                        try:
                            async for message in client.iter_messages(
                                chat_entity, 
                                from_user=user_entity,
                                limit=MESSAGES_PER_CHAT
                            ):
                                message_count += 1
                        except:
                            message_count = 1  # Минимум 1 если есть доступ
                        
                        if message_count > 0:
                            total_messages += message_count
                            results.append({
                                'chat': chat,
                                'title': chat_title,
                                'message_count': message_count,
                                'entity': chat_entity,
                                'link': get_chat_link(chat)
                            })
                            
                except Exception as e:
                    logger.debug(f"Ошибка проверки чата {chat}: {e}")
                    continue
                    
            except Exception as e:
                logger.debug(f"Ошибка обработки чата {chat}: {e}")
                continue
        
        state.searching = False
        state.results = results
        
        # Формируем результат
        if results:
            result_text = (
                f"✅ **Результаты поиска для @{username}**\n"
                f"👤 Имя: {user_name}\n\n"
                f"📊 **Статистика:**\n"
                f"• Всего чатов проверено: {scanned_chats}\n"
                f"• Чатов с пользователем: {len(results)}\n"
                f"• Всего сообщений: {total_messages}\n\n"
                f"🕒 Поиск занял: {datetime.now().strftime('%M:%S')}\n\n"
                f"👇 **Выберите действие:**"
            )
            
            buttons = [
                [Button.inline("📊 Показать чаты", data=f"show_chats_{username}_1")],
                [Button.inline("🔎 Найти сообщения", data=f"search_msgs_{username}")]
            ]
            
            await msg.edit(
                result_text,
                buttons=buttons
            )
            
            # Сохраняем состояние
            save_state(user_id)
            
        else:
            await msg.edit(
                f"❌ Пользователь @{username} не найден ни в одном из {scanned_chats} проверенных чатов!\n\n"
                f"Возможно:\n"
                f"1. Пользователь не состоит в этих чатах\n"
                f"2. Чаты приватные\n"
                f"3. Нет доступа к чатам"
            )
            state.searching = False
            
    except Exception as e:
        logger.error(f"Критическая ошибка поиска: {e}")
        await msg.edit("❌ Произошла критическая ошибка при поиске!")
        state.searching = False

@bot.on(events.CallbackQuery(pattern=r'show_chats_(\w+)_(\d+)'))
async def show_chats_handler(event):
    """Показ чатов пользователя с пагинацией"""
    username = event.pattern_match.group(1)
    page = int(event.pattern_match.group(2))
    user_id = event.sender_id
    state = get_user_state(user_id)
    
    if not state.results:
        await event.answer("❌ Нет данных о чатах!")
        return
    
    # Используем Paginator
    paginator = Paginator(state.results, CHATS_PER_PAGE)
    page_data, total_pages = paginator.get_page(page)
    
    if not page_data:
        await event.answer("❌ Нет данных для этой страницы!")
        return
    
    # Формируем текст
    text = f"📊 **Чаты пользователя @{username}**\n\n"
    
    for i, result in enumerate(page_data):
        idx = (page - 1) * CHATS_PER_PAGE + i + 1
        chat_title = result['title']
        message_count = result['message_count']
        chat_link = result['link']
        
        text += f"{idx}. **{chat_title}**\n"
        text += f"   💬 Сообщений: {message_count}\n"
        text += f"   🔗 [Перейти в чат]({chat_link})\n\n"
    
    text += f"📄 Страница {page}/{total_pages}"
    
    # Создаем кнопки навигации
    buttons = []
    
    # Кнопки пагинации
    nav_row = []
    if page > 1:
        nav_row.append(Button.inline("⬅️ Назад", data=f"show_chats_{username}_{page-1}"))
    
    nav_row.append(Button.inline(f"{page}/{total_pages}", data="noop"))
    
    if page < total_pages:
        nav_row.append(Button.inline("Вперед ➡️", data=f"show_chats_{username}_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Кнопка поиска сообщений
    buttons.append([Button.inline("🔎 Найти сообщения", data=f"search_msgs_{username}")])
    
    # Кнопка возврата
    buttons.append([Button.inline("🔙 Назад к статистике", data=f"back_stats_{username}")])
    
    try:
        await event.edit(text, buttons=buttons, link_preview=False)
    except Exception as e:
        logger.error(f"Ошибка редактирования: {e}")
        await event.answer("⚠️ Ошибка обновления!")

@bot.on(events.CallbackQuery(pattern=r'search_msgs_(\w+)'))
async def search_messages_handler(event):
    """Начало поиска по сообщениям"""
    username = event.pattern_match.group(1)
    user_id = event.sender_id
    state = get_user_state(user_id)
    
    if state.searching:
        await event.answer("⏳ Уже идет поиск! Подождите.")
        return
    
    state.waiting_for_keyword = True
    state.current_username = username
    state.current_keyword = None
    state.found_messages = []
    
    await event.edit(
        f"🔍 **Поиск сообщений от @{username}**\n\n"
        "Введите ключевое слово или фразу для поиска:\n"
        "(бот найдет все сообщения, содержащие этот текст)\n\n"
        "Пример: `привет` или `как дела`\n\n"
        "❌ **Отмена:** /start",
        buttons=[
            [Button.inline("🔙 Отмена", data=f"back_stats_{username}")]
        ]
    )

@bot.on(events.NewMessage())
async def handle_keyword_input(event):
    """Обработка ввода ключевого слова"""
    if event.message.message.startswith('/'):
        return
    
    user_id = event.sender_id
    state = get_user_state(user_id)
    
    if not state.waiting_for_keyword:
        return
    
    keyword = event.message.text.strip()
    if not keyword or len(keyword) < 2:
        await event.reply("❌ Слишком короткий запрос! Минимум 2 символа.")
        return
    
    state.waiting_for_keyword = False
    state.searching = True
    state.current_keyword = keyword
    
    msg = await event.reply(f"🔍 **Ищу сообщения от @{state.current_username}...**\n\n"
                           f"📝 Ключевое слово: `{keyword}`\n"
                           f"⏳ Поиск может занять несколько минут...")
    
    try:
        # Получаем пользователя
        try:
            user_entity = await client.get_entity(state.current_username)
        except:
            await msg.edit("❌ Пользователь не найден!")
            state.searching = False
            return
        
        # Загружаем чаты
        chats = load_chats()
        found_messages = []
        
        # Ищем в чатах где есть пользователь
        user_chats = state.results if state.results else []
        
        if not user_chats:
            # Если нет сохраненных результатов, ищем во всех чатах
            for chat in load_chats()[:20]:  # Ограничиваем для скорости
                try:
                    chat_entity = await client.get_entity(chat)
                    user_chats.append({
                        'chat': chat,
                        'title': getattr(chat_entity, 'title', chat),
                        'entity': chat_entity,
                        'link': get_chat_link(chat)
                    })
                except:
                    continue
        
        # Ищем сообщения
        for i, chat_info in enumerate(user_chats[:20]):  # Ограничиваем для скорости
            try:
                # Обновляем статус
                if i % 5 == 0:
                    await msg.edit(f"🔍 Ищу в чатах...\n"
                                  f"Обработано: {i}/{len(user_chats[:20])}\n"
                                  f"Найдено: {len(found_messages)} сообщений\n"
                                  f"Ключевое слово: `{keyword}`")
                
                chat_entity = chat_info['entity']
                chat_name = chat_info['title']
                
                # Ищем сообщения
                try:
                    async for message in client.iter_messages(
                        chat_entity,
                        from_user=user_entity,
                        search=keyword,
                        limit=100
                    ):
                        if message.text and keyword.lower() in message.text.lower():
                            message_link = f"{chat_info['link']}/{message.id}"
                            
                            found_messages.append({
                                'chat': chat_info['chat'],
                                'title': chat_name,
                                'message_id': message.id,
                                'text': message.text[:200] + '...' if len(message.text) > 200 else message.text,
                                'link': message_link,
                                'date': message.date.strftime('%d.%m.%Y %H:%M')
                            })
                            
                except Exception as e:
                    logger.debug(f"Ошибка поиска в чате {chat_name}: {e}")
                    continue
                    
            except Exception as e:
                logger.debug(f"Ошибка обработки чата: {e}")
                continue
        
        state.searching = False
        state.found_messages = found_messages
        
        if found_messages:
            await show_found_messages_page(user_id, 1)
            await msg.delete()
        else:
            await msg.edit(
                f"❌ Сообщения от @{state.current_username} с текстом `{keyword}` не найдены!\n\n"
                f"Попробуйте:\n"
                f"1. Другое ключевое слово\n"
                f"2. Более общий запрос\n"
                f"3. Проверить доступность чатов"
            )
        
        # Сохраняем состояние
        save_state(user_id)
        
    except Exception as e:
        logger.error(f"Ошибка поиска сообщений: {e}")
        await msg.edit("❌ Произошла ошибка при поиске сообщений!")
        state.searching = False

async def show_found_messages_page(user_id, page):
    """Показать страницу с найденными сообщениями"""
    state = get_user_state(user_id)
    
    if not state.found_messages:
        return
    
    paginator = Paginator(state.found_messages, MESSAGES_PER_PAGE)
    page_data, total_pages = paginator.get_page(page)
    
    text = f"🔍 **Найдено сообщений от @{state.current_username}**\n\n"
    text += f"📝 **Ключевое слово:** `{state.current_keyword}`\n"
    text += f"📊 **Всего найдено:** {len(state.found_messages)} сообщений\n\n"
    
    for i, msg_data in enumerate(page_data):
        idx = (page - 1) * MESSAGES_PER_PAGE + i + 1
        text += f"**{idx}. {msg_data['title']}**\n"
        text += f"📅 {msg_data['date']}\n"
        text += f"💬 {msg_data['text']}\n"
        text += f"🔗 [Открыть сообщение]({msg_data['link']})\n\n"
    
    text += f"📄 Страница {page}/{total_pages}"
    
    # Кнопки
    buttons = []
    
    # Пагинация
    nav_row = []
    if page > 1:
        nav_row.append(Button.inline("⬅️ Назад", 
                     data=f"page_msgs_{state.current_username}_{state.current_keyword}_{page-1}"))
    
    nav_row.append(Button.inline(f"{page}/{total_pages}", data="noop"))
    
    if page < total_pages:
        nav_row.append(Button.inline("Вперед ➡️", 
                     data=f"page_msgs_{state.current_username}_{state.current_keyword}_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Дополнительные кнопки
    buttons.append([
        Button.inline("📊 Показать чаты", data=f"show_chats_{state.current_username}_1"),
        Button.inline("🔎 Новый поиск", data=f"search_msgs_{state.current_username}")
    ])
    
    buttons.append([Button.inline("🔙 Назад к статистике", 
                data=f"back_stats_{state.current_username}")])
    
    try:
        # Находим последнее сообщение бота
        async for message in bot.iter_messages(user_id, limit=5):
            if message.out:
                await message.edit(text, buttons=buttons, link_preview=False)
                return
    except:
        pass

@bot.on(events.CallbackQuery(pattern=r'page_msgs_(\w+)_(.+)_(\d+)'))
async def messages_page_handler(event):
    """Обработчик пагинации сообщений"""
    username = event.pattern_match.group(1)
    keyword = event.pattern_match.group(2)
    page = int(event.pattern_match.group(3))
    
    user_id = event.sender_id
    state = get_user_state(user_id)
    
    if state.current_username != username:
        state.current_username = username
    if state.current_keyword != keyword:
        state.current_keyword = keyword
    
    await show_found_messages_page(user_id, page)
    await event.answer()

@bot.on(events.CallbackQuery(pattern=r'back_stats_(\w+)'))
async def back_to_stats_handler(event):
    """Возврат к статистике"""
    username = event.pattern_match.group(1)
    user_id = event.sender_id
    state = get_user_state(user_id)
    
    if not state.results:
        await event.answer("❌ Нет данных для отображения!")
        return
    
    # Пересчитываем статистику
    total_messages = sum(r['message_count'] for r in state.results)
    
    text = (
        f"✅ **Результаты поиска для @{username}**\n\n"
        f"📊 **Статистика:**\n"
        f"• Чатов с пользователем: {len(state.results)}\n"
        f"• Всего сообщений: {total_messages}\n\n"
        f"👇 **Выберите действие:**"
    )
    
    buttons = [
        [Button.inline("📊 Показать чаты", data=f"show_chats_{username}_1")],
        [Button.inline("🔎 Найти сообщения", data=f"search_msgs_{username}")]
    ]
    
    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern='noop'))
async def noop_handler(event):
    """Обработчик пустой кнопки"""
    await event.answer()

@bot.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    """Проверка статуса бота"""
    user_id = event.sender_id
    state = get_user_state(user_id)
    
    chats = load_chats()
    status_text = (
        f"🤖 **Статус бота:**\n\n"
        f"✅ Бот работает\n"
        f"📊 Чатов в базе: {len(chats)}\n"
        f"👤 Ваш ID: {user_id}\n"
        f"🔍 Поиск активен: {'Да' if state.searching else 'Нет'}\n"
        f"📝 Ждет ключ: {'Да' if state.waiting_for_keyword else 'Нет'}\n\n"
        f"🔄 Используйте /start для начала"
    )
    
    await event.reply(status_text)

@bot.on(events.NewMessage(pattern='/chats'))
async def list_chats_handler(event):
    """Показать список чатов"""
    chats = load_chats()
    
    if not chats:
        await event.reply("❌ Список чатов пустой!")
        return
    
    text = f"📋 **Список чатов для поиска:**\n\n"
    
    for i, chat in enumerate(chats[:50], 1):  # Показываем первые 50
        text += f"{i}. {chat}\n"
    
    if len(chats) > 50:
        text += f"\n... и еще {len(chats) - 50} чатов"
    
    text += f"\n\nВсего чатов: {len(chats)}"
    
    await event.reply(text)

# ==================== ОСНОВНАЯ ФУНКЦИЯ ====================

async def main():
    """Основная функция запуска"""
    logger.info("🚀 Запуск Telegram-бота...")
    
    try:
        # Запускаем клиент
        await client.start()
        logger.info(f"✅ Клиент Telethon запущен ({SESSION_NAME})")
        
        # Проверяем подключение
        me = await client.get_me()
        logger.info(f"👤 Авторизован как: {me.first_name} (@{me.username})")
        
        # Проверяем файл с чатами
        chats = load_chats()
        logger.info(f"📊 Загружено {len(chats)} чатов для поиска")
        
        # Запускаем бота
        await bot.start()
        bot_me = await bot.get_me()
        logger.info(f"🤖 Бот запущен: @{bot_me.username}")
        
        # Приветственное сообщение
        logger.info("✅ Бот готов к работе!")
        logger.info("📝 Отправьте /start в боте для начала")
        
        # Бесконечный цикл
        await bot.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await client.disconnect()
        await bot.disconnect()

# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    # Проверяем настройки
    if API_ID == 1234567 or API_HASH == 'ваш_api_hash_здесь' or BOT_TOKEN == 'ваш_bot_token_здесь':
        print("⚠️ ВНИМАНИЕ: Настройки не заданы!")
        print("=" * 50)
        print("📋 Инструкция по настройке:")
        print("1. Получите API_ID и API_HASH на my.telegram.org")
        print("2. Создайте бота через @BotFather и получите токен")
        print("3. Вставьте полученные данные в начало файла:")
        print("   - API_ID = ваши_цифры")
        print("   - API_HASH = 'ваша_строка'")
        print("   - BOT_TOKEN = 'ваш_токен'")
        print("4. Сохраните файл и запустите снова")
        print("=" * 50)
        exit(1)
    
    print("=" * 50)
    print("🤖 Telegram Bot-Fazer")
    print("🚀 Быстрый поиск пользователей и сообщений")
    print("=" * 50)
    print(f"📊 API ID: {API_ID}")
    print(f"🔑 API Hash: {'*' * len(API_HASH)}")
    print(f"🤖 Bot Token: {'*' * len(BOT_TOKEN)}")
    print(f"👤 Session: {SESSION_NAME}")
    print("=" * 50)
    print("🔄 Запуск бота...")
    
    # Запуск
    asyncio.run(main())