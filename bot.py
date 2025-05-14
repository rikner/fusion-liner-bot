import datetime
import json
import os
from enum import Enum
from typing import Optional

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
)

FUSION_EVENT_ID = 195
OUTWARD_TOUR_TYPE_ID = 1


class MeetingPoint(Enum):
    OSTBAHNHOF = 1
    ZOB = 2


def get_earliest_available_fusion_outward_departure_time(
    meeting_point: MeetingPoint,
) -> Optional[datetime.datetime]:
    tours = get_tours(
        event_id=FUSION_EVENT_ID,
        meeting_point_id=meeting_point.value,
        tour_type_id=OUTWARD_TOUR_TYPE_ID,
    )

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

    return earliest_available_tour_departure_time


def get_tours(event_id: int, meeting_point_id: MeetingPoint, tour_type_id: int):
    request_payload = {
        "event_id": event_id,
        "meeting_point_id": meeting_point_id,
        "tour_type_id": tour_type_id,
    }
    try:
        response = requests.post(
            "https://bassliner.org/api/event/tours", data=request_payload, timeout=2000
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tours: {e}")
        return []


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome! Use /check to check for available buses to Fusion festival."
    )


def perform_check() -> str:
    ostbahnhof_departure = get_earliest_available_fusion_outward_departure_time(
        meeting_point=MeetingPoint.OSTBAHNHOF
    )
    ostbahnhof_departure = (
        ostbahnhof_departure.strftime("%d.%m.%y, %H:%M") if ostbahnhof_departure else "No available seats"
    )
    
    zob_departure = get_earliest_available_fusion_outward_departure_time(
        meeting_point=MeetingPoint.ZOB
    )
    zob_departure = (
        zob_departure.strftime("%d.%m.%y, %H:%M") if zob_departure else "No available seats"
    )

    return """
    🚍 Earliest available bassliner to Fusion: 🍾 
    ---------------------------------------------
    
    From Ostbahnhof: {}

    From ZOB: {}

    ---------------------------------------------
    https://bassliner.org/en/tours/fusion-festival-2025

    """.format(
        ostbahnhof_departure, zob_departure
    )


async def check(update: Update, context: CallbackContext) -> None:
    result = perform_check()
    await update.message.reply_text(result)

async def error_handler(update: object, context: CallbackContext) -> None:
    print(f"Exception while handling update {update}: {context.error}")
    await update.message.reply_text("Oops, something went wrong! Maybe ask Dr. Uffi?")

def main():
    token = os.getenv("TG_API_TOKEN")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check))
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
