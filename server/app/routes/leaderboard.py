from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Game, User

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        return local[0] + "**@" + domain
    return local[:2] + "**@" + domain


class LeaderboardItem(BaseModel):
    rank: int
    email: str
    total_games: int
    avg_score: float
    best_score: int
    total_correct: int


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardItem]
    total: int
    page: int
    page_size: int


@router.get("", response_model=LeaderboardResponse)
def get_leaderboard(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("avg_score", pattern="^(avg_score|total_games|best_score|total_correct)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> LeaderboardResponse:
    stats = (
        db.query(
            Game.user_id,
            func.count(Game.id).label("total_games"),
            func.avg(Game.final_score).label("avg_score"),
            func.max(Game.final_score).label("best_score"),
            func.sum(Game.score).label("total_correct"),
        )
        .filter(Game.status == "submitted", Game.user_id.isnot(None), Game.final_score.isnot(None))
        .group_by(Game.user_id)
        .all()
    )

    sort_key_map = {
        "avg_score": lambda s: float(s.avg_score or 0),
        "total_games": lambda s: int(s.total_games or 0),
        "best_score": lambda s: int(s.best_score or 0),
        "total_correct": lambda s: int(s.total_correct or 0),
    }
    sort_key = sort_key_map.get(sort_by, sort_key_map["avg_score"])
    ranked = sorted(stats, key=sort_key, reverse=(sort_order == "desc"))
    total = len(ranked)

    user_ids = [row.user_id for row in ranked]
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    start = (page - 1) * page_size
    end = start + page_size
    page_items = ranked[start:end]

    items = []
    for i, row in enumerate(page_items, start=start + 1):
        user = users.get(row.user_id)
        items.append(
            LeaderboardItem(
                rank=i,
                email=_mask_email(user.email) if user else "未知",
                total_games=int(row.total_games or 0),
                avg_score=round(float(row.avg_score or 0), 2),
                best_score=int(row.best_score or 0),
                total_correct=int(row.total_correct or 0),
            )
        )

    return LeaderboardResponse(items=items, total=total, page=page, page_size=page_size)
