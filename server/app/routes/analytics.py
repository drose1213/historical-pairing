from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user_optional
from ..database import get_db
from ..models import Game, User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class TrackEventRequest(BaseModel):
    event_type: str
    game_id: str | None = None
    user_id: str | None = None
    payload: dict | None = None


class TrackEventResponse(BaseModel):
    success: bool


@router.post("/track", response_model=TrackEventResponse)
def track_event(
    request: TrackEventRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> TrackEventResponse:
    # For now, just log the event
    # In production, this would store to a tracking table
    print(f"[ANALYTICS] event={request.event_type}, user={current_user.id if current_user else None}, game={request.game_id}")

    # TODO: Store to DataTrackingLog table if needed
    # For now, just acknowledge the event
    return TrackEventResponse(success=True)
