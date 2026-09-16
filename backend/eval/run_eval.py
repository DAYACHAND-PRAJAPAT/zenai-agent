"""
eval/run_eval.py
Automated evaluation of the ZenAI Agent's core capabilities, per the assignment's
Key Evaluation Criteria (section 10):
  - Accuracy of keyword/topic detection
  - Effectiveness of environment/sustainability boundary setting
  - Handling of out-of-scope requests

Run with: python eval/run_eval.py  (from the backend/ directory)
Exits with code 1 if accuracy drops below the threshold, so this can also run in CI.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # allow importing sibling modules
from scope_classifier import classify_scope

ACCURACY_THRESHOLD = 0.85
TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"


def run_scope_detection_eval() -> dict:
    with open(TEST_CASES_PATH, "r") as f:
        test_cases = json.load(f)

    results = []
    correct = 0

    for case in test_cases:
        result = classify_scope(case["request"])
        # Only trust the pure keyword-match result here (no live LLM fallback in CI —
        # keeps this test free, fast, and deterministic).
        predicted = result.in_scope if result.confidence != "low" else False
        is_correct = predicted == case["expected_in_scope"]
        correct += is_correct

        results.append({
            "request": case["request"],
            "expected": case["expected_in_scope"],
            "predicted": predicted,
            "correct": is_correct,
            "matched_keywords": result.matched_keywords,
        })

    accuracy = correct / len(test_cases) if test_cases else 0
    return {"accuracy": accuracy, "total": len(test_cases), "correct": correct, "results": results}


def main():
    print("Running ZenAI Agent evaluation suite...\n")
    report = run_scope_detection_eval()

    print(f"Scope Detection Accuracy: {report['accuracy']:.1%} ({report['correct']}/{report['total']})\n")

    for r in report["results"]:
        mark = "PASS" if r["correct"] else "FAIL"
        print(f"[{mark}] expected={r['expected']!s:5} predicted={r['predicted']!s:5} | {r['request']}")

    print()
    if report["accuracy"] < ACCURACY_THRESHOLD:
        print(f"FAILED: accuracy {report['accuracy']:.1%} is below threshold {ACCURACY_THRESHOLD:.0%}")
        sys.exit(1)
    else:
        print(f"PASSED: accuracy {report['accuracy']:.1%} meets threshold {ACCURACY_THRESHOLD:.0%}")
        sys.exit(0)


if __name__ == "__main__":
    main()
