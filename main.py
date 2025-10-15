import json
import os
import uuid
from typing import List

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Meeting
from .schemas import MeetingOut
from .services.asr import ASRService
from .services.llm import LLMService


UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


app = FastAPI(title="Meeting Summarizer API")

# Allow requests from browsers opening the frontend via file:// (Origin 'null')
# and any local/static server origins. Credentials are disabled to support '*'.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/meetings/upload", response_model=MeetingOut)
async def upload_meeting(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"]:
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    uid = str(uuid.uuid4())
    stored_name = f"{uid}{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)

    contents = await file.read()
    with open(stored_path, "wb") as f:
        f.write(contents)

    # Transcribe
    try:
        asr = ASRService()
        transcript_text = asr.transcribe_file(stored_path)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {e}")

    # Summarize
    try:
        llm = LLMService()
        summary_data = llm.summarize(transcript_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Summarization failed: {e}")

    meeting = Meeting(
        filename=file.filename,
        transcript=transcript_text,
        summary=summary_data.get("summary"),
        decisions=json.dumps(summary_data.get("decisions", [])),
        action_items=json.dumps(summary_data.get("action_items", [])),
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return _to_meeting_out(meeting)


@app.get("/api/meetings", response_model=List[MeetingOut])
def list_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [_to_meeting_out(m) for m in meetings]


@app.get("/api/meetings/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return _to_meeting_out(meeting)


def _to_meeting_out(m: Meeting) -> MeetingOut:
    decisions: List[str] = []
    action_items: List[str] = []
    try:
        if m.decisions:
            decisions = json.loads(m.decisions)
    except Exception:
        decisions = []
    try:
        if m.action_items:
            action_items = json.loads(m.action_items)
    except Exception:
        action_items = []
    return MeetingOut(
        id=m.id,
        filename=m.filename,
        transcript=m.transcript,
        summary=m.summary,
        decisions=decisions,
        action_items=action_items,
    )


