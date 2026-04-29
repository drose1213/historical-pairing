from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..database import get_db
from ..models import Game, GameAnswer, GamePair, User

router = APIRouter(prefix="/api/history", tags=["history"])


class HistoryItem(BaseModel):
    id: str
    keyword: str
    score: int | None
    total: int
    time_used: int | None
    created_at: str

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int


class HistoryDetailResponse(BaseModel):
    id: str
    keyword: str
    score: int | None
    total: int
    time_used: int | None
    status: str
    created_at: str
    submitted_at: str | None
    results: list["HistoryResultItem"]


class HistoryResultItem(BaseModel):
    left: str
    right: str
    correct_right: str
    is_correct: bool
    explanation: str
    type: str


@router.get("", response_model=HistoryListResponse)
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryListResponse:
    total = db.query(Game).filter(Game.user_id == current_user.id).count()
    games = (
        db.query(Game)
        .filter(Game.user_id == current_user.id)
        .order_by(Game.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        HistoryItem(
            id=game.id,
            keyword=game.keyword,
            score=game.score,
            total=game.total,
            time_used=game.time_used,
            created_at=game.created_at.isoformat() if game.created_at else "",
        )
        for game in games
    ]

    return HistoryListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{game_id}", response_model=HistoryDetailResponse)
def get_history_detail(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryDetailResponse:
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if game is None:
        raise HTTPException(status_code=404, detail="游戏不存在")

    pairs = {pair.id: pair for pair in game.pairs}
    answers = {a.pair_id: a for a in db.query(GameAnswer).filter(GameAnswer.game_id == game_id).all()}

    results = []
    for pair in game.pairs:
        answer = answers.get(pair.id)
        results.append(
            HistoryResultItem(
                left=pair.left_text,
                right=answer.selected_right_text if answer else "未作答",
                correct_right=pair.right_text,
                is_correct=answer.is_correct if answer else False,
                explanation=pair.explanation,
                type=pair.pair_type,
            )
        )

    return HistoryDetailResponse(
        id=game.id,
        keyword=game.keyword,
        score=game.score,
        total=game.total,
        time_used=game.time_used,
        status=game.status,
        created_at=game.created_at.isoformat() if game.created_at else "",
        submitted_at=game.submitted_at.isoformat() if game.submitted_at else None,
        results=results,
    )


HistoryDetailResponse.model_rebuild()
