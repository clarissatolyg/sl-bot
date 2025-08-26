import os
import requests
from dotenv import load_dotenv
from typing import List
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram import ReplyKeyboardMarkup, KeyboardButton
from resrobot import StopLocation
from trafiklab import Departure
from collections import defaultdict
from datetime import datetime
import pytz
from telegram.helpers import escape_markdown

stockholm_tz = pytz.timezone("Europe/Stockholm")


load_dotenv()
RESROBOT_API_KEY = os.getenv("RESROBOT_API")
TRAFIKLAB_REALTIME_API_KEY = os.getenv("TRAFIKLAB_REALTIME_API")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def format_departure_time(dep: Departure) -> str:
    """Format departure time as 'Arr*' or 'Xm*'."""
    raw_time = getattr(dep, "realtime", None) or getattr(dep, "planned", None)
    if raw_time is None:
        return "??"

    if isinstance(raw_time, str):
        dep_time = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    else:
        dep_time = raw_time

    if dep_time.tzinfo is None:
        dep_time = stockholm_tz.localize(dep_time)

    now = datetime.now(stockholm_tz)
    diff = int((dep_time - now).total_seconds() / 60)

    if diff <= 0:
        return "Arr\\*"  # escape * for MarkdownV2
    return f"{diff}m\\*"


def get_nearby_stops(lat: str, lon: str) -> List[StopLocation]:
    response = requests.get(
        f"https://api.resrobot.se/v2.1/location.nearbystops?originCoordLat={lat}&originCoordLong={lon}&format=json"
        f"&accessId={RESROBOT_API_KEY}"
    )
    data = response.json()
    stop_locations = [
        StopLocation(**item["StopLocation"])
        for item in data["stopLocationOrCoordLocation"]
    ]
    return stop_locations


def get_departures(area_id: str) -> List[Departure]:
    response = requests.get(
        f"https://realtime-api.trafiklab.se/v1/departures/{area_id}?key={TRAFIKLAB_REALTIME_API_KEY}"
    )
    data = response.json()
    departures = [Departure(**d) for d in data["departures"]]
    return departures


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    location_button = KeyboardButton(text="📍 Send Location", request_location=True)
    reply_markup = ReplyKeyboardMarkup(
        [[location_button]], resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "Please share your location:", reply_markup=reply_markup
    )
    # await update.message.reply_text(
    #     "Hi! Send me your location and I’ll show you the nearest bus departures 🚍"
    # )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lat = update.message.location.latitude
    lon = update.message.location.longitude

    nearby_stops = get_nearby_stops(lat, lon)

    if not nearby_stops:
        await update.message.reply_text("No bus stops found nearby.")
        return

    response_text = "🚌 Upcoming departures:\n\n"

    for stop in nearby_stops[:3]:
        departures = get_departures(stop.extId)
        if not departures:
            continue

        grouped = defaultdict(list)
        for dep in departures:
            key = (dep.route.designation, dep.route.direction)
            grouped[key].append(dep)

        sorted_groups = sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1]))

        # Escape stop name
        response_text += f"📍 *{escape_markdown(stop.name, version=2)}*\n"

        for (line, direction), deps in sorted_groups:
            deps.sort(key=lambda d: d.realtime)
            times = [format_departure_time(d) for d in deps[:3]]

            # Escape line and direction
            safe_line = escape_markdown(line, version=2)
            safe_times = " \\| ".join(times)  # escape | for MarkdownV2

            response_text += f"🚍{safe_line:<4}: {safe_times}\n"

        response_text += "\n"

    await update.message.reply_markdown_v2(response_text)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))

    app.run_polling()


if __name__ == "__main__":
    main()
