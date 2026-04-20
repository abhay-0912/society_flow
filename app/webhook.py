from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from app.ai import classify_complaint
from app.database import save_ticket, supabase
from app.dispatch import find_best_worker, assign_worker, notify_no_worker

router = APIRouter()

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
):
    # Handle worker DONE command
    if Body.strip().upper() == "DONE":
        handle_done(From)
        return PlainTextResponse(
            content="""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>Great work! Your status is now available.</Message></Response>""",
            media_type="application/xml"
        )

    print(f"\n--- New Message ---")
    print(f"From: {From}")
    print(f"Message: {Body}")

    result = classify_complaint(Body)
    ticket_id = save_ticket(From, Body, result)

    print(f"Category  : {result['category']}")
    print(f"Priority  : {result['priority']}")
    print(f"Ticket ID : {ticket_id}")

    worker = find_best_worker(result["category"])

    if worker:
        assign_worker(ticket_id, worker, result["summary"], From)
        reply = (
            f"{result['reply']}\n\n"
            f"Ticket ID: *{ticket_id}*\n"
            f"Worker *{worker['name']}* has been assigned and will reach you shortly."
        )
        print(f"Assigned  : {worker['name']}")
    else:
        notify_no_worker(From)
        reply = (
            f"{result['reply']}\n\n"
            f"Ticket ID: *{ticket_id}*\n"
            f"We will assign a worker shortly."
        )
        print(f"Assigned  : No worker found")

    print(f"-------------------\n")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply}</Message>
</Response>"""

    return PlainTextResponse(content=twiml, media_type="application/xml")


def handle_done(worker_phone: str):
    worker = supabase.table("workers").select("*").eq(
        "phone", worker_phone
    ).single().execute().data

    if not worker:
        return

    supabase.table("workers").update(
        {"status": "available"}
    ).eq("id", worker["id"]).execute()

    ticket = supabase.table("tickets").select("*").eq(
        "worker_id", worker["id"]
    ).eq(
        "status", "assigned"
    ).limit(1).execute()

    if ticket.data:
        t = ticket.data[0]
        supabase.table("tickets").update(
            {"status": "completed"}
        ).eq("id", t["id"]).execute()

        from twilio.rest import Client
        import os
        from dotenv import load_dotenv
        load_dotenv()
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(
            from_=os.getenv("TWILIO_WHATSAPP_NUMBER"),
            to=t["resident_phone"],
            body=f"Your complaint (*{t['id'][:8].upper()}*) has been resolved by {worker['name']}. Thank you!"
        )
