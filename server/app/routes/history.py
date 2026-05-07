from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user, get_current_user_optional
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


class PeriodStats(BaseModel):
    keyword: str
    count: int
    avg_score: float


class PairTypeStats(BaseModel):
    pair_type: str
    total: int
    correct: int
    correct_rate: float


class UserStatsResponse(BaseModel):
    total_games: int
    avg_score: float
    min_score: int
    max_score: int
    avg_time: float | None
    min_time: int | None
    max_time: int | None
    periods: list[PeriodStats]
    pair_types: list[PairTypeStats]
    tendency: str


class RecentKeywordsResponse(BaseModel):
    keywords: list[str]


_DEFAULT_KEYWORDS = ["三国", "唐朝", "秦始皇", "法国大革命", "工业革命"]


class HistoryResultItem(BaseModel):
    left: str
    right: str
    correct_right: str
    is_correct: bool
    explanation: str
    type: str


def _build_tendency(pair_types: list[PairTypeStats]) -> str:
    if not pair_types:
        return "暂无足够数据生成倾向分析"
    best = max(pair_types, key=lambda p: p.correct_rate)
    worst = min(pair_types, key=lambda p: p.correct_rate)
    if best.pair_type == worst.pair_type or best.correct_rate == worst.correct_rate:
        return f"各类题型表现均衡，整体正确率 {best.correct_rate:.0%}"
    return f"擅长{best.pair_type}类（正确率 {best.correct_rate:.0%}），弱项为{worst.pair_type}类（正确率 {worst.correct_rate:.0%}）"


@router.get("/stats", response_model=UserStatsResponse)
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserStatsResponse:
    submitted_games = (
        db.query(Game)
        .filter(Game.user_id == current_user.id, Game.status == "submitted")
        .all()
    )
    total_games = len(submitted_games)

    if total_games == 0:
        return UserStatsResponse(
            total_games=0, avg_score=0.0, min_score=0, max_score=0,
            avg_time=None, min_time=None, max_time=None,
            periods=[], pair_types=[], tendency="暂无游戏记录",
        )

    scores = [g.score for g in submitted_games if g.score is not None]
    times = [g.time_used for g in submitted_games if g.time_used is not None]

    avg_score = sum(scores) / len(scores) if scores else 0.0
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    avg_time = sum(times) / len(times) if times else None
    min_time = min(times) if times else None
    max_time = max(times) if times else None

    period_map: dict[str, list[int]] = {}
    for g in submitted_games:
        if g.score is not None:
            period_map.setdefault(g.keyword, []).append(g.score)
    periods = [
        PeriodStats(keyword=k, count=len(v), avg_score=round(sum(v) / len(v), 2))
        for k, v in sorted(period_map.items(), key=lambda x: len(x[1]), reverse=True)
    ]

    game_ids = [g.id for g in submitted_games]
    pair_type_rows = (
        db.query(GamePair.pair_type, func.count(GamePair.id))
        .filter(GamePair.game_id.in_(game_ids))
        .group_by(GamePair.pair_type)
        .all()
    )
    correct_rows = (
        db.query(GamePair.pair_type, func.count(GameAnswer.id))
        .join(GameAnswer, GameAnswer.pair_id == GamePair.id)
        .filter(GamePair.game_id.in_(game_ids), GameAnswer.is_correct == True)  # noqa: E712
        .group_by(GamePair.pair_type)
        .all()
    )
    correct_map = {row[0]: row[1] for row in correct_rows}
    pair_types = [
        PairTypeStats(
            pair_type=pt,
            total=int(cnt),
            correct=correct_map.get(pt, 0),
            correct_rate=round(correct_map.get(pt, 0) / cnt, 2) if cnt > 0 else 0.0,
        )
        for pt, cnt in pair_type_rows
    ]

    tendency = _build_tendency(pair_types)

    return UserStatsResponse(
        total_games=total_games,
        avg_score=round(avg_score, 2),
        min_score=min_score,
        max_score=max_score,
        avg_time=round(avg_time, 1) if avg_time is not None else None,
        min_time=min_time,
        max_time=max_time,
        periods=periods,
        pair_types=pair_types,
        tendency=tendency,
    )


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


@router.get("/recent-keywords", response_model=RecentKeywordsResponse)
def get_recent_keywords(
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> RecentKeywordsResponse:
    """返回用户最近游玩的 Top 5 关键词，未登录返回默认列表。"""
    if current_user is None:
        return RecentKeywordsResponse(keywords=_DEFAULT_KEYWORDS)

    games = (
        db.query(Game)
        .filter(Game.user_id == current_user.id, Game.status == "submitted")
        .order_by(Game.created_at.desc())
        .limit(50)
        .all()
    )

    seen: set[str] = set()
    keywords: list[str] = []
    for g in games:
        if g.keyword not in seen:
            seen.add(g.keyword)
            keywords.append(g.keyword)
        if len(keywords) >= 5:
            break

    return RecentKeywordsResponse(keywords=keywords or _DEFAULT_KEYWORDS)


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
