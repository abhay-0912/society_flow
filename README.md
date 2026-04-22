# SocietyFlow

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Twilio](https://img.shields.io/badge/Twilio-WhatsApp%20Integration-F22F46?logo=twilio&logoColor=white)](https://www.twilio.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-AI%20Classification-000000?logo=openai&logoColor=white)](https://openai.com/)
[![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-22C55E)](#)

> **AI-powered WhatsApp complaint management for residential societies.**
> SocietyFlow turns resident messages into structured tickets, routes them to the right worker, and keeps the resolution loop connected end-to-end.

## Live Demo

🌍 **Website:** [https://society-flow.onrender.com/](https://society-flow.onrender.com/)

## Problem Statement

Residential societies often handle complaints through scattered WhatsApp chats, manual follow-ups, and ad-hoc coordination. That creates avoidable delays, poor visibility, and inconsistent assignment of issues like plumbing, electrical, cleaning, security, and noise complaints.

## Solution Overview

SocietyFlow provides a conversational WhatsApp-based intake flow that collects complaint details step by step, classifies the issue with AI, stores it in Supabase, and assigns an available worker based on category and skill match. The result is a cleaner workflow for residents, workers, and society management.

## Features

- Conversational WhatsApp intake flow with polite Hinglish/Hindi responses
- Greeting handling that avoids creating tickets too early
- Step-by-step collection of complaint, resident name, and flat number
- AI-based complaint classification with fallback keyword logic
- Automatic ticket creation in Supabase
- Intelligent worker assignment based on category and availability
- WhatsApp notification to workers with job details and resident contact
- Worker completion flow using the `DONE` command
- Resident notification when a ticket is marked completed
- FastAPI-based webhook architecture designed for production deployment

## Tech Stack

### Backend

- FastAPI
- Uvicorn
- Python 3.13+

### Messaging & Automation

- Twilio WhatsApp API
- OpenAI API

### Database

- Supabase

### Configuration

- python-dotenv
- python-multipart

## Architecture Overview

1. A resident sends a WhatsApp message to the Twilio number.
2. Twilio forwards the message to the FastAPI `/webhook` endpoint.
3. The webhook checks conversation state and decides whether to greet, ask for missing details, or finalize the ticket.
4. Once the complaint, name, and flat number are collected, SocietyFlow classifies the issue using OpenAI.
5. The ticket is saved in Supabase with category, priority, summary, and status.
6. The dispatch layer finds the best available worker based on skill and marks them busy.
7. The worker receives the job on WhatsApp, and the resident receives a confirmation.
8. When the worker sends `DONE`, the ticket is marked complete and the resident is notified.

## Getting Started

### Prerequisites

- Python 3.13 or newer
- A Supabase project
- A Twilio account with WhatsApp enabled
- An OpenAI API key

### Installation

```bash
git clone https://github.com/abhay-0912/society_flow.git
cd society_flow
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_or_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### Run Locally

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```bash
http://127.0.0.1:8000
```

## Usage

### Resident Flow

1. Resident sends `Hi` or `Hello`.
2. Bot replies politely and asks how it can help.
3. Resident describes the issue.
4. Bot asks for name and flat number.
5. Once all details are collected, SocietyFlow creates the ticket and confirms it.

### Worker Flow

1. Worker receives the assigned job on WhatsApp.
2. After completing the task, the worker sends `DONE`.
3. SocietyFlow marks the worker available again.
4. The resident receives a completion notification.

### Example Interaction

```text
Resident: Hi
Bot: Namaste 👋
     Hum aapki kaise sahayta kar sakte hain?

Resident: Tap leak ho raha hai
Bot: Kripya apna naam aur flat number batayein.

Resident: My name is Rajesh, Flat 305
Bot: ✅ Complaint Registered
     Category: Plumbing
     Priority: Medium
```

## Screenshots / Demo

> Add product screenshots here when available.

| Home / Dashboard | WhatsApp Intake | Ticket Confirmation |
|---|---|---|
| _Placeholder_ | _Placeholder_ | _Placeholder_ |

## Roadmap

- Persistent conversation state with Supabase or Redis
- Admin dashboard for live ticket tracking
- Resident authentication and profile linkage
- SLA-based escalation for high-priority tickets
- Analytics dashboard for complaint volume and resolution time
- Multi-language support expansion
- Smarter worker recommendation based on workload and response time

## Why This Project Stands Out

- Built around a real operational workflow, not a demo-only chatbot
- Converts unstructured resident messages into structured operational tickets
- Uses AI only where it adds value, with deterministic fallback logic for reliability
- Designed for WhatsApp-first communication, which matches real society operations
- Clear separation of concerns across intake, AI, database, and dispatch layers
- Strong portfolio value for backend, AI automation, and product engineering roles

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the flow locally
5. Open a pull request with a clear description

## License

No license has been declared yet. Add a `LICENSE` file before distributing or open-sourcing the project publicly.

## Author

**Abhay Srivastava**

AI-powered operations and workflow automation project focused on residential society service management.

If you found this project useful, consider starring the repository and sharing feedback for future improvements.