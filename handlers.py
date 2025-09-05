import asyncio
import re
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import add_reminder, get_reminders, delete_reminder
from scheduler import schedule_reminder

router = Router()
user_states = {}

# --- Главное меню ---
def main_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить", callback_data="add"),
                InlineKeyboardButton(text="📋 Список", callback_data="list"),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить все", callback_data="delete_all")
            ]
        ]
    )
    return kb

# --- Проверка формата времени HH:MM ---
def valid_time_format(time_str):
    return bool(re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", time_str))

# --- /start ---
@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! Я бот-напоминатель.\nВыбери действие:",
        reply_markup=main_menu()
    )

# --- Обработка нажатий кнопок главного меню ---
@router.callback_query(lambda c: c.data in ["add", "list", "delete_all"])
async def callback_handler(query: types.CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if data == "add":
        user_states[user_id] = {"action": "add"}
        await query.message.answer("Напиши текст напоминания:")

    elif data == "list":
        await send_reminders_list(query.message, user_id)

    elif data == "delete_all":
        reminders = get_reminders(user_id)
        if not reminders:
            await query.message.answer("Нет напоминаний для удаления.", reply_markup=main_menu())
        else:
            for r in reminders:
                delete_reminder(r[0])
            await query.message.answer("✅ Все напоминания удалены.", reply_markup=main_menu())

    await query.answer()

# --- Функция вывода списка напоминаний с кнопками удаления ---
async def send_reminders_list(message: types.Message, user_id: int):
    reminders = get_reminders(user_id)
    if not reminders:
        await message.answer("У вас нет активных напоминаний.", reply_markup=main_menu())
        return

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{r[1]} в {r[2]} (Нажмите для удаления)",
                callback_data=f"delete:{r[0]}"
            )
        ]
        for r in reminders
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Ваши напоминания:", reply_markup=kb)

# --- Обработка текстовых сообщений при добавлении напоминания ---
@router.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    if state.get("action") == "add":
        if "text" not in state:
            state["text"] = message.text
            await message.answer("Укажи время напоминания в формате HH:MM")
        elif "time" not in state:
            if not valid_time_format(message.text):
                await message.answer("❌ Неверный формат времени. Попробуйте HH:MM")
                return
            state["time"] = message.text
            reminder_id = add_reminder(user_id, state["text"], state["time"])
            await message.answer(
                f"✅ Напоминание добавлено: {state['text']} в {state['time']}",
                reply_markup=main_menu()
            )
            asyncio.create_task(schedule_reminder(
                message.bot, reminder_id, user_id, state["text"], state["time"]
            ))
            user_states.pop(user_id)

# --- Удаление отдельного напоминания через кнопку ---
@router.callback_query(lambda c: c.data and c.data.startswith("delete:"))
async def delete_callback(query: types.CallbackQuery):
    reminder_id = int(query.data.split(":")[1])
    delete_reminder(reminder_id)  # удаляем из базы

    # Обновляем список оставшихся напоминаний
    await send_reminders_list(query.message, query.from_user.id)
    await query.answer("✅ Напоминание удалено")
