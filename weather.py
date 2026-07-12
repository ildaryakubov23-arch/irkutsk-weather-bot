"""
Модуль для получения текущей погоды и прогноза в Иркутске
через бесплатный сервис Open-Meteo (https://open-meteo.com) —
API-ключ не требуется.
"""

from datetime import date

import requests

# Координаты Иркутска, Россия
LATITUDE = 52.2978
LONGITUDE = 104.2964
TIMEZONE = "Asia/Irkutsk"

API_URL = "https://api.open-meteo.com/v1/forecast"

# Расшифровка WMO weather code -> текст на русском + эмодзи
WEATHER_CODES = {
    0: ("Ясно", "☀️"),
    1: ("Преимущественно ясно", "🌤️"),
    2: ("Переменная облачность", "⛅"),
    3: ("Пасмурно", "☁️"),
    45: ("Туман", "🌫️"),
    48: ("Изморозь", "🌫️"),
    51: ("Лёгкая морось", "🌦️"),
    53: ("Морось", "🌦️"),
    55: ("Сильная морось", "🌧️"),
    56: ("Ледяная морось", "🌧️"),
    57: ("Сильная ледяная морось", "🌧️"),
    61: ("Небольшой дождь", "🌦️"),
    63: ("Дождь", "🌧️"),
    65: ("Сильный дождь", "🌧️"),
    66: ("Ледяной дождь", "🌧️"),
    67: ("Сильный ледяной дождь", "🌧️"),
    71: ("Небольшой снег", "🌨️"),
    73: ("Снег", "❄️"),
    75: ("Сильный снег", "❄️"),
    77: ("Снежные зёрна", "❄️"),
    80: ("Небольшие ливни", "🌦️"),
    81: ("Ливни", "🌧️"),
    82: ("Сильные ливни", "⛈️"),
    85: ("Небольшой снегопад", "🌨️"),
    86: ("Сильный снегопад", "❄️"),
    95: ("Гроза", "⛈️"),
    96: ("Гроза с небольшим градом", "⛈️"),
    99: ("Гроза с сильным градом", "⛈️"),
}

# Короткие названия дней недели (индекс 0 = понедельник, как в date.weekday())
WEEKDAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


class WeatherFetchError(Exception):
    """Не удалось получить данные о погоде."""


def _describe_code(code: int) -> tuple[str, str]:
    return WEATHER_CODES.get(code, ("Неизвестно", "❓"))


def _weekday_label(iso_date: str, index: int) -> str:
    """Возвращает 'Сегодня' для первого дня, иначе короткое название дня недели."""
    if index == 0:
        return "Сегодня"
    year, month, day = (int(part) for part in iso_date.split("-"))
    weekday_index = date(year, month, day).weekday()
    return WEEKDAY_NAMES[weekday_index]


def fetch_weather() -> dict:
    """
    Возвращает словарь с текущей погодой и прогнозом на неделю для Иркутска.
    """
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
        "wind_speed_10m,weather_code,precipitation",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
        "precipitation_sum,precipitation_probability_max",
        "forecast_days": 7,
    }

    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise WeatherFetchError(f"Ошибка сети при обращении к Open-Meteo: {exc}") from exc
    except ValueError as exc:
        raise WeatherFetchError(f"Не удалось разобрать ответ Open-Meteo: {exc}") from exc

    if "current" not in data or "daily" not in data:
        raise WeatherFetchError("Open-Meteo вернул неожиданный ответ (нет current/daily).")

    return data


def format_weather_message(data: dict) -> str:
    """Форматирует данные о погоде в читаемое сообщение для Telegram."""
    current = data["current"]
    daily = data["daily"]

    code = current.get("weather_code")
    description, emoji = _describe_code(code)

    today_precip_prob = None
    if daily.get("precipitation_probability_max"):
        today_precip_prob = daily["precipitation_probability_max"][0]

    lines = [
        f"{emoji} *Погода в Иркутске сейчас*",
        f"Температура: {current['temperature_2m']}°C "
        f"(ощущается как {current['apparent_temperature']}°C)",
        f"Состояние: {description}",
        "",
        f"💧 Осадки: {today_precip_prob if today_precip_prob is not None else '—'}%",
        f"💨 Ветер: {current['wind_speed_10m']} км/ч",
        f"🌫 Влажность: {current['relative_humidity_2m']}%",
        "",
        "*Прогноз по дням:*",
    ]

    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])

    for i in range(len(dates)):
        day_description, day_emoji = _describe_code(codes[i])
        day_label = _weekday_label(dates[i], i)
        lines.append(
            f"{day_emoji} {day_label}: {round(temp_max[i])}°/{round(temp_min[i])}° "
            f"— {day_description}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    # Локальный тест: python weather.py
    weather_data = fetch_weather()
    print(format_weather_message(weather_data))
