import re

from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from app.ai import classify_complaint
from app.database import save_ticket, supabase
from app.dispatch import find_best_worker, assign_worker
from app.prompts.assistant_prompt import (
    ASK_FLAT_REPLY,
    ASK_NAME_AND_FLAT_REPLY,
    ASK_NAME_REPLY,
    ASK_PROBLEM_DETAIL_REPLY,
    GREETING_REPLY,
)

router = APIRouter()

pending_intakes: dict[str, dict] = {}

GREETING_WORDS = {"hi", "hello", "hey", "hii", "namaste", "namaskar"}

COMPLAINT_HINTS = {
    "problem",
    "issue",
    "complaint",
    "leak",
    "water",
    "paani",
    "tap",
    "pipe",
    "light",
    "electric",
    "power",
    "switch",
    "clean",
    "garbage",
    "trash",
    "waste",
    "security",
    "guard",
    "gate",
    "noise",
    "shor",
    "awaaz",
    "lift",
    "elevator",
    "drain",
    "sewer",
    "wifi",
    "internet",
    "smell",
    "odor",
}


def _normalize_message(message: str) -> str:
    return re.sub(r"\s+", " ", message.strip().lower())


def _is_greeting(message: str) -> bool:
    normalized = _normalize_message(message)
    return normalized in GREETING_WORDS


def _looks_like_complaint(message: str) -> bool:
    normalized = _normalize_message(message)
    if any(hint in normalized for hint in COMPLAINT_HINTS):
        return True

    complaint_phrases = (
        r"\bnot working\b",
        r"\bbroken\b",
        r"\bblocked\b",
        r"\bstuck\b",
        r"\bleaking\b",
        r"\bleak\b",
        r"\bno water\b",
        r"\bno power\b",
        r"\bpower cut\b",
        r"\bdirty\b",
        r"\bsmell\b",
        r"\bnoise\b",
        r"\bkharab\b",
        r"\bband\b",
        r"\bfault\b",
        r"\brepair\b",
        r"\bmaintenance\b",
    )

    return any(re.search(pattern, normalized) for pattern in complaint_phrases)


def _extract_name(message: str) -> str | None:
    patterns = [
        r"(?:my name is|i am|i'm|naam\s*(?:hai|hoon|hu)|mera naam\s*(?:hai)?|name\s*(?:is)?|naam)\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]{1,40})",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name = re.split(r"\b(?:flat|flat no|flat number|house|house no|apartment)\b", name, flags=re.IGNORECASE)[0].strip()
            if name:
                return name
    return None


def _extract_flat_number(message: str) -> str | None:
    patterns = [
        r"(?:flat(?:\s*(?:no|number))?|house(?:\s*(?:no|number))?|apartment)\s*[:\-#]?\s*([A-Za-z0-9/-]+)",
        r"(?:flat|house|apartment)\s*([0-9A-Za-z/-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _create_ticket_response(result: dict, ticket_id: str, worker: dict | None) -> str:
    short_ticket_id = ticket_id[:8].upper()

    if worker:
        return (
            "✅ Complaint Registered\n"
            "──────────────────\n"
            f"Ticket ID : *{short_ticket_id}*\n"
            f"Category  : {result['category'].capitalize()}\n"
            f"Priority  : {result['priority'].upper()}\n"
            "──────────────────\n"
            f"Worker *{worker['name']}* has been assigned."
        )

    return (
        "✅ Complaint Registered\n"
        "──────────────────\n"
        f"Ticket ID : *{short_ticket_id}*\n"
        f"Category  : {result['category'].capitalize()}\n"
        f"Priority  : {result['priority'].upper()}\n"
        "──────────────────\n"
        "Our team will assign a worker shortly."
    )


def _finalize_complaint(phone: str, state: dict) -> tuple[str, str]:
    complaint_text = state["problem"]
    resident_name = state["name"]
    flat_number = state["flat_number"]

    result = classify_complaint(complaint_text)
    ticket = save_ticket(
        phone,
        f"Name: {resident_name} | Flat: {flat_number} | Problem: {complaint_text}",
        result,
    )

    ticket_id = ticket["id"]
    worker = find_best_worker(result["category"])

    if worker:
        assign_worker(ticket_id, worker, result["summary"], phone)

    pending_intakes.pop(phone, None)

    return _create_ticket_response(result, ticket_id, worker), result["category"]


def _prompt_for_missing_details(state: dict) -> str:
    if not state.get("name") and not state.get("flat_number"):
        return ASK_NAME_AND_FLAT_REPLY
    if not state.get("name"):
        return ASK_NAME_REPLY
    if not state.get("flat_number"):
        return ASK_FLAT_REPLY
    return ASK_PROBLEM_DETAIL_REPLY

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

    state = pending_intakes.setdefault(
        From,
        {"problem": None, "name": None, "flat_number": None},
    )

    try:
        if _is_greeting(Body) and not state["problem"]:
            reply = GREETING_REPLY
        else:
            extracted_name = _extract_name(Body)
            extracted_flat = _extract_flat_number(Body)

            if extracted_name and not state["name"]:
                state["name"] = extracted_name
            if extracted_flat and not state["flat_number"]:
                state["flat_number"] = extracted_flat

            if state["problem"] is None:
                if _looks_like_complaint(Body):
                    state["problem"] = Body.strip()
                    if state["name"] and state["flat_number"]:
                        reply, category = _finalize_complaint(From, state)
                        print(f"Category  : {category}")
                    else:
                        reply = _prompt_for_missing_details(state)
                else:
                    reply = ASK_PROBLEM_DETAIL_REPLY
            else:
                if _looks_like_complaint(Body) and not (extracted_name or extracted_flat):
                    state["problem"] = f"{state['problem']} {Body.strip()}".strip()

                if state["name"] and state["flat_number"]:
                    reply, category = _finalize_complaint(From, state)
                    print(f"Category  : {category}")
                else:
                    reply = _prompt_for_missing_details(state)
    except Exception as exc:
        print(f"Webhook error: {exc}")
        reply = "We received your message, but our system had a temporary issue. Please try again in a minute."

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
