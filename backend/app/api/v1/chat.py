"""AI Chat and Copilot API Endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User
from app.services.ai_chat.chat_service import ai_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(default="user", description="'user' or 'model'")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list)
    gemini_api_key: str | None = Field(default=None, description="Optional user-provided Gemini API key")


class ChatResponse(BaseModel):
    reply: str
    model: str
    live_stats: dict[str, Any] | None = None
    timestamp: str


class SuggestionResponse(BaseModel):
    suggestions: list[str]


@router.post("", response_model=ChatResponse)
async def chat_with_copilot(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Interact with the AI Copilot. Combines live application state with universal AI intelligence."""
    history_dicts = [{"role": m.role, "content": m.content} for m in payload.history]
    result = await ai_chat_service.generate_response(
        message=payload.message,
        history=history_dicts,
        user=current_user,
        db=db,
        gemini_api_key=payload.gemini_api_key,
    )
    return ChatResponse(**result)


@router.get("/suggestions", response_model=SuggestionResponse)
def get_quick_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return contextual quick-action suggestions for the user."""
    context = ai_chat_service.gather_live_context(current_user, db)
    stats = context["today_stats"]

    suggestions = [
        f"📊 Innaki evlo jobs vanthuchu? ({stats['jobs_found']} found)",
        f"⏳ Show {stats['pending_approval']} jobs in my Approval Queue",
        "🎯 How to prepare for Next.js / React technical interviews?",
        "🤖 Is my Bot active and scheduled right now?",
    ]
    return SuggestionResponse(suggestions=suggestions)
