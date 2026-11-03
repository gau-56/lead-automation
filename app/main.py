from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.db import get_conn, init_db
from app.scoring import analyze_lead

app = FastAPI(title="AI Lead Automation")
init_db()

FORM_PATH = Path(__file__).parent / "form.html"


class LeadIn(BaseModel):
    name: str
    email: str
    phone: str = ""
    message: str


@app.get("/", include_in_schema=False)
def form_page():
    return FileResponse(FORM_PATH)


@app.post("/leads")
def create_lead(lead: LeadIn):
    result = analyze_lead(lead.name, lead.message)
    with get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO leads
               (name, email, phone, message, score, category, summary, suggested_reply)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lead.name, lead.email, lead.phone, lead.message,
                result["score"], result["category"],
                result["summary"], result["suggested_reply"],
            ),
        )
        lead_id = cursor.lastrowid
    return {"id": lead_id, **result}


@app.get("/leads")
def list_leads():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]