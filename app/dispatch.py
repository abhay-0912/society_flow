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
    response = supabase.table("workers").select("*").eq(
        "skill", category
    ).eq(
        "status", "available"
    ).limit(1).execute()

    if response.data:
        return response.data[0]
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

    message = (
        f"*New Job Assigned*\n\n"
        f"Ticket  : {ticket_id[:8].upper()}\n"
        f"Issue   : {summary}\n"
        f"Contact : {resident_phone}\n\n"
        f"Reply *DONE* when completed."
    )

    twilio_client.messages.create(
        from_=TWILIO_NUMBER,
        to=worker["phone"],
        body=message
    )

def notify_no_worker(resident_phone: str):
    twilio_client.messages.create(
        from_=TWILIO_NUMBER,
        to=resident_phone,
        body="We have received your complaint. Our team will assign a worker shortly and notify you."
    )
