#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram бот - финальная рабочая версия с кнопками
"""

import os
import re
from io import BytesIO
from docx import Document
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Токен из переменной окружения
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Добавь переменную окружения.")

# Глобальное хранилище для вопросов (временное)
user_data = {}


def parse_questions(text):
    """Парсит вопросы из текста"""
    questions = []
    lines = text.strip().split('\n')

    current_question = None
    variants = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_question and variants:
                questions.append({'question': current_question, 'variants': variants.copy()})
                current_question = None
                variants = []
            continue

        if '<question>' in line:
            if current_question and variants:
                questions.append({'question': current_question, 'variants': variants.copy()})
                variants = []
            current_question = re.sub(r'</?question>', '', line).strip()

        elif '<variant>' in line:
            variant = re.sub(r'</?variant>', '', line).strip()
            if variant:
                variants.append(variant)

    if current_question and variants:
        questions.append({'question': current_question, 'variants': variants.copy()})

    return questions


def format_output(questions, correct_num):
    """Форматирует результат"""
    result = []
    correct_idx = correct_num - 1

    for q in questions:
        result.append(f"?{q['question']}")
        for i, v in enumerate(q['variants']):
            result.append(f"+{v}" if i == correct_idx else f"-{v}")
        result.append("")

    return '\n'.join(result)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    text = (
        "👋 Привет! Я бот для конвертации вопросов.\n\n"
        "📄 Отправь мне .docx файл с вопросами\n\n"
        "📝 Я спрошу какой вариант правильный во ВСЕХ вопросах!"
    )

    # Простые кнопки
    keyboard = [
        [InlineKeyboardButton("📖 Инструкция", callback_data="help")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка документа"""
    document = update.message.document
    user_id = update.effective_user.id

    if not document.file_name.endswith('.docx'):
        await update.message.reply_text("❌ Отправь файл в формате .docx")
        return

    try:
        msg = await update.message.reply_text("⏳ Обрабатываю...")

        # Скачиваем
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()

        # Читаем
        doc = Document(BytesIO(file_bytes))
        text = '\n'.join([p.text.strip() for p in doc.paragraphs if p.text.strip()])

        # Парсим
        questions = parse_questions(text)

        if not questions:
            await msg.edit_text("❌ Не нашел вопросы. Проверь формат.")
            return

        # Сохраняем
        max_vars = max(len(q['variants']) for q in questions)
        user_data[user_id] = {
            'questions': questions,
            'filename': document.file_name,
            'max_variants': max_vars
        }

        await msg.delete()

        # Показываем инфо + кнопки
        info_text = (
            f"✅ Документ обработан!\n\n"
            f"📊 Найдено вопросов: {len(questions)}\n"
            f"📝 Вариантов ответа: {max_vars}\n\n"
            f"❓ Какой вариант правильный во ВСЕХ вопросах?"
        )

        # Создаем кнопки с номерами
        buttons = []
        row = []
        for i in range(1, max_vars + 1):
            row.append(InlineKeyboardButton(str(i), callback_data=f"v{i}"))
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        buttons.append([InlineKeyboardButton("📋 Показать вопросы", callback_data="show")])
        buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])

        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(info_text, reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    # Помощь
    if data == "help":
        text = (
            "📖 Инструкция:\n\n"
            "1️⃣ Отправь .docx файл\n"
            "2️⃣ Нажми кнопку с номером правильного варианта\n"
            "3️⃣ Получи готовый файл\n\n"
            "Формат документа:\n"
            "<question>Вопрос?\n"
            "<variant>Вариант 1\n"
            "<variant>Вариант 2"
        )
        await query.edit_message_text(text)
        return

    # О боте
    if data == "about":
        text = (
            "🤖 Бот для конвертации тестов\n\n"
            "Версия: 3.0\n"
            "Функции:\n"
            "✅ Конвертация .docx → .txt\n"
            "✅ Интерактивные кнопки\n"
            "✅ Просмотр вопросов"
        )
        await query.edit_message_text(text)
        return

    # Отмена
    if data == "cancel":
        if user_id in user_data:
            del user_data[user_id]
        await query.edit_message_text("❌ Отменено. Отправь новый файл или /start")
        return

    if user_id not in user_data:
        await query.edit_message_text("❌ Сначала отправь .docx файл")
        return

    questions = user_data[user_id]['questions']

    # Показать вопросы
    if data == "show":
        text = f"📚 Всего вопросов: {len(questions)}\n\n"

        for i, q in enumerate(questions[:10], 1):
            text += f"{i}. {q['question'][:50]}...\n"
            for j, v in enumerate(q['variants'], 1):
                text += f"   {j}) {v[:30]}...\n"
            text += "\n"

        if len(questions) > 10:
            text += f"... и ещё {len(questions) - 10}\n"

        keyboard = [[InlineKeyboardButton("« Назад", callback_data="back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Назад
    if data == "back":
        max_vars = user_data[user_id]['max_variants']
        text = f"✅ Документ обработан!\n\n📊 Вопросов: {len(questions)}\n\n❓ Какой вариант правильный?"

        buttons = []
        row = []
        for i in range(1, max_vars + 1):
            row.append(InlineKeyboardButton(str(i), callback_data=f"v{i}"))
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        buttons.append([InlineKeyboardButton("📋 Показать вопросы", callback_data="show")])
        buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    # Выбор варианта (v1, v2, v3...)
    if data.startswith("v"):
        variant_num = int(data[1:])

        # Проверка
        for i, q in enumerate(questions, 1):
            if variant_num > len(q['variants']):
                await query.edit_message_text(f"❌ В вопросе {i} нет варианта {variant_num}!")
                return

        # Конвертируем
        await query.edit_message_text("⏳ Конвертирую...")

        result = format_output(questions, variant_num)

        # Создаем файл
        filename = user_data[user_id]['filename'].replace('.docx', '_converted.txt')
        file = BytesIO(result.encode('utf-8'))
        file.name = filename

        # Отправляем
        await query.message.reply_document(
            document=file,
            filename=filename,
            caption=f"✅ Готово!\n📊 Вопросов: {len(questions)}\n✅ Правильный вариант: {variant_num}"
        )

        # Очищаем
        del user_data[user_id]

        await query.message.reply_text("✅ Конвертация завершена! Можешь отправить новый файл.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    text = (
        "📖 Инструкция:\n\n"
        "1️⃣ Отправь .docx файл\n"
        "2️⃣ Нажми кнопку с номером\n"
        "3️⃣ Получи готовый .txt файл\n\n"
        "Команды:\n"
        "/start - начать\n"
        "/help - помощь"
    )
    await update.message.reply_text(text)


def main():
    """Запуск"""
    print("🤖 Запуск бота...")

    app = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.Document.FileExtension("docx"), handle_document))
    app.add_handler(CallbackQueryHandler(button_click))

    print("✅ Бот запущен!")
    print("📱 Отправь /start боту")

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
