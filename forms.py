import os
import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Установка библиотеки aiohttp (если не установлена): pip install aiohttp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8211088663:AAHAisWnPKFMBF9JzJA9ArOsHIe3QZVpqhU')

ROLES_LIST = [
    "Технический специалист [Форумный]",
    "Технический специалист [Логирования]",
    "Зам. Куратора тех. специалистов",
    "Куратор тех. специалистов"
]

def get_user_role(user_id: int) -> str:
    return "Куратор тех. специалистов"

# Функция для получения информации по IP через API
async def get_ip_info(ip: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://ipapi.co/{ip}/json/') as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"error": "Не удалось получить информацию по IP"}

# Обработка ввода для создания форм одним списком
async def collect_form_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    step = context.user_data.get('step')

    if step == 'command':
        # Сохраняем команду и переходим к запросу причины
        context.user_data['command'] = text
        await update.message.reply_text("Введите причину блокировки, к примеру «2.28 Покупка ИВ».")
        context.user_data['step'] = 'reason'

    elif step == 'reason':
        # Сохраняем причину и переходим к запросу списка ников
        context.user_data['reason'] = text
        await update.message.reply_text("Введите список ников (через пробел или запятую).")
        context.user_data['step'] = 'nicks'

    elif step == 'nicks':
        # Сохраняем список ников и формируем итоговую форму
        context.user_data['nicks'] = text.split()  # разбиваем строку на список

        # Формируем список команд
        commands_list = []
        for nick in context.user_data['nicks']:
            cmd = f"{context.user_data['command']} {nick} {context.user_data['reason']}"
            commands_list.append(cmd)

        # Отправляем результат
        result_text = "Список форм сформирован:\n"
        for i, cmd in enumerate(commands_list, 1):
            result_text += f"{i}. {cmd}\n"

        result_text += "\nВы можете отправить список ников для продолжения создания форм, вернуться к настройке форм или же возвратиться в меню."

        await update.message.reply_text(result_text)

        # Очищаем user_data и удаляем хендлер
        context.user_data.clear()
        context.application.remove_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_form_data))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_first_name = update.effective_user.first_name
    user_id = update.effective_user.id
    user_role = get_user_role(user_id)

    message_text = (
        f"👋🏻 Привет, {user_first_name}!\n\n"
        "Для получения более подробной информации введи /help.\n"
        "Для открытия панели — /panel\n\n"
        "Реферальная программа теперь в настройках (/panel > Настройки)\n\n"
        f"Твоя роль: {user_role}"
    )
    await update.message.reply_text(message_text)
    logger.info(f"Пользователь {user_first_name} (ID: {user_id}) вызвал команду /start")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start — приветствие\n"
        "/panel — открыть панель управления\n"
        "/help — это сообщение"
    )
    logger.info(f"Пользователь {update.effective_user.first_name} вызвал команду /help")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    keyboard = [
        [InlineKeyboardButton("Создание форм", callback_data="create_forms"),
         InlineKeyboardButton("Аналитика IP", callback_data="ip_analytics")],
        [InlineKeyboardButton("Логи", callback_data="logs")],
        [InlineKeyboardButton("Настройки", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"{user_name}, выберите нужный пункт ниже", reply_markup=reply_markup)
    logger.info(f"Пользователь {user_name} открыл панель (/panel)")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "create_forms":
        keyboard = [
            [InlineKeyboardButton("Одним списком", callback_data="form_single_list")],
            [InlineKeyboardButton("Отдельными сообщениями", callback_data="form_separate_msgs")],
            [InlineKeyboardButton("Моно-формы", callback_data="form_mono")],
            [InlineKeyboardButton("Вернуться в панель", callback_data="back_to_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите способ создания форм:", reply_markup=reply_markup)

    elif action == "form_single_list":
        await query.edit_message_text("Введите команду, к примеру `/permban`.")
        context.user_data['step'] = 'command'
        context.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_form_data))

    elif action == "ip_analytics":
        await query.edit_message_text("Пожалуйста, введите IP-адрес для анализа (например, 8.8.8.8)")
        context.application.add_handler(MessageHandler(filters.RegexPattern(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), ip_analysis))

    else:
        actions = {
            "logs": "Вы просматриваете логи.",
            "settings": "Вы вошли в настройки.",
            "form_separate_msgs": "Функция «Отдельными сообщениями» активирована.",
            "form_mono": "Функция «Моно-формы» активирована.",
            "back_to_panel": "Возвращаемся в панель управления..."
        }
        response_text = actions.get(action, "Неизвестное действие.")
        await query.edit_message_text(response_text)

async def ip_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ip = update.message.text
    ip_info = await get_ip_info(ip)
    if "error" in ip_info:
        await update.message.reply_text(f"Ошибка: {ip_info['error']}")
    else:
        response_text = (
            f"Информация по IP-адресу {ip}:\n"
            f"Страна: {ip_info.get('country_name', 'Неизвестно')}\n"
            f"Регион: {ip_info.get('region', 'Неизвестно')}\n"
            f"Город: {ip_info.get('city', 'Неизвестно')}\n"
            f"Широта: {ip_info.get('latitude', 'Неизвестно')}\n"
            f"Долгота: {ip_info.get('
