import os
from twilio.rest import Client
from app.database import supabase
from dotenv import load_dotenv

load_dotenv()

twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

def find_best_worker(category: str) -> dict | None:
    normalized_category = category.strip().lower()
    response = supabase.table("workers").select("*").eq(
        "skill", normalized_category
    ).eq(
        "status", "available"
    ).limit(1).execute()

    if response.data:
        return response.data[0]

    # Fallback: assign any available worker if no exact skill match.
    fallback = supabase.table("workers").select("*").eq(
        "status", "available"
    ).limit(1).execute()
    if fallback.data:
        return fallback.data[0]

    return None

def assign_worker(ticket_id: str, worker: dict, summary: str, resident_phone: str):
    supabase.table("workers").update(
        {"status": "busy"}
    ).eq("id", worker["id"]).execute()

    supabase.table("tickets").update({
        "assigned_worker": worker["name"],
        "worker_id": worker["id"],
        "status": "assigned"
    }).eq("id", ticket_id).execute()

    short_id = ticket_id[:8].upper()

    message = (
        f"*New Job Assigned*\n\n"
        f"Ticket  : {short_id}\n"
        f"Issue   : {summary}\n"
        f"Contact : {resident_phone}\n\n"
        f"Reply *DONE* when completed."
    )

    try:
        twilio_client.messages.create(
            from_=TWILIO_NUMBER,
            to=worker["phone"],
            body=message
        )
    except Exception as exc:
        # Do not fail resident webhook if worker outbound message cannot be sent.
        print(f"Worker notify error: {exc}")
