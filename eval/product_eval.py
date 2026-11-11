"""Deterministic offline evaluation for the travel-agent product layer.

No LLM, MCP server, transport provider, API key, or network connection is
used.  The suite checks whether a request is safe to show for confirmation,
should fall back for clarification, or contains invalid user constraints.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from MCP.skills import parse_query
from product.confirmation import UserPreferences, build_search_plan


DEFAULT_CASES = Path(__file__).with_name("product_cases.json")


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    category: str
    passed: bool
    expected_action: str
    actual_action: str
    detail: str = ""


def _evaluate_route(case: dict[str, Any]) -> CaseResult:
    expected = case["expected"]
    parsed = parse_query(case["query"])
    actual_action = "confirm" if parsed is not None else "fallback"
    errors: list[str] = []

    if actual_action != expected["action"]:
        errors.append(f"action={actual_action!r}")
    if parsed is not None:
        plan = build_search_plan(case["query"], parsed)
        actual = {
            "mode": parsed["mode"],
            "from": plan.origin,
            "to": plan.destination,
        }
        for field in ("mode", "from", "to"):
            if field in expected and actual[field] != expected[field]:
                errors.append(f"{field}={actual[field]!r}")

    return CaseResult(
        case_id=case["id"],
        category=case["category"],
        passed=not errors,
        expected_action=expected["action"],
        actual_action=actual_action,
        detail=", ".join(errors),
    )


def _evaluate_preferences(case: dict[str, Any]) -> CaseResult:
    expected_action = case["expected"]["action"]
    try:
        UserPreferences(**case["preferences"])
        actual_action = "accepted"
    except (TypeError, ValueError):
        actual_action = "rejected"
    passed = actual_action == expected_action
    return CaseResult(
        case_id=case["id"],
        category=case["category"],
        passed=passed,
        expected_action=expected_action,
        actual_action=actual_action,
        detail="" if passed else f"action={actual_action!r}",
    )


def evaluate_cases(cases: list[dict[str, Any]]) -> list[CaseResult]:
    """Evaluate all cases and return structured results."""

    results = []
    for case in cases:
        if "preferences" in case:
            results.append(_evaluate_preferences(case))
        else:
            results.append(_evaluate_route(case))
    return results


def build_summary(results: list[CaseResult]) -> dict[str, Any]:
    passed = sum(result.passed for result in results)
    category_total = Counter(result.category for result in results)
    category_passed = Counter(result.category for result in results if result.passed)
    false_confirmations = sum(
        result.expected_action == "fallback" and result.actual_action == "confirm"
        for result in results
    )
    missed_confirmations = sum(
        result.expected_action == "confirm" and result.actual_action == "fallback"
        for result in results
    )
    return {
        "total": len(results),
        "passed": passed,
        "pass_rate": round(100 * passed / len(results), 1) if results else 0.0,
        "false_confirmations": false_confirmations,
        "missed_confirmations": missed_confirmations,
        "categories": {
            category: {
                "passed": category_passed[category],
                "total": total,
            }
            for category, total in sorted(category_total.items())
        },
    }


def load_cases(path: Path = DEFAULT_CASES) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    args = parser.parse_args()

    results = evaluate_cases(load_cases(args.cases))
    summary = build_summary(results)
    if args.json:
        print(json.dumps({"summary": summary, "results": [asdict(r) for r in results]}, indent=2))
    else:
        for result in results:
            marker = "PASS" if result.passed else "FAIL"
            detail = f" ({result.detail})" if result.detail else ""
            print(f"[{marker}] {result.case_id}{detail}")
        print(
            f"\n{summary['passed']}/{summary['total']} passed "
            f"({summary['pass_rate']:.1f}%) | "
            f"false confirmations: {summary['false_confirmations']} | "
            f"missed confirmations: {summary['missed_confirmations']}"
        )
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
