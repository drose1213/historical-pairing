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


PROMPT = """你是一个严谨的历史知识出题助手。

请根据用户输入的关键词生成 4 组历史配对题。

关键词：{keyword}

要求：
1. 只生成与关键词强相关的历史内容。
2. 每组包含 left、right、explanation、type。
3. left 和 right 必须可以明确一一配对。
4. 不要生成有争议或模糊答案。
5. left 不超过 20 个汉字，right 不超过 32 个汉字。
6. explanation 控制在 80 字以内。
7. 如果关键词不是历史相关内容，仍尝试从历史角度解释；完全无关时返回与“历史学习”相关的基础配对。
8. 返回严格 JSON，不要输出 Markdown。

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
        GeneratedPair(left=f"{cleaned}背景", right="理解时代条件", explanation=f"学习 {cleaned} 时，先看政治、经济、文化等时代条件。", type="概念-方法"),
        GeneratedPair(left=f"{cleaned}人物", right="梳理关键行动", explanation=f"围绕 {cleaned} 的人物，可以用行动和影响建立配对。", type="人物-方法"),
        GeneratedPair(left=f"{cleaned}事件", right="判断因果关系", explanation=f"历史事件常通过原因、经过和结果来理解。", type="事件-方法"),
        GeneratedPair(left=f"{cleaned}影响", right="比较长期变化", explanation=f"历史影响可从制度、社会、经济和文化角度比较。", type="影响-方法"),
    ]


def _dedupe_and_validate(pairs: list[GeneratedPair]) -> list[GeneratedPair]:
    seen_left: set[str] = set()
    seen_right: set[str] = set()
    cleaned: list[GeneratedPair] = []

    for pair in pairs:
        left = pair.left.strip()
        right = pair.right.strip()
        if not left or not right or left in seen_left or right in seen_right:
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

    if len(cleaned) != 4:
        raise ValueError("generated pairs must contain exactly 4 unique pairs")
    return cleaned


def _extract_json_payload(content: str) -> dict:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("empty response content")

    # Remove reasoning blocks returned by some compatible providers such as MiniMax.
    cleaned = re.sub(r"<think>.*?</think>\s*", "", cleaned, flags=re.DOTALL).strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])


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
    try:
        request_kwargs = {
            "model": model or settings.openai_model,
            "messages": [
                {"role": "system", "content": "你只输出符合要求的 JSON。"},
                {"role": "user", "content": PROMPT.format(keyword=keyword.strip())},
            ],
            "temperature": 0.4,
            "timeout": 30,
        }
        # Only add response_format for OpenAI, not for compatible APIs like MiniMax
        if not effective_base_url or effective_base_url.lower().rstrip("/") == "https://api.openai.com/v1":
            request_kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**request_kwargs)
    except Exception as exc:
        logger.exception("API call failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=f"API 调用失败: {type(exc).__name__}: {exc}") from exc

    content = response.choices[0].message.content or ""
    try:
        payload = _extract_json_payload(content)
        parsed = GeneratedPairs.model_validate(payload)
        return _dedupe_and_validate(parsed.pairs)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        logger.exception("Parse failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"题目生成失败：{exc}") from exc


def shuffle_items(items: list[T]) -> list[T]:
    copied = items[:]
    random.shuffle(copied)
    return copied
