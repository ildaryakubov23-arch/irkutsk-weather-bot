"""
Телеграм-бот, показывающий текущую погоду и прогноз в Иркутске
через Open-Meteo (без API-ключа).

Команды:
  /start   — приветствие
  /weather — показать текущую погоду и прогноз на неделю
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv

from weather import fetch_weather, format_weather_message, WeatherFetchError

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет! Я показываю погоду в Иркутске 🌤️\n\n"
        "Команда /weather — покажу текущую погоду и прогноз на неделю."
    )


@dp.message(Command("weather"))
async def handle_weather(message: Message) -> None:
    status_message = await message.answer("Смотрю погоду в Иркутске…")
    try:
        data = await asyncio.to_thread(fetch_weather)
        text = format_weather_message(data)
        await status_message.edit_text(text, parse_mode="Markdown")
    except WeatherFetchError as exc:
        await status_message.edit_text(f"⚠️ Не получилось получить погоду: {exc}")
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error while fetching weather")
        await status_message.edit_text(
            "⚠️ Что-то пошло не так при получении погоды. Попробуйте позже."
        )


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Добавьте его в переменные окружения хостинга."
        )

    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
