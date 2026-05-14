import json
import logging
import random
import re
from typing import TypeVar

from fastapi import HTTPException
from openai import APIError, APITimeoutError, AsyncOpenAI
from pydantic import ValidationError

from .config import settings
from .schemas import GeneratedPair, GeneratedPairs

logger = logging.getLogger(__name__)

T = TypeVar("T")


PROMPT = """你是一个严谨的历史知识学家以及出题小能手。

请根据用户输入的关键词生成 4 组历史配对题。

关键词：{keyword}

要求：
1. 只生成与关键词强相关的历史内容。
2. 每组包含 left、right、explanation、type。
3. left 和 right 必须可以明确一一配对。
4. 不要生成有争议或模糊答案。
5. left 不超过 20 个汉字，right 不超过 32 个汉字。
6. explanation 控制在 80 字以内。
7. 4 组题必须是 4 个彼此不同的历史对象或角度，但都要和关键词有明确关联；优先覆盖人物、事件、制度/政策、作品/思想、地点、影响等不同类型。
8. 不要把同一个关键词机械改写成“关键词背景、关键词人物、关键词事件、关键词影响”这类模板题；left 不要全部以关键词开头，也不要全部围绕同一个人或同一个事件。
9. 如果关键词是人物，可以围绕其相关事件、关系人物、作品/政策、历史影响分别出题；如果关键词是事件，可以围绕起因、关键人物、过程节点、结果影响分别出题，但 left 必须是具体名称而不是泛泛标签。
10. 如果关键词不是历史相关内容，仍尝试从历史角度解释；完全无关时返回与“历史学习”相关的基础配对。
11. 返回严格 JSON，不要输出 Markdown。

返回格式：
{{
  "pairs": [
    {{"left": "", "right": "", "explanation": "", "type": ""}}
  ]
}}
"""


SEED_BANK: dict[str, list[GeneratedPair]] = {
    "三国": [
        GeneratedPair(left="赤壁之战", right="孙刘联军击败曹操", explanation="赤壁之战奠定了三国鼎立的重要基础。", type="事件-结果"),
        GeneratedPair(left="诸葛亮", right="隆中对", explanation="隆中对提出联吴抗曹、取荆益的战略设想。", type="人物-事迹"),
        GeneratedPair(left="曹操", right="挟天子以令诸侯", explanation="曹操控制汉献帝后取得政治号召力。", type="人物-策略"),
        GeneratedPair(left="刘备", right="建立蜀汉", explanation="刘备在成都称帝，建立蜀汉政权。", type="人物-政权"),
    ],
    "唐朝": [
        GeneratedPair(left="唐太宗", right="贞观之治", explanation="唐太宗时期政治清明、经济恢复，史称贞观之治。", type="皇帝-治世"),
        GeneratedPair(left="武则天", right="周朝政权", explanation="武则天改唐为周，是中国历史上重要的女皇帝。", type="人物-政权"),
        GeneratedPair(left="唐玄宗", right="开元盛世", explanation="唐玄宗前期国力强盛，出现开元盛世。", type="皇帝-治世"),
        GeneratedPair(left="安史之乱", right="唐朝由盛转衰", explanation="安史之乱严重削弱中央集权和社会经济。", type="事件-影响"),
    ],
    "秦始皇": [
        GeneratedPair(left="秦始皇", right="统一六国", explanation="秦始皇结束战国割据，建立统一秦朝。", type="人物-事迹"),
        GeneratedPair(left="郡县制", right="加强中央集权", explanation="郡县制削弱分封势力，强化中央治理。", type="制度-作用"),
        GeneratedPair(left="统一文字", right="小篆推广", explanation="统一文字便利政令传达和文化交流。", type="政策-内容"),
        GeneratedPair(left="统一度量衡", right="促进经济往来", explanation="度量衡统一降低了各地交易和管理成本。", type="政策-影响"),
    ],
    "法国大革命": [
        GeneratedPair(left="攻占巴士底狱", right="革命爆发象征", explanation="1789 年攻占巴士底狱成为法国大革命的重要象征。", type="事件-意义"),
        GeneratedPair(left="《人权宣言》", right="宣示自由平等", explanation="《人权宣言》体现资产阶级革命的政治原则。", type="文件-主张"),
        GeneratedPair(left="路易十六", right="被送上断头台", explanation="路易十六被处死标志君主制权威崩塌。", type="人物-结局"),
        GeneratedPair(left="雅各宾派", right="革命专政", explanation="雅各宾派执政时期采取激进革命措施。", type="派别-政策"),
    ],
    "工业革命": [
        GeneratedPair(left="瓦特", right="改良蒸汽机", explanation="改良蒸汽机推动机器生产和工厂制度发展。", type="人物-发明"),
        GeneratedPair(left="珍妮纺纱机", right="提高纺纱效率", explanation="珍妮纺纱机是纺织业机械化的重要发明。", type="发明-作用"),
        GeneratedPair(left="英国", right="率先发生工业革命", explanation="英国具备市场、资本、技术和劳动力条件。", type="国家-事件"),
        GeneratedPair(left="工厂制度", right="集中机器生产", explanation="工厂制度改变了传统手工业生产方式。", type="制度-特点"),
    ],
}


def _fallback_pairs(keyword: str) -> list[GeneratedPair]:
    normalized = keyword.strip().lower()
    for key, pairs in SEED_BANK.items():
        if key.lower() in normalized or normalized in key.lower():
            return pairs

    cleaned = keyword.strip() or "历史"
    return [
        GeneratedPair(left="时代背景", right="理解历史条件", explanation=f"学习 {cleaned} 时，先看其所处时代的政治、经济、文化条件。", type="背景-条件"),
        GeneratedPair(left="相关人物", right="梳理行动关系", explanation=f"围绕 {cleaned} 找相关人物，比较他们的行动、立场和相互关系。", type="人物-关系"),
        GeneratedPair(left="关键事件", right="判断因果脉络", explanation=f"把 {cleaned} 放入具体事件中，按原因、经过、结果建立配对。", type="事件-因果"),
        GeneratedPair(left="历史影响", right="比较长期变化", explanation=f"从制度、社会、经济和文化角度观察 {cleaned} 带来的变化。", type="影响-变化"),
    ]


def _dedupe_and_validate(pairs: list[GeneratedPair], keyword: str = "") -> list[GeneratedPair]:
    seen_left: set[str] = set()
    seen_right: set[str] = set()
    cleaned: list[GeneratedPair] = []

    for pair in pairs:
        left = pair.left.strip()
        right = pair.right.strip()
        if not left or not right:
            continue
        # Deduplicate: skip if this left or this right was already used
        if left in seen_left or right in seen_right:
            continue
        seen_left.add(left)
        seen_right.add(right)
        cleaned.append(
            GeneratedPair(
                left=left,
                right=right,
                explanation=pair.explanation.strip(),
                type=pair.type.strip(),
            )
        )

    if len(cleaned) < 4:
        raise ValueError(f"generated pairs must contain at least 4 unique pairs, got {len(cleaned)}")
    _validate_diverse_pairs(cleaned[:4], keyword)
    return cleaned[:4]


def _validate_diverse_pairs(pairs: list[GeneratedPair], keyword: str) -> None:
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return

    generic_suffixes = (
        "背景",
        "人物",
        "事件",
        "影响",
        "原因",
        "结果",
        "意义",
        "作用",
        "评价",
        "概念",
        "方法",
    )
    templated_lefts = [
        pair.left
        for pair in pairs
        if pair.left == f"{normalized_keyword}{next((suffix for suffix in generic_suffixes if pair.left.endswith(suffix)), '')}"
        or any(pair.left == f"{normalized_keyword}{suffix}" for suffix in generic_suffixes)
    ]
    keyword_prefixed_lefts = [pair.left for pair in pairs if pair.left.startswith(normalized_keyword)]
    if len(templated_lefts) >= 2 or len(keyword_prefixed_lefts) >= 3:
        raise ValueError("generated pairs are too template-like around the keyword")

    type_heads = {re.split(r"[-—－]", pair.type, maxsplit=1)[0].strip() for pair in pairs if pair.type.strip()}
    if len(type_heads) < 3:
        raise ValueError("generated pairs must cover at least 3 different item types")


def _extract_json_payload(content: str) -> dict:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("empty response content")

    # Remove reasoning blocks returned by some compatible providers such as MiniMax.
    cleaned = re.sub(r"<think>.*?</think>\s*", "", cleaned, flags=re.DOTALL).strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    decoder = json.JSONDecoder()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as original_exc:
        # Some compatible providers wrap JSON with prose. Scan for the first
        # complete JSON object instead of only trimming to the last brace.
        for match in re.finditer(r"\{", cleaned):
            try:
                payload, _ = decoder.raw_decode(cleaned[match.start() :])
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                continue
        raise original_exc


async def generate_pairs(
    keyword: str,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> list[GeneratedPair]:
    effective_key = api_key or settings.openai_api_key
    if not effective_key:
        return _fallback_pairs(keyword)

    client_kwargs: dict = {"api_key": effective_key}
    effective_base_url = base_url or settings.openai_base_url
    if effective_base_url:
        client_kwargs["base_url"] = effective_base_url
    client = AsyncOpenAI(**client_kwargs)

    for attempt in range(3):
        try:
            request_kwargs = {
                "model": model or settings.openai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你只输出严格 JSON。所有字符串必须使用双引号并正确转义，"
                            "不要输出 Markdown、注释、尾随逗号或额外说明。"
                        ),
                    },
                    {"role": "user", "content": PROMPT.format(keyword=keyword.strip())},
                ],
                "temperature": 0.4 + attempt * 0.1,
                "timeout": 30,
            }
            if not effective_base_url or effective_base_url.lower().rstrip("/") == "https://api.openai.com/v1":
                request_kwargs["response_format"] = {"type": "json_object"}

            response = await client.chat.completions.create(**request_kwargs)
        except Exception as exc:
            logger.exception("API call failed: %s", type(exc).__name__)
            raise HTTPException(status_code=502, detail=f"API 调用失败: {type(exc).__name__}: {exc}") from exc

        content = response.choices[0].message.content or ""
        logger.info("Raw LLM response: %s", content[:2000])
        try:
            payload = _extract_json_payload(content)
            parsed = GeneratedPairs.model_validate(payload)
            logger.info("Parsed pairs count before dedupe: %d", len(parsed.pairs))
            return _dedupe_and_validate(parsed.pairs, keyword)
        except ValueError as exc:
            if attempt < 2:
                logger.warning("Generated payload was invalid (attempt %d), retrying: %s", attempt + 1, exc)
                continue
            logger.exception("Parse failed: %s", exc)
            logger.warning("Falling back to local pairs after invalid generated payload")
            return _fallback_pairs(keyword)
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt < 2:
                logger.warning("Generated JSON could not be parsed (attempt %d), retrying: %s", attempt + 1, exc)
                continue
            logger.exception("Parse failed: %s", exc)
            logger.warning("Falling back to local pairs after generated JSON parse failure")
            return _fallback_pairs(keyword)

    raise HTTPException(status_code=502, detail="题目生成失败，请稍后重试")


def shuffle_items(items: list[T]) -> list[T]:
    copied = items[:]
    random.shuffle(copied)
    return copied
