import asyncio
import logging
import requests
import urllib3
from aiogram import Bot, Dispatcher, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand
import kpi_api
import re
import db  # Наш модуль бази даних

# BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
BOT_TOKEN = "8884330606:AAGXxsJQBXElcplIjf4jcu6dYrQqkaRJVfI"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    user_name = html.quote(message.from_user.full_name)
    db.init_db()
    await message.answer(
        f"Привіт, <b>{user_name}</b>!\n\n"
        "Я бот для відстеження розкладу КПІ.\n\n"
        "1 Вкажи групу: /setgroup 3970\n"
        "2 Подивись розклад: /today\n"
        "3 Додай Zoom: /addzoom Назва_Предмета Посилання\n",
        parse_mode="HTML"
    )

# Команда /setgroup
@dp.message(Command("setgroup"))
async def set_group_handler(message: Message):
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        group_id = int(args[1])
        db.set_user_group(message.from_user.id, group_id)
        await message.answer(f"Групу {group_id} успішно збережено!")
    else:
        await message.answer("Вкажи ID групи цифрою. Приклад:\n`/setgroup 3970`", parse_mode="Markdown")

# Команда /addzoom
@dp.message(Command("addzoom"))
async def add_zoom_handler(message: Message):
    user_group = db.get_user_group(message.from_user.id)
    if not user_group:
        await message.answer(" Спочатку вкажи свою групу через команду /setgroup!")
        return

    try:
        _, subject, link = message.text.split(maxsplit=2)
        db.add_zoom_link(user_group, subject, link)
        await message.answer(f"Посилання для предмета '{subject}' збережено!")
    except ValueError:
        await message.answer("Формат теми:\n`/addzoom Назва_Предмета Посилання`", parse_mode="Markdown")

# Команда /today
@dp.message(Command("today"))
async def today_schedule_handler(message: Message):
    user_group = db.get_user_group(message.from_user.id)
    if not user_group:
        await message.answer(" Спочатку вкажіть групу через команду /setgroup", parse_mode="HTML")
        return

    await message.answer(" Завантажую розклад з сервера КПІ...")

    data = kpi_api.get_schedule(user_group)

    if not data:
        await message.answer(" Не вдалося отримати розклад з сервера КПІ.")
        return

    first_week = data.get('scheduleFirstWeek', [])
    if not first_week:
        await message.answer("Розклад для цієї групи відсутній.")
        return

    text = f" <b>РОЗКЛАД ДЛЯ ГРУПИ {user_group}</b>\n\n"

    for day in first_week:
        day_name = day.get('day', 'День')
        pairs = day.get('pairs', [])

        if pairs:
            text += f" <b>{day_name}:</b>\n"
            for lesson in pairs:
                subject = lesson.get('name', 'Без назви')
                raw_time = lesson.get('time', 'Час не вказано')
                time = re.sub(r'(\d{2}:\d{2}):00', r'\1', raw_time)
                
                lesson_type = lesson.get('type', '')
                
                # Інформація про викладача з твого скрипту
                lecturer_info = lesson.get('lecturer')
                teacher = lecturer_info.get('name') if isinstance(lecturer_info, dict) else None
                teacher_txt = f"\n       <i>{html.quote(teacher)}</i>" if teacher else ""

                # Посилання на Zoom з нашої бази
                zoom = db.get_zoom_link(user_group, subject)
                zoom_txt = f"\n     <a href='{zoom}'>Zoom / Meet</a>" if zoom != "Посилання відсутнє" else ""

                text += f"    {time} — <b>{html.quote(subject)}</b> ({lesson_type}){teacher_txt}{zoom_txt}\n"
            text += "\n"

    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

  
            

# Налаштування меню команд в Telegram
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Перезапустити бота"),
        BotCommand(command="setgroup", description="Встановити ID групи"),
        BotCommand(command="today", description="Показати розклад"),
        BotCommand(command="addzoom", description="Додати Zoom-посилання"),
    ]
    await bot.set_my_commands(commands)

async def main():
    db.init_db()
    await set_bot_commands(bot)
    print(" Бот успішно запущений і готовий до роботи!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())