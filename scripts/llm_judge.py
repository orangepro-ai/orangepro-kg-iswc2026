"""
Blinded matched-pair judge service.

Provides a provider-agnostic Stage 3 judging foundation that compares baseline
and KG-generated test cases without revealing which side is KG to the provider.
"""

from __future__ import annotations

import asyncio
import json
import hashlib
import os
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Protocol

import structlog

from app.models.nodes import (
    JudgeAggregateSummary,
    JudgeOptionSide,
    JudgePairRequestItem,
    JudgePairRunResponse,
    JudgePairVerdict,
    JudgeProvider,
    JudgeRubricScores,
    JudgeTestOption,
    JudgeWinner,
)
from app.services.database import Neo4jService, get_db

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)?", re.IGNORECASE)
_ACTION_TOKENS = {"verify", "assert", "ensure", "confirm", "validate", "check"}
_BUG_TOKENS = {"error", "fail", "timeout", "regression", "drift", "stale", "mismatch", "invalid"}
_TRACE_TOKENS = {"incident", "audit", "trace", "evidence", "service", "file", "endpoint", "fx_lock_id"}
_APPROX_COST_PER_CALL_USD = {
    JudgeProvider.DETERMINISTIC: 0.0,
    JudgeProvider.OPENAI: 0.003,
    JudgeProvider.ANTHROPIC: 0.0015,
}

logger = structlog.get_logger()


@dataclass
class ProviderJudgeResult:
    winner: JudgeWinner
    confidence: float
    scores: JudgeRubricScores
    rationale_short: str
    flags: list[str]
    raw_prompt_system: str
    raw_prompt_user: str
    raw_response_content: str
    provider_fingerprint: str = ""
    provider_seed: Optional[int] = None


class PairJudgeProvider(Protocol):
    async def judge_pair(
        self,
        *,
        model: str | None,
        system_prompt: str,
        user_prompt: str,
        packet_title: str,
        story_text: str,
        acceptance_criteria: list[str],
        bucket_name: str,
        option_a_title: str,
        option_a_body: str,
        option_b_title: str,
        option_b_body: str,
    ) -> ProviderJudgeResult:
        ...


class DeterministicPairJudgeProvider:
    async def judge_pair(
        self,
        *,
        model: str | None,
        system_prompt: str,
        user_prompt: str,
        packet_title: str,
        story_text: str,
        acceptance_criteria: list[str],
        bucket_name: str,
        option_a_title: str,
        option_a_body: str,
        option_b_title: str,
        option_b_body: str,
    ) -> ProviderJudgeResult:
        story_tokens = _tokens(" ".join([packet_title, story_text, bucket_name] + acceptance_criteria))
        score_a = self._score_option(option_a_title, option_a_body, story_tokens)
        score_b = self._score_option(option_b_title, option_b_body, story_tokens)

        total_a = _weighted_total(score_a)
        total_b = _weighted_total(score_b)
        margin = abs(total_a - total_b)

        if margin < 0.05:
            winner = JudgeWinner.TIE
        elif total_a > total_b:
            winner = JudgeWinner.A
        else:
            winner = JudgeWinner.B

        confidence = min(0.99, max(0.45, 0.55 + margin))
        rationale = _build_rationale(winner, score_a, score_b)
        flags = _build_flags(option_a_body if winner == JudgeWinner.B else option_b_body)
        selected_scores = score_a if winner != JudgeWinner.B else score_b
        if winner == JudgeWinner.TIE:
            selected_scores = JudgeRubricScores(
                bucket_fit=round((score_a.bucket_fit + score_b.bucket_fit) / 2, 4),
                story_relevance=round((score_a.story_relevance + score_b.story_relevance) / 2, 4),
                actionability=round((score_a.actionability + score_b.actionability) / 2, 4),
                specificity=round((score_a.specificity + score_b.specificity) / 2, 4),
                adversarial_depth=round((score_a.adversarial_depth + score_b.adversarial_depth) / 2, 4),
                traceability_or_evidence=round(
                    (score_a.traceability_or_evidence + score_b.traceability_or_evidence) / 2, 4
                ),
            )
        return ProviderJudgeResult(
            winner=winner,
            confidence=round(confidence, 4),
            scores=selected_scores,
            rationale_short=rationale,
            flags=flags,
            raw_prompt_system=system_prompt,
            raw_prompt_user=user_prompt,
            raw_response_content=json.dumps(
                {
                    "winner": winner.value,
                    "confidence": round(confidence, 4),
                    "scores": selected_scores.model_dump(),
                    "rationale_short": rationale,
                    "flags": flags,
                },
                sort_keys=True,
            ),
            provider_fingerprint="deterministic-rubric-v1",
            provider_seed=None,
        )

    def _score_option(self, title: str, body: str, story_tokens: set[str]) -> JudgeRubricScores:
        text = f"{title}\n{body}"
        option_tokens = _tokens(text)
        overlap = _overlap_ratio(story_tokens, option_tokens)
        actionability = min(1.0, _count_hits(option_tokens, _ACTION_TOKENS) * 0.22 + _has_expected_shape(body))
        specificity = min(1.0, _specificity_score(text))
        adversarial_depth = min(1.0, _count_hits(option_tokens, _BUG_TOKENS) * 0.24 + _edge_case_score(text))
        traceability = min(1.0, _count_hits(option_tokens, _TRACE_TOKENS) * 0.2 + _reference_score(text))
        bucket_fit = min(1.0, overlap * 0.75 + _bucket_keyword_score(text, story_tokens) * 0.25)
        story_relevance = min(1.0, overlap * 0.8 + _acceptance_criteria_shape(text) * 0.2)

        return JudgeRubricScores(
            bucket_fit=round(bucket_fit, 4),
            story_relevance=round(story_relevance, 4),
            actionability=round(actionability, 4),
            specificity=round(specificity, 4),
            adversarial_depth=round(adversarial_depth, 4),
            traceability_or_evidence=round(traceability, 4),
        )


class OpenAIPairJudgeProvider:
    DEFAULT_MODEL = "gpt-4o-mini"

    async def judge_pair(
        self,
        *,
        model: str | None,
        system_prompt: str,
        user_prompt: str,
        packet_title: str,
        story_text: str,
        acceptance_criteria: list[str],
        bucket_name: str,
        option_a_title: str,
        option_a_body: str,
        option_b_title: str,
        option_b_body: str,
    ) -> ProviderJudgeResult:
        resolved_model = model or os.environ.get("OPENAI_JUDGE_MODEL") or os.environ.get("OPENAI_MODEL") or self.DEFAULT_MODEL
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set for judge provider")
        seed = _resolve_openai_seed()
        response_payload = await asyncio.to_thread(
            self._request_completion,
            api_key,
            os.environ.get("OPENAI_BASE_URL"),
            resolved_model,
            system_prompt,
            user_prompt,
            seed,
        )
        verdict = _parse_provider_verdict(response_payload["content"])
        verdict.raw_prompt_system = system_prompt
        verdict.raw_prompt_user = user_prompt
        verdict.raw_response_content = response_payload["content"]
        verdict.provider_fingerprint = response_payload.get("fingerprint", "") or ""
        verdict.provider_seed = seed
        return verdict

    def _request_completion(
        self,
        api_key: str,
        base_url: str | None,
        model: str,
        system_prompt: str,
        user_prompt: str,
        seed: int,
    ) -> dict[str, str]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package not installed for judge provider") from exc

        client_kwargs = {"api_key": api_key, "timeout": 45.0}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            seed=seed,
            response_format={"type": "json_object"},
        )
        return {
            "content": response.choices[0].message.content or "{}",
            "fingerprint": getattr(response, "system_fingerprint", "") or "",
        }


class AnthropicPairJudgeProvider:
    DEFAULT_MODEL = "claude-3-5-haiku-latest"

    async def judge_pair(
        self,
        *,
        model: str | None,
        system_prompt: str,
        user_prompt: str,
        packet_title: str,
        story_text: str,
        acceptance_criteria: list[str],
        bucket_name: str,
        option_a_title: str,
        option_a_body: str,
        option_b_title: str,
        option_b_body: str,
    ) -> ProviderJudgeResult:
        resolved_model = model or os.environ.get("ANTHROPIC_JUDGE_MODEL") or self.DEFAULT_MODEL
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set for judge provider")
        content = await asyncio.to_thread(
            self._request_completion,
            api_key,
            os.environ.get("ANTHROPIC_BASE_URL"),
            resolved_model,
            system_prompt,
            user_prompt,
        )
        verdict = _parse_provider_verdict(content)
        verdict.raw_prompt_system = system_prompt
        verdict.raw_prompt_user = user_prompt
        verdict.raw_response_content = content
        verdict.provider_fingerprint = resolved_model
        verdict.provider_seed = None
        return verdict

    def _request_completion(
        self,
        api_key: str,
        base_url: str | None,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package not installed for judge provider") from exc

        client_kwargs = {"api_key": api_key, "timeout": 45.0}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = Anthropic(**client_kwargs)
        response = client.messages.create(
            model=model,
            max_tokens=800,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text_blocks = [block.text for block in getattr(response, "content", []) if getattr(block, "type", "") == "text"]
        return "\n".join(text_blocks).strip() or "{}"


class LlmJudgeService:
    def __init__(
        self,
        db: Optional[Neo4jService] = None,
        provider_registry: Optional[dict[JudgeProvider, PairJudgeProvider]] = None,
    ):
        self.db = db or get_db()
        self.provider_registry = provider_registry or {
            JudgeProvider.DETERMINISTIC: DeterministicPairJudgeProvider(),
            JudgeProvider.OPENAI: OpenAIPairJudgeProvider(),
            JudgeProvider.ANTHROPIC: AnthropicPairJudgeProvider(),
        }

    async def judge_pairs(
        self,
        tenant_id: str,
        pairs: list[JudgePairRequestItem],
        provider: JudgeProvider = JudgeProvider.DETERMINISTIC,
        model: str | None = None,
        run_id: str | None = None,
        notes: str | None = None,
        max_pairs_per_run: int | None = None,
    ) -> JudgePairRunResponse:
        if not pairs:
            raise ValueError("At least one matched testcase pair is required")

        judge_provider = self.provider_registry.get(provider)
        if judge_provider is None:
            raise NotImplementedError(f"Judge provider '{provider.value}' is not configured")
        resolved_model = self._resolve_model(provider, model)
        resolved_max_pairs = self._resolve_max_pairs_per_run(max_pairs_per_run)
        if len(pairs) > resolved_max_pairs:
            raise ValueError(
                f"Judge run exceeds max_pairs_per_run ({len(pairs)} > {resolved_max_pairs})"
            )

        now = datetime.now(timezone.utc).isoformat()
        judge_run_uid = run_id or f"judge-run-{uuid.uuid4()}"
        run_node = await self.db.create_judge_run(
            {
                "uid": judge_run_uid,
                "tenant_id": tenant_id,
                "provider": provider.value,
                "model": resolved_model,
                "notes": notes or "",
                "pair_count": len(pairs),
                "max_pairs_per_run": resolved_max_pairs,
                "created_at": now,
                "created_from": "llm_judge",
                "ingestion_channel": "system_judged",
                "source_priority": 2,
            }
        )

        pair_verdicts: list[JudgePairVerdict] = []
        bucket_rollup: dict[str, list[JudgePairVerdict]] = defaultdict(list)
        story_rollup: dict[str, list[JudgePairVerdict]] = defaultdict(list)

        for index, pair in enumerate(pairs, start=1):
            pair_uid = pair.pair_uid or self._pair_uid(pair, index)
            kg_side = self._kg_side(pair_uid)
            option_a, option_b = self._blind_options(pair, kg_side)
            system_prompt, user_prompt = _build_judge_prompts(
                packet_title=pair.packet_title,
                story_text=pair.story_text,
                acceptance_criteria=pair.acceptance_criteria,
                bucket_name=pair.bucket_name,
                option_a_title=option_a.title,
                option_a_body=option_a.body,
                option_b_title=option_b.title,
                option_b_body=option_b.body,
            )

            judgment = await judge_provider.judge_pair(
                model=resolved_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                packet_title=pair.packet_title,
                story_text=pair.story_text,
                acceptance_criteria=pair.acceptance_criteria,
                bucket_name=pair.bucket_name,
                option_a_title=option_a.title,
                option_a_body=option_a.body,
                option_b_title=option_b.title,
                option_b_body=option_b.body,
            )
            low_confidence = judgment.confidence < 0.6
            kg_won = judgment.winner != JudgeWinner.TIE and judgment.winner.value == kg_side.value

            verdict_uid = f"judge-verdict-{uuid.uuid4()}"
            verdict_node = await self.db.create_judge_pair_verdict(
                {
                    "uid": verdict_uid,
                    "tenant_id": tenant_id,
                    "judge_run_uid": run_node["uid"],
                    "pair_uid": pair_uid,
                    "packet_title": pair.packet_title,
                    "story_key": pair.story_key or "",
                    "bucket_name": pair.bucket_name,
                    "winner": judgment.winner.value,
                    "kg_side": kg_side.value,
                    "kg_won": kg_won,
                    "confidence": judgment.confidence,
                    "low_confidence": low_confidence,
                    "rationale_short": judgment.rationale_short,
                    "flags": judgment.flags,
                    "scores": judgment.scores.model_dump(),
                    "provider_fingerprint": judgment.provider_fingerprint,
                    "provider_seed": judgment.provider_seed,
                    "raw_prompt_system": judgment.raw_prompt_system,
                    "raw_prompt_user": judgment.raw_prompt_user,
                    "raw_response_content": judgment.raw_response_content,
                    "created_at": now,
                    "created_from": "llm_judge",
                    "ingestion_channel": "system_judged",
                    "source_priority": 2,
                }
            )
            await self.db.save_judge_run_link(
                judge_run_uid=run_node["uid"],
                verdict_uid=verdict_node["uid"],
                tenant_id=tenant_id,
                props={"created_at": now, "method": "blinded_pair_judge"},
            )

            if pair.baseline_test.generation_uid:
                await self._assert_generation_belongs_to_tenant(tenant_id, pair.baseline_test.generation_uid)
                await self.db.save_judge_generation_link(
                    verdict_uid=verdict_node["uid"],
                    generation_uid=pair.baseline_test.generation_uid,
                    tenant_id=tenant_id,
                    rel_type="EVALUATES_BASELINE",
                    props={"created_at": now, "method": "blinded_pair_judge"},
                )
            if pair.kg_test.generation_uid:
                await self._assert_generation_belongs_to_tenant(tenant_id, pair.kg_test.generation_uid)
                await self.db.save_judge_generation_link(
                    verdict_uid=verdict_node["uid"],
                    generation_uid=pair.kg_test.generation_uid,
                    tenant_id=tenant_id,
                    rel_type="EVALUATES_KG",
                    props={"created_at": now, "method": "blinded_pair_judge"},
                )

            verdict = JudgePairVerdict(
                pair_uid=pair_uid,
                bucket_name=pair.bucket_name,
                story_key=pair.story_key,
                winner=judgment.winner,
                kg_side=kg_side,
                kg_won=kg_won,
                confidence=judgment.confidence,
                low_confidence=low_confidence,
                scores=judgment.scores,
                rationale_short=judgment.rationale_short,
                flags=judgment.flags,
            )
            pair_verdicts.append(verdict)
            bucket_rollup[pair.bucket_name].append(verdict)
            story_rollup[pair.story_key or pair.packet_title].append(verdict)

        approx_cost_usd = self._estimate_run_cost(provider, len(pair_verdicts))
        logger.info(
            "judge_run_completed",
            judge_run_uid=run_node["uid"],
            tenant_id=tenant_id,
            provider=provider.value,
            model=resolved_model,
            pairs=len(pair_verdicts),
            max_pairs_per_run=resolved_max_pairs,
            approx_cost_usd=approx_cost_usd,
        )

        return JudgePairRunResponse(
            tenant_id=tenant_id,
            judge_run_uid=run_node["uid"],
            provider=provider,
            model=resolved_model or None,
            judged_pairs=len(pair_verdicts),
            kg_win_rate=_safe_rate(sum(1 for verdict in pair_verdicts if verdict.kg_won), len(pair_verdicts)),
            tie_rate=_safe_rate(sum(1 for verdict in pair_verdicts if verdict.winner == JudgeWinner.TIE), len(pair_verdicts)),
            low_confidence_pairs=sum(1 for verdict in pair_verdicts if verdict.low_confidence),
            pair_verdicts=pair_verdicts,
            bucket_summaries=self._build_rollup(bucket_rollup),
            story_summaries=self._build_rollup(story_rollup),
        )

    def _resolve_model(self, provider: JudgeProvider, requested_model: str | None) -> str:
        if requested_model:
            return requested_model
        if provider == JudgeProvider.OPENAI:
            return os.environ.get("OPENAI_JUDGE_MODEL") or os.environ.get("OPENAI_MODEL") or OpenAIPairJudgeProvider.DEFAULT_MODEL
        if provider == JudgeProvider.ANTHROPIC:
            return os.environ.get("ANTHROPIC_JUDGE_MODEL") or AnthropicPairJudgeProvider.DEFAULT_MODEL
        return "deterministic-rubric-v1"

    def _resolve_max_pairs_per_run(self, requested_max_pairs: int | None) -> int:
        if requested_max_pairs is not None:
            return requested_max_pairs
        raw = os.environ.get("JUDGE_MAX_PAIRS_PER_RUN", "100")
        try:
            value = int(raw)
        except ValueError as exc:
            raise RuntimeError("JUDGE_MAX_PAIRS_PER_RUN must be an integer") from exc
        if value < 1:
            raise RuntimeError("JUDGE_MAX_PAIRS_PER_RUN must be >= 1")
        return value

    def _estimate_run_cost(self, provider: JudgeProvider, pair_count: int) -> float:
        return round(_APPROX_COST_PER_CALL_USD.get(provider, 0.0) * pair_count, 4)

    async def _assert_generation_belongs_to_tenant(self, tenant_id: str, generation_uid: str) -> None:
        generation = await self.db.get_generation_run(generation_uid, tenant_id)
        if generation is None:
            raise ValueError(f"Generation run '{generation_uid}' not found for tenant")

    def _pair_uid(self, pair: JudgePairRequestItem, index: int) -> str:
        raw = "::".join([pair.packet_title, pair.bucket_name, pair.story_text, str(index)]).encode("utf-8")
        return f"judge-pair-{hashlib.sha256(raw).hexdigest()[:16]}"

    def _kg_side(self, pair_uid: str) -> JudgeOptionSide:
        return JudgeOptionSide.A if int(hashlib.sha256(pair_uid.encode("utf-8")).hexdigest(), 16) % 2 == 0 else JudgeOptionSide.B

    def _blind_options(self, pair: JudgePairRequestItem, kg_side: JudgeOptionSide) -> tuple[JudgeTestOption, JudgeTestOption]:
        if kg_side == JudgeOptionSide.A:
            return pair.kg_test, pair.baseline_test
        return pair.baseline_test, pair.kg_test

    def _build_rollup(self, grouped: dict[str, list[JudgePairVerdict]]) -> list[JudgeAggregateSummary]:
        rows: list[JudgeAggregateSummary] = []
        for name, verdicts in grouped.items():
            total = len(verdicts)
            rows.append(
                JudgeAggregateSummary(
                    name=name,
                    total_pairs=total,
                    kg_win_rate=_safe_rate(sum(1 for verdict in verdicts if verdict.kg_won), total),
                    tie_rate=_safe_rate(sum(1 for verdict in verdicts if verdict.winner == JudgeWinner.TIE), total),
                    low_confidence_rate=_safe_rate(sum(1 for verdict in verdicts if verdict.low_confidence), total),
                )
            )
        rows.sort(key=lambda item: (-item.total_pairs, item.name.lower()))
        return rows


def _tokens(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_RE.finditer(text or "")}


def _build_judge_prompts(
    *,
    packet_title: str,
    story_text: str,
    acceptance_criteria: list[str],
    bucket_name: str,
    option_a_title: str,
    option_a_body: str,
    option_b_title: str,
    option_b_body: str,
) -> tuple[str, str]:
    system_prompt = (
        "You are a blinded software test judge. Compare Option A and Option B without assuming either side is preferred. "
        "Return only strict JSON with keys: winner, confidence, scores, rationale_short, flags. "
        "winner must be one of A, B, tie. confidence must be 0.0-1.0. "
        "scores must include bucket_fit, story_relevance, actionability, specificity, adversarial_depth, traceability_or_evidence."
    )
    criteria_text = "\n".join(f"- {item}" for item in acceptance_criteria) or "- none supplied"
    user_prompt = f"""Judge which testcase is better for this story and bucket.

Packet title:
{packet_title}

Bucket:
{bucket_name}

Story:
{story_text}

Acceptance criteria:
{criteria_text}

Option A title:
{option_a_title}

Option A body:
{option_a_body}

Option B title:
{option_b_title}

Option B body:
{option_b_body}

Return JSON only.
"""
    return system_prompt, user_prompt


def _parse_provider_verdict(content: str) -> ProviderJudgeResult:
    payload = _load_json_object(content)
    try:
        winner = JudgeWinner(payload.get("winner", "tie"))
    except ValueError as exc:
        raise ValueError(f"Invalid judge winner: {payload.get('winner')}") from exc

    confidence = payload.get("confidence", 0.0)
    if not isinstance(confidence, (int, float)):
        raise ValueError("Judge confidence must be numeric")
    confidence_value = round(float(confidence), 4)
    if confidence_value < 0.0 or confidence_value > 1.0:
        raise ValueError("Judge confidence must be between 0.0 and 1.0")

    scores_payload = payload.get("scores")
    if not isinstance(scores_payload, dict):
        raise ValueError("Judge scores must be a JSON object")
    scores = JudgeRubricScores(**scores_payload)

    rationale = str(payload.get("rationale_short") or "").strip()
    flags_raw = payload.get("flags") or []
    if not isinstance(flags_raw, list):
        raise ValueError("Judge flags must be a JSON array")
    flags = [str(flag).strip() for flag in flags_raw if str(flag).strip()]

    return ProviderJudgeResult(
        winner=winner,
        confidence=confidence_value,
        scores=scores,
        rationale_short=rationale,
        flags=flags,
        raw_prompt_system="",
        raw_prompt_user="",
        raw_response_content=content,
    )


def _load_json_object(content: str) -> dict:
    cleaned = (content or "").strip()
    if cleaned.startswith("```"):
        lines = [line for line in cleaned.splitlines() if not line.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    payload = json.loads(cleaned or "{}")
    if not isinstance(payload, dict):
        raise ValueError("Judge response must be a JSON object")
    return payload


def _resolve_openai_seed() -> int:
    raw = os.environ.get("OPENAI_JUDGE_SEED", "42")
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError("OPENAI_JUDGE_SEED must be an integer") from exc


def _overlap_ratio(left: set[str], right: set[str]) -> float:
    if not left:
        return 0.0
    return len(left & right) / len(left)


def _count_hits(tokens: set[str], vocabulary: set[str]) -> float:
    return float(len(tokens & vocabulary))


def _has_expected_shape(text: str) -> float:
    lowered = text.lower()
    return 0.2 if any(marker in lowered for marker in ("should", "expected", "must", "returns")) else 0.0


def _specificity_score(text: str) -> float:
    tokens = _tokens(text)
    signal = sum(1 for token in tokens if any(char.isdigit() for char in token))
    signal += sum(1 for token in tokens if "-" in token or "_" in token)
    signal += sum(1 for token in tokens if token in {"cop", "usd", "pen", "fx", "rounding", "shipping"})
    return min(1.0, signal * 0.16)


def _edge_case_score(text: str) -> float:
    lowered = text.lower()
    signal = 0.0
    if "while" in lowered:
        signal += 0.15
    if any(marker in lowered for marker in ("instead of", "after", "before", "without")):
        signal += 0.2
    return min(1.0, signal)


def _reference_score(text: str) -> float:
    tokens = _tokens(text)
    signal = sum(1 for token in tokens if token in {"fx_lock_id", "checkout-service", "shipping-service", "incident"})
    return min(1.0, signal * 0.18)


def _bucket_keyword_score(text: str, story_tokens: set[str]) -> float:
    tokens = _tokens(text)
    bucket_terms = {"functional", "integration", "security", "performance", "traceability", "edge", "cases"}
    return _overlap_ratio((story_tokens & bucket_terms) | (tokens & bucket_terms), tokens)


def _acceptance_criteria_shape(text: str) -> float:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return min(1.0, len(lines) * 0.08)


def _weighted_total(scores: JudgeRubricScores) -> float:
    return (
        scores.bucket_fit * 0.22
        + scores.story_relevance * 0.22
        + scores.actionability * 0.16
        + scores.specificity * 0.16
        + scores.adversarial_depth * 0.14
        + scores.traceability_or_evidence * 0.10
    )


def _build_rationale(winner: JudgeWinner, score_a: JudgeRubricScores, score_b: JudgeRubricScores) -> str:
    if winner == JudgeWinner.TIE:
        return "Both options are similarly grounded against the story and bucket."
    winning = score_a if winner == JudgeWinner.A else score_b
    losing = score_b if winner == JudgeWinner.A else score_a
    if winning.specificity > losing.specificity and winning.traceability_or_evidence >= losing.traceability_or_evidence:
        return "Winner is more specific and better anchored in concrete system evidence."
    if winning.adversarial_depth > losing.adversarial_depth:
        return "Winner covers stronger failure-oriented and adversarial cases for this bucket."
    return "Winner is better aligned with the story and bucket while remaining actionable."


def _build_flags(losing_body: str) -> list[str]:
    flags: list[str] = []
    lowered = losing_body.lower()
    if "todo" in lowered or "tbd" in lowered:
        flags.append("vague_expected_result")
    if len(lowered.split()) < 12:
        flags.append("underspecified")
    return flags


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)
