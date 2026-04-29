import logging
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth.deps import get_current_user, get_current_user_optional
from .config import settings
from .database import get_db, init_db, engine
from .generator import generate_pairs, shuffle_items
from .models import Game, GameAnswer, GamePair, SystemConfig, User
from .routes import admin, analytics, auth, history
from .schemas import (
    CONFIG_KEY_OPENAI_API_KEY,
    CONFIG_KEY_OPENAI_BASE_URL,
    CONFIG_KEY_OPENAI_MODEL,
    CONFIG_KEYS,
    ConfigItem,
    ConfigUpdateRequest,
    CreateGameRequest,
    CreateGameResponse,
    ItemResponse,
    ResultItem,
    SubmitRequest,
    SubmitResponse,
)

logging.basicConfig(level=logging.INFO)

LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def _get_config(db: Session, key: str) -> str | None:
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else None


def _require_local_config_access(request: Request) -> None:
    client_host = request.client.host if request.client else None
    if client_host not in LOOPBACK_HOSTS:
        raise HTTPException(status_code=403, detail="配置接口仅允许本机访问")


def _serialize_config(config: SystemConfig) -> ConfigItem:
    is_secret = config.key == CONFIG_KEY_OPENAI_API_KEY
    return ConfigItem(
        key=config.key,
        value=None if is_secret else config.value,
        description=config.description,
        configured=bool(config.value.strip()),
    )

logger = logging.getLogger(__name__)

app = FastAPI(title="Historical Pairing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list({settings.client_origin, "http://127.0.0.1:5173"}),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(admin.router)
app.include_router(analytics.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        logger.error("Health check failed: %s", e)
        raise HTTPException(status_code=503, detail="database unreachable") from e


@app.post("/api/games", response_model=CreateGameResponse)
async def create_game(
    payload: CreateGameRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CreateGameResponse:
    keyword = payload.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=422, detail="关键词不能为空")

    openai_key = _get_config(db, CONFIG_KEY_OPENAI_API_KEY)
    openai_base_url = _get_config(db, CONFIG_KEY_OPENAI_BASE_URL)
    openai_model = _get_config(db, CONFIG_KEY_OPENAI_MODEL)

    logger.info("Creating game for keyword: %s", keyword)
    generated = await generate_pairs(keyword, api_key=openai_key, base_url=openai_base_url, model=openai_model)
    game = Game(keyword=keyword, total=4, status="created", user_id=current_user.id if current_user else None)
    db.add(game)
    db.flush()
    logger.info("Game created: id=%s, keyword=%s", game.id, keyword)

    pairs: list[GamePair] = []
    for pair in generated:
        game_pair = GamePair(
            game_id=game.id,
            left_text=pair.left,
            right_text=pair.right,
            explanation=pair.explanation,
            pair_type=pair.type,
        )
        db.add(game_pair)
        pairs.append(game_pair)

    db.commit()
    for pair in pairs:
        db.refresh(pair)

    return CreateGameResponse(
        gameId=game.id,
        keyword=game.keyword,
        leftItems=[ItemResponse(id=pair.id, text=pair.left_text) for pair in pairs],
        rightItems=[
            ItemResponse(id=pair.right_option_id, text=pair.right_text)
            for pair in shuffle_items(pairs)
        ],
    )


@app.post("/api/games/{game_id}/submit", response_model=SubmitResponse)
def submit_game(
    game_id: str,
    payload: SubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmitResponse:
    logger.info("Submitting game: id=%s, match_count=%d", game_id, len(payload.matches))
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="游戏不存在")
    if game.user_id is not None and game.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权提交该游戏")
    if game.status == "submitted":
        raise HTTPException(status_code=409, detail="游戏已提交，请勿重复提交")

    pairs = list(game.pairs)
    pair_by_left_id = {pair.id: pair for pair in pairs}
    right_text_by_id = {pair.right_option_id: pair.right_text for pair in pairs}
    expected_left_ids = set(pair_by_left_id)
    expected_right_ids = set(right_text_by_id)
    submitted_left_ids = {match.leftId for match in payload.matches}
    submitted_right_ids = {match.rightId for match in payload.matches}
    if submitted_left_ids != expected_left_ids or submitted_right_ids != expected_right_ids:
        raise HTTPException(status_code=422, detail="提交答案与当前游戏题目不匹配")
    submitted = {match.leftId: match.rightId for match in payload.matches}

    db.query(GameAnswer).filter(GameAnswer.game_id == game.id).delete()

    score = 0
    results: list[ResultItem] = []
    for pair in pairs:
        selected_right_id = submitted.get(pair.id)
        selected_right_text = right_text_by_id.get(selected_right_id or "")
        is_correct = selected_right_id == pair.right_option_id
        if is_correct:
            score += 1

        if selected_right_id is not None and pair.id in pair_by_left_id:
            db.add(
                GameAnswer(
                    game_id=game.id,
                    pair_id=pair.id,
                    selected_right_id=selected_right_id,
                    selected_right_text=selected_right_text or "未识别选项",
                    is_correct=is_correct,
                )
            )

        results.append(
            ResultItem(
                leftId=pair.id,
                left=pair.left_text,
                userRight=selected_right_text,
                correctRight=pair.right_text,
                isCorrect=is_correct,
                explanation=pair.explanation,
                type=pair.pair_type,
            )
        )

    game.score = score
    game.status = "submitted"
    game.submitted_at = datetime.now(timezone.utc)
    db.commit()

    return SubmitResponse(score=score, total=game.total, results=results)


@app.get("/api/configs", response_model=list[ConfigItem])
def list_configs(request: Request, db: Session = Depends(get_db)) -> list[ConfigItem]:
    _require_local_config_access(request)
    configs = db.query(SystemConfig).all()
    return [_serialize_config(config) for config in configs]


@app.put("/api/configs/{config_key}", response_model=ConfigItem)
def update_config(
    config_key: str,
    payload: ConfigUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ConfigItem:
    _require_local_config_access(request)
    if config_key not in CONFIG_KEYS:
        raise HTTPException(status_code=400, detail=f"不允许修改该配置项: {config_key}")
    if payload.key != config_key:
        raise HTTPException(status_code=400, detail="请求体 key 与路径参数不一致")

    config = db.query(SystemConfig).filter(SystemConfig.key == config_key).first()
    if config is None:
        config = SystemConfig(key=config_key, value=payload.value)
        db.add(config)
    else:
        config.value = payload.value

    db.commit()
    db.refresh(config)
    logger.info("Config updated: %s", config_key)
    return _serialize_config(config)
