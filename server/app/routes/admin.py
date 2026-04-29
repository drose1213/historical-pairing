from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..auth.deps import get_current_admin_user
from ..database import get_db
from ..models import Game, SystemConfig, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users_7d: int
    total_games: int
    avg_correct_rate: float
    avg_time_used: float | None


class UserListItem(BaseModel):
    id: str
    email: str
    is_admin: bool
    created_at: str
    total_games: int
    last_game_at: str | None


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int


class GameListItem(BaseModel):
    id: str
    user_email: str | None
    keyword: str
    score: int | None
    total: int
    time_used: int | None
    status: str
    created_at: str


class GameListResponse(BaseModel):
    items: list[GameListItem]
    total: int
    page: int
    page_size: int


class ConfigItemResponse(BaseModel):
    key: str
    value: str | None
    configured: bool


@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> AdminStatsResponse:
    from datetime import datetime, timedelta, timezone

    total_users = db.query(User).count()

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_users_7d = (
        db.query(Game.user_id)
        .filter(Game.created_at >= seven_days_ago, Game.user_id.isnot(None))
        .distinct()
        .count()
    )

    total_games = db.query(Game).count()

    # Average correct rate - single query with aggregation
    stats = db.query(
        func.sum(Game.score).label("total_score"),
        func.sum(Game.total).label("total_total"),
    ).filter(Game.score.isnot(None)).first()

    if stats and stats.total_total:
        avg_correct_rate = stats.total_score / stats.total_total
    else:
        avg_correct_rate = 0.0

    # Average time used - single query
    time_stats = db.query(
        func.avg(Game.time_used).label("avg_time"),
    ).filter(Game.time_used.isnot(None)).first()

    avg_time_used = time_stats.avg_time if time_stats.avg_time else None

    return AdminStatsResponse(
        total_users=total_users,
        active_users_7d=active_users_7d,
        total_games=total_games,
        avg_correct_rate=avg_correct_rate,
        avg_time_used=avg_time_used,
    )


@router.get("/users", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> UserListResponse:
    total = db.query(User).count()

    # Subquery: count games per user
    game_count_subq = (
        select(Game.user_id, func.count(Game.id).label("game_count"))
        .group_by(Game.user_id)
        .subquery()
    )

    # Subquery: latest game timestamp per user
    last_game_subq = (
        select(Game.user_id, func.max(Game.created_at).label("last_game_at"))
        .group_by(Game.user_id)
        .subquery()
    )

    users = (
        db.query(
            User,
            func.coalesce(game_count_subq.c.game_count, 0).label("total_games"),
            last_game_subq.c.last_game_at.label("last_game_at"),
        )
        .outerjoin(game_count_subq, User.id == game_count_subq.c.user_id)
        .outerjoin(last_game_subq, User.id == last_game_subq.c.user_id)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        UserListItem(
            id=user.id,
            email=user.email,
            is_admin=user.is_admin,
            created_at=user.created_at.isoformat() if user.created_at else "",
            total_games=total_games,
            last_game_at=last_game_at.isoformat() if last_game_at else None,
        )
        for user, total_games, last_game_at in users
    ]

    return UserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/games", response_model=GameListResponse)
def list_games(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> GameListResponse:
    total = db.query(Game).count()

    games = (
        db.query(Game)
        .options(joinedload(Game.user))
        .order_by(Game.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        GameListItem(
            id=game.id,
            user_email=game.user.email if game.user else None,
            keyword=game.keyword,
            score=game.score,
            total=game.total,
            time_used=game.time_used,
            status=game.status,
            created_at=game.created_at.isoformat() if game.created_at else "",
        )
        for game in games
    ]

    return GameListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/configs", response_model=list[ConfigItemResponse])
def list_configs(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> list[ConfigItemResponse]:
    configs = db.query(SystemConfig).all()
    return [
        ConfigItemResponse(
            key=c.key,
            value=c.value if c.key != "openai_api_key" else None,
            configured=bool(c.value.strip()) if c.value else False,
        )
        for c in configs
    ]


@router.put("/configs/{config_key}", response_model=ConfigItemResponse)
def update_config(
    config_key: str,
    value: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> ConfigItemResponse:
    config = db.query(SystemConfig).filter(SystemConfig.key == config_key).first()
    if config is None:
        config = SystemConfig(key=config_key, value=value)
        db.add(config)
    else:
        config.value = value
    db.commit()
    db.refresh(config)

    return ConfigItemResponse(
        key=config.key,
        value=config.value if config.key != "openai_api_key" else None,
        configured=bool(config.value.strip()) if config.value else False,
    )
