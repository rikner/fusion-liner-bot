import os
import requests
import datetime
import json

from telegram import Update
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


def check_buses():
    event_id = 195  # fusion festival
    meeting_point_id = 1  # ostbahnhof
    tour_type_id = 1  # outward

    tours = get_tours(event_id, meeting_point_id, tour_type_id)

    earliest_available_tour_departure_time = None
    for tour in tours:
        tour_departure_time = datetime.datetime.fromisoformat(tour["time"])
        price_groups = tour["departures"][0]["price_groups"]

        if len(price_groups) == 0:
            continue
        else:
            if earliest_available_tour_departure_time is None:
                earliest_available_tour_departure_time = tour_departure_time
            elif tour_departure_time < earliest_available_tour_departure_time:
                earliest_available_tour_departure_time = tour_departure_time

    if earliest_available_tour_departure_time is None:
        return "No buses available"
    else:
        return (
            "Buses available! Earliest departure time: "
            + earliest_available_tour_departure_time.strftime("%Y-%m-%d %H:%M:%S")
        )


def get_tours(event_id, meeting_point_id, tour_type_id):
    request_payload = {
        "event_id": event_id,
        "meeting_point_id": meeting_point_id,
        "tour_type_id": tour_type_id,
    }

    response = requests.post(
        "https://bassliner.org/api/event/tours", data=request_payload
    )
    return json.loads(response.text)


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome! Use /check to check for available buses to Fusion festival."
    )

async def check(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(check_buses())

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

def main():
    token = os.getenv("TG_API_TOKEN")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
