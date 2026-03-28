import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

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
    user = query.from_user.first_name
    actions = {
        "create_forms": "Функция «Создание форм» активирована.",
        "ip_analytics": "Аналитика IP запущена.",
        "logs": "Вы просматриваете логи.",
        "settings": "Вы вошли в настройки."
    }
    response_text = actions.get(action, "Неизвестное действие.")
    await query.edit_message_text(response_text)
    logger.info(f"Пользователь {user} нажал кнопку: {action}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Неизвестная команда. Введите /help для списка команд.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("panel", panel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.add_error_handler(error_handler)
    logger.info("Бот успешно запущен и начал опрос обновлений...")
    application.run_polling()

if __name__ == '__main__':
    main()