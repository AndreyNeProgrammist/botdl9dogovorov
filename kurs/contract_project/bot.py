import asyncio
import nest_asyncio
import aiofiles
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from docx import Document
import os
import django

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contract_project.settings')
django.setup()

from contracts.models import Contract

API_TOKEN = "8034797078:AAHIffWSFROoUNr8yznBua-CMW8WIYdEyfg"

# Состояния для обработки диалога
FIO, SERIA_NUMBER, DATE, SIGNED_CONTRACT = range(4)

# Функция для создания клавиатуры с кнопкой "Старт"
def get_start_keyboard():
    keyboard = [
        [KeyboardButton("Старт")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: CallbackContext):
    print("Запущен обработчик /start")  # Для отладки
    await update.message.reply_text(
        "Доброго времени суток! Я твой бот. Давайте начнем процесс оформления договора. Введите свое ФИО",
        reply_markup=get_start_keyboard()  # Кнопка "Старт"
    )
    return FIO


# Получение ФИО
async def get_fio(update: Update, context: CallbackContext):
    context.user_data['fio'] = update.message.text
    await update.message.reply_text("Введите серию и номер паспорта")
    return SERIA_NUMBER

# Получение серии и номера паспорта
async def get_seria_number(update: Update, context: CallbackContext):
    context.user_data['seria_number'] = update.message.text
    await update.message.reply_text("Введите дату заключения договора (формат: дд.мм.гггг).")
    return DATE

# Получение даты
async def get_date(update: Update, context: CallbackContext):
    context.user_data['date'] = update.message.text
    
    # Путь к шаблону документа
    template_path = "C:/Users/andre/Desktop/kurs/docs/шаблон.docx"
    doc = Document(template_path)

    # Замена данных в документе
    for para in doc.paragraphs:
        if '%ФИО%' in para.text:
            para.text = para.text.replace('%ФИО%', context.user_data['fio'])
        if '%серияномер%' in para.text:
            para.text = para.text.replace('%серияномер%', context.user_data['seria_number'])
        if '%дата%' in para.text:
            para.text = para.text.replace('%дата%', context.user_data['date'])

    # Путь к директории для сохранения
    output_dir = "../docs/wablon/"

    # Проверка, существует ли директория, и создание её при необходимости
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Путь к файлу для сохранения
    output_path = os.path.join(output_dir, f"{context.user_data['fio']}_contract.docx")
    doc.save(output_path)

    # Отправка готового документа
    await update.message.reply_document(document=open(output_path, 'rb'), caption="Вот ваш готовый договор. Пожалуйста, подпишите его.")
    await update.message.reply_text("Когда вы подпишете договор, загрузите его обратно сюда.", reply_markup=get_start_keyboard())

    return SIGNED_CONTRACT

# Получение подписанного договора
async def get_signed_contract(update: Update, context: CallbackContext):
    signed_contract = update.message.document
    signed_contract_path = f"../docs/rospis/{signed_contract.file_name}"

    # Get the file object
    signed_contract_file = await context.bot.get_file(signed_contract.file_id)

    # Download the file
    file_content = await signed_contract_file.download_as_bytearray()
    
    # Save the file
    async with aiofiles.open(signed_contract_path, 'wb') as out:
        await out.write(file_content)

    # Send confirmation to the user
    await update.message.reply_text("Подписанный договор успешно загружен. Спасибо!", reply_markup=get_start_keyboard())
    return ConversationHandler.END

# Обработка команды "cancel"
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Процесс был отменен.", reply_markup=get_start_keyboard())
    return ConversationHandler.END

# Основная функция для настройки бота
async def main():
    print("Ura rabotaet...")  # Вывод в консоль о старте бота
    application = Application.builder().token(API_TOKEN).build()

    # Создание обработчиков
    conversation_handler = ConversationHandler(
        entry_points=[
    CommandHandler('start', start),
    MessageHandler(filters.Regex('^Старт$'), start)],  
    # Добавляем обработку кнопки "Старт"
        states={
            FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)],
            SERIA_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seria_number)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            SIGNED_CONTRACT: [MessageHandler(filters.Document.ALL, get_signed_contract)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчики в приложение
    application.add_handler(conversation_handler)

    # Запускаем бота
    await application.run_polling()

if __name__ == "__main__":
    # Для среды с уже запущенным циклом событий используем так:
    nest_asyncio.apply()

    # Теперь запускаем бота
    asyncio.run(main())
