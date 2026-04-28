from pydantic import BaseModel, Field, model_validator


class GeneratedPair(BaseModel):
    left: str = Field(min_length=1, max_length=80)
    right: str = Field(min_length=1, max_length=120)
    explanation: str = Field(min_length=1, max_length=220)
    type: str = Field(min_length=1, max_length=30)


class GeneratedPairs(BaseModel):
    pairs: list[GeneratedPair] = Field(min_length=4, max_length=4)


class CreateGameRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=100)


class ItemResponse(BaseModel):
    id: str
    text: str


class CreateGameResponse(BaseModel):
    gameId: str
    keyword: str
    leftItems: list[ItemResponse]
    rightItems: list[ItemResponse]


class MatchInput(BaseModel):
    leftId: str
    rightId: str


class SubmitRequest(BaseModel):
    matches: list[MatchInput] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_unique_matches(self) -> "SubmitRequest":
        left_ids = [item.leftId for item in self.matches]
        right_ids = [item.rightId for item in self.matches]
        if len(set(left_ids)) != len(left_ids):
            raise ValueError("leftId must be unique")
        if len(set(right_ids)) != len(right_ids):
            raise ValueError("rightId must be unique")
        return self


class ResultItem(BaseModel):
    leftId: str
    left: str
    userRight: str | None
    correctRight: str
    isCorrect: bool
    explanation: str
    type: str


class SubmitResponse(BaseModel):
    score: int
    total: int
    results: list[ResultItem]


# System config keys
CONFIG_KEY_OPENAI_API_KEY = "openai_api_key"
CONFIG_KEY_OPENAI_BASE_URL = "openai_base_url"
CONFIG_KEY_OPENAI_MODEL = "openai_model"

CONFIG_KEYS = {CONFIG_KEY_OPENAI_API_KEY, CONFIG_KEY_OPENAI_BASE_URL, CONFIG_KEY_OPENAI_MODEL}


class ConfigItem(BaseModel):
    key: str
    value: str | None = None
    description: str | None = None
    configured: bool = False


class ConfigUpdateRequest(BaseModel):
    key: str
    value: str
