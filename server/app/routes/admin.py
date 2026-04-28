from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

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

    # Total users
    total_users = db.query(User).count()

    # Active users (played in last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_users_7d = (
        db.query(Game.user_id)
        .filter(Game.created_at >= seven_days_ago, Game.user_id.isnot(None))
        .distinct()
        .count()
    )

    # Total games
    total_games = db.query(Game).count()

    # Average correct rate
    completed_games = db.query(Game).filter(Game.score.isnot(None)).all()
    if completed_games:
        avg_correct_rate = sum(g.score or 0 for g in completed_games) / sum(g.total for g in completed_games)
    else:
        avg_correct_rate = 0.0

    # Average time used
    games_with_time = db.query(Game).filter(Game.time_used.isnot(None)).all()
    if games_with_time:
        avg_time_used = sum(g.time_used or 0 for g in games_with_time) / len(games_with_time)
    else:
        avg_time_used = None

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

    users = db.query(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for user in users:
        last_game = (
            db.query(Game)
            .filter(Game.user_id == user.id)
            .order_by(Game.created_at.desc())
            .first()
        )
        total_games = db.query(Game).filter(Game.user_id == user.id).count()

        items.append(
            UserListItem(
                id=user.id,
                email=user.email,
                is_admin=user.is_admin,
                created_at=user.created_at.isoformat() if user.created_at else "",
                total_games=total_games,
                last_game_at=last_game.created_at.isoformat() if last_game and last_game.created_at else None,
            )
        )

    return UserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/games", response_model=GameListResponse)
def list_games(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> GameListResponse:
    total = db.query(Game).count()

    games = db.query(Game).order_by(Game.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for game in games:
        user_email = None
        if game.user_id:
            user = db.get(User, game.user_id)
            if user:
                user_email = user.email

        items.append(
            GameListItem(
                id=game.id,
                user_email=user_email,
                keyword=game.keyword,
                score=game.score,
                total=game.total,
                time_used=game.time_used,
                status=game.status,
                created_at=game.created_at.isoformat() if game.created_at else "",
            )
        )

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
