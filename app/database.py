import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def save_ticket(resident_phone: str, message: str, result: dict) -> str:
    response = supabase.table("tickets").insert({
        "resident_phone": resident_phone,
        "message": message,
        "category": result["category"],
        "priority": result["priority"],
        "summary": result["summary"],
        "status": "open"
    }).execute()

    ticket_id = response.data[0]["id"]
    short_id = ticket_id[:8].upper()
    return short_id
