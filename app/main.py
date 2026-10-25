from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.schemas import LeadCreate, LeadStatusUpdate, FollowUpUpdate
from app.database import create_tables, get_connection
from app.courses import COURSES
from app.research import CAREER_ROADMAPS, LEARNING_RESOURCES


# -------------------------
# Project paths
# -------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"


# -------------------------
# Application startup
# -------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they do not exist.
    # Existing database data is preserved.
    create_tables()
    yield


app = FastAPI(
    title="AI Coaching Growth Agent",
    description=(
        "Student research, AI career guidance, "
        "and coaching institute lead management"
    ),
    version="0.3.0",
    lifespan=lifespan,
)


# -------------------------
# Static frontend
# -------------------------

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


# -------------------------
# Request models
# -------------------------

class AIQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class CareerGuidanceRequest(BaseModel):
    current_level: str = Field(min_length=2, max_length=50)
    career_goal: str = Field(min_length=3, max_length=200)
    weekly_hours: int = Field(ge=1, le=80)


class LeadReplyRequest(BaseModel):
    student_message: str = Field(min_length=3, max_length=2000)
    course_name: str = Field(min_length=2, max_length=100)
    verified_course_details: str = Field(
        min_length=5,
        max_length=2000,
    )


# -------------------------
# Home, dashboard and health
# -------------------------

@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/dashboard")
def institute_dashboard():
    dashboard_file = STATIC_DIR / "dashboard.html"

    if not dashboard_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Dashboard file not found. "
                   "Create static/dashboard.html first.",
        )

    return FileResponse(dashboard_file)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# -------------------------
# AI endpoints (Gemini)
# -------------------------

@app.post("/ai/ask")
def ask_ai_endpoint(request: AIQuestion):
    from app.ai_service import ask_ai

    try:
        answer = ask_ai(request.question)

        return {
            "question": request.question,
            "answer": answer,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI service failed. Check server logs.",
        ) from exc


@app.post("/ai/career-guidance")
def career_guidance(request: CareerGuidanceRequest):
    from app.ai_service import ask_ai

    prompt = f"""
Create a practical career learning roadmap for a student.

Current skill level: {request.current_level}
Career goal: {request.career_goal}
Available study time: {request.weekly_hours} hours per week

Include:
1. Learning phases in the correct order.
2. Important topics for each phase.
3. A practical project for each phase.
4. A realistic estimated timeline.
5. Free learning resources where possible.

Use simple English and beginner-friendly explanations.
Clearly state that the timeline is an estimate.
"""

    try:
        answer = ask_ai(prompt)

        return {
            "career_goal": request.career_goal,
            "current_level": request.current_level,
            "weekly_hours": request.weekly_hours,
            "roadmap": answer,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Career guidance service failed. "
                "Check server logs."
            ),
        ) from exc


@app.post("/ai/reply-draft")
def generate_lead_reply(request: LeadReplyRequest):
    from app.ai_service import ask_ai

    prompt = f"""
You are an assistant for a coaching institute.

Write a polite, professional reply to the student's enquiry.

Course name: {request.course_name}
Verified course details: {request.verified_course_details}
Student's message: {request.student_message}

Rules:
- Use simple, friendly English.
- Answer using only the verified course details.
- Do not invent fees, discounts, batch timings, or promises.
- If information is missing, say the institute needs to confirm it.
- Do not claim that the reply has been sent.
- Return only the reply draft.
"""

    try:
        draft = ask_ai(prompt)

        return {
            "course_name": request.course_name,
            "reply_draft": draft,
            "sent": False,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Reply draft generation failed. "
                "Check server logs."
            ),
        ) from exc


# -------------------------
# Lead management
# -------------------------

@app.post("/leads", status_code=201)
def create_lead(lead: LeadCreate):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (
                student_name,
                phone,
                interested_course,
                enquiry_message
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                lead.student_name,
                lead.phone,
                lead.interested_course,
                lead.enquiry_message,
            ),
        )

        lead_id = cursor.lastrowid

    return {
        "message": "Lead saved successfully",
        "lead_id": lead_id,
        "status": "new",
    }


@app.get("/leads")
def get_leads():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM leads ORDER BY id DESC"
        ).fetchall()

    return {
        "total": len(rows),
        "leads": [dict(row) for row in rows],
    }


@app.patch("/leads/{lead_id}/status")
def update_lead_status(
    lead_id: int,
    update: LeadStatusUpdate,
):
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE leads SET status = ? WHERE id = ?",
            (update.status, lead_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Lead not found",
            )

    return {
        "message": "Lead status updated successfully",
        "lead_id": lead_id,
        "status": update.status,
    }


@app.patch("/leads/{lead_id}/follow-up")
def schedule_follow_up(
    lead_id: int,
    update: FollowUpUpdate,
):
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE leads SET follow_up_at = ? WHERE id = ?",
            (update.follow_up_at.isoformat(), lead_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Lead not found",
            )

    return {
        "message": "Follow-up scheduled successfully",
        "lead_id": lead_id,
        "follow_up_at": update.follow_up_at.isoformat(),
    }


@app.get("/follow-ups")
def get_follow_ups():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM leads
            WHERE follow_up_at IS NOT NULL
              AND status NOT IN ('admitted', 'not_interested')
            ORDER BY follow_up_at ASC
            """
        ).fetchall()

    return {
        "total": len(rows),
        "follow_ups": [dict(row) for row in rows],
    }


# -------------------------
# Course search
# -------------------------

@app.get("/courses")
def get_courses():
    return {
        "total": len(COURSES),
        "courses": COURSES,
    }


@app.get("/courses/search")
def search_courses(
    q: str,
    level: str | None = None,
):
    query = q.strip().lower()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty",
        )

    results = []

    for course in COURSES:
        searchable_text = " ".join([
            course["name"],
            course["category"],
            course["level"],
            course["description"],
            " ".join(course["skills"]),
            " ".join(course["prerequisites"]),
        ]).lower()

        matches_query = query in searchable_text

        matches_level = (
            level is None
            or course["level"].lower() == level.strip().lower()
        )

        if matches_query and matches_level:
            results.append(course)

    return {
        "query": q,
        "total": len(results),
        "courses": results,
    }


# -------------------------
# Career research
# -------------------------

@app.get("/research/roadmaps")
def get_career_roadmaps():
    return {
        "total": len(CAREER_ROADMAPS),
        "roadmaps": CAREER_ROADMAPS,
    }


@app.get("/research/roadmaps/{roadmap_id}")
def get_career_roadmap(roadmap_id: str):
    roadmap = CAREER_ROADMAPS.get(roadmap_id)

    if roadmap is None:
        raise HTTPException(
            status_code=404,
            detail="Career roadmap not found",
        )

    return roadmap


@app.get("/research/resources")
def get_learning_resources(topic: str | None = None):
    resources = LEARNING_RESOURCES

    if topic:
        query = topic.strip().lower()

        resources = [
            resource
            for resource in LEARNING_RESOURCES
            if query in resource["topic"].lower()
            or query in resource["title"].lower()
        ]

    return {
        "total": len(resources),
        "resources": resources,
    }