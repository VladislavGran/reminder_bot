import asyncio
from datetime import datetime, timedelta
from db import delete_reminder

async def schedule_reminder(bot, reminder_id, user_id, text, time_str):
    now = datetime.now()
    reminder_time = datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    if reminder_time < now:
        reminder_time += timedelta(days=1)

    wait_seconds = (reminder_time - now).total_seconds()
    await asyncio.sleep(wait_seconds)

    try:
        await bot.send_message(user_id, f"⏰ Напоминание: {text}")
        delete_reminder(reminder_id)
    except Exception as e:
        print(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")
