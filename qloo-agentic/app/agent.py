"""Taste-aware OmniPulse planner: entity resolution -> Qloo insights -> experience plan."""
from __future__ import annotations
from typing import Any
from .qloo_client import QlooClient, QlooAPIError

OCCASION_SCENES = {
    "movie_night": {"label": "Cinema cocoon", "brightness": 22, "temperature": "warm", "music": "low-volume ambient"},
    "dinner_party": {"label": "Warm hosting", "brightness": 58, "temperature": "warm", "music": "social background"},
    "date_night": {"label": "Intimate lounge", "brightness": 30, "temperature": "warm", "music": "soft instrumental"},
    "weekend": {"label": "Relaxed weekend", "brightness": 48, "temperature": "neutral", "music": "easy listening"},
}

class TasteExperienceAgent:
    """Bounded tool-using agent that grounds cultural picks in Qloo."""
    def __init__(self, qloo: QlooClient):
        self.qloo = qloo

    async def resolve(self, interests: list[dict[str, str]]) -> dict[str, Any]:
        resolved, trace = [], []
        for interest in interests[:3]:
            query, kind = interest["query"].strip(), interest["type"]
            try:
                candidates = await self.qloo.search_entities(query, kind, take=8)
                resolved.append({"query": query, "type": kind, "candidates": candidates})
                trace.append({"step": "Resolve cultural reference", "tool": "Qloo /search",
                              "input": query, "status": "ok" if candidates else "empty",
                              "result_count": len(candidates)})
            except QlooAPIError as exc:
                trace.append({"step": "Resolve cultural reference", "tool": "Qloo /search",
                              "input": query, "status": "error", "message": str(exc)})
                raise
        return {"resolved": resolved, "trace": trace}

    async def plan(self, selected_signals: list[dict[str, str]],
                   city: str, occasion: str) -> dict[str, Any]:
        signal_ids = list(dict.fromkeys(
            x["entity_id"].strip() for x in selected_signals if x.get("entity_id")
        ))[:3]
        if not signal_ids:
            raise QlooAPIError("Select at least one confirmed Qloo entity before generating a plan.")
        if occasion not in OCCASION_SCENES:
            raise QlooAPIError("Choose a supported occasion.")
        trace: list[dict[str, Any]] = [{
            "step": "Load confirmed taste signals", "tool": "OmniPulse session context",
            "status": "ok", "result_count": len(signal_ids),
            "detail": "Only entity IDs selected for this session are used; no profile is stored.",
        }]
        recommendations: dict[str, list[dict[str, Any]]] = {"places": [], "movies": [], "music": []}
        tasks = [("places", "place", city.strip()), ("movies", "movie", ""), ("music", "artist", "")]
        errors = []
        for key, kind, location in tasks:
            try:
                candidates = await self.qloo.recommend(kind, signal_ids, city=location or None, take=6)
                recommendations[key] = candidates
                trace.append({
                    "step": f"Find taste-aligned {key}", "tool": "Qloo /v2/insights",
                    "status": "ok" if candidates else "empty", "result_count": len(candidates),
                    "detail": f"Target category: {kind}" + (f" · Location: {location}" if location else ""),
                })
            except QlooAPIError as exc:
                errors.append(f"{key}: {exc}")
                trace.append({"step": f"Find taste-aligned {key}", "tool": "Qloo /v2/insights",
                              "status": "error", "message": str(exc)})
        if not any(recommendations.values()):
            raise QlooAPIError("Qloo did not return recommendations. " +
                               " | ".join(errors or ["Try different cultural references or a broader city name."]))
        trace.append({
            "step": "Compose the experience", "tool": "OmniPulse experience orchestrator",
            "status": "ok", "result_count": sum(len(v) for v in recommendations.values()),
            "detail": "Combines Qloo affinity-ranked candidates with the selected occasion's ambient scene preview.",
        })
        return {
            "title": f"Your {occasion.replace('_', ' ')} in {city.strip()}",
            "occasion": occasion, "city": city.strip(),
            "recommendations": recommendations, "scene": OCCASION_SCENES[occasion],
            "trace": trace, "warnings": errors,
            "provenance": "Cultural recommendations are returned by Qloo's Taste Graph. The ambient scene is an OmniPulse preset based on the occasion, not a Qloo prediction.",
            "privacy": "This request is processed for this session only. Taste signals are not saved by this Qloo edition.",
        }
