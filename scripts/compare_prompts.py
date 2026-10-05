
import os
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import MODELS, RESULTS_DIR, SCORE_WEIGHTS


# ============================================================
# LOAD RESULTS FILE
# ============================================================

def load_results(model_key, prompt_label):

    filename = f"{model_key}_{prompt_label}.json"

    filepath = os.path.join(
        RESULTS_DIR,
        filename
    )

    if not os.path.exists(filepath):
        return None

    with open(
        filepath,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# COMPUTE METRICS
# ============================================================

def compute_metrics(results):

    successful = [
        r for r in results
        if r.get("error", "") == ""
    ]

    if not successful:
        return None

    total = len(successful)

    avg_halluc = sum(
        r["hallucination_resistance"]
        for r in successful
    ) / total

    avg_honesty = sum(
        r["honesty"]
        for r in successful
    ) / total

    avg_latency = sum(
        r["latency_seconds"]
        for r in successful
    ) / total

    abstention_count = sum(
        r["abstained"]
        for r in successful
    )

    # Composite score (using hallucination + honesty only,
    # since factual accuracy requires manual review)

    composite = (
        avg_halluc
        * SCORE_WEIGHTS["hallucination_resistance"]
        + avg_honesty
        * SCORE_WEIGHTS["honesty"]
    ) / (
        SCORE_WEIGHTS["hallucination_resistance"]
        + SCORE_WEIGHTS["honesty"]
    )

    return {
        "total_cases": total,
        "avg_hallucination_resistance": round(
            avg_halluc, 2
        ),
        "avg_honesty": round(
            avg_honesty, 2
        ),
        "composite_score": round(
            composite, 2
        ),
        "avg_latency": round(
            avg_latency, 2
        ),
        "abstention_count": abstention_count,
    }


# ============================================================
# COMPARE ACROSS PROMPTS (SINGLE MODEL)
# ============================================================

def compare_prompts_for_model(model_key):

    prompt_labels = [
        "v1_basic",
        "v2_improved",
        "v3_strong",
        "v4_final",
    ]

    print(f"\n{'='*60}")
    print(
        f"MODEL: {MODELS[model_key]['name']} "
        f"({MODELS[model_key]['family']})"
    )
    print(f"{'='*60}")

    print(
        f"\n{'Prompt':<16} "
        f"{'Halluc':>8} "
        f"{'Honesty':>8} "
        f"{'Composite':>10} "
        f"{'Latency':>8} "
        f"{'Abstain':>8}"
    )

    print("-" * 62)

    for prompt_label in prompt_labels:

        results = load_results(
            model_key,
            prompt_label
        )

        if results is None:

            print(
                f"{prompt_label:<16} "
                f"{'(no data)'}"
            )
            continue

        metrics = compute_metrics(results)

        if metrics is None:

            print(
                f"{prompt_label:<16} "
                f"{'(no successful runs)'}"
            )
            continue

        print(
            f"{prompt_label:<16} "
            f"{metrics['avg_hallucination_resistance']:>7.2f} "
            f"{metrics['avg_honesty']:>7.2f} "
            f"{metrics['composite_score']:>9.2f} "
            f"{metrics['avg_latency']:>7.2f}s "
            f"{metrics['abstention_count']:>7}"
        )


# ============================================================
# COMPARE ACROSS MODELS (SINGLE PROMPT)
# ============================================================

def compare_models_for_prompt(prompt_label):

    print(f"\n{'='*60}")
    print(f"PROMPT: {prompt_label}")
    print(f"{'='*60}")

    print(
        f"\n{'Model':<20} "
        f"{'Halluc':>8} "
        f"{'Honesty':>8} "
        f"{'Composite':>10} "
        f"{'Latency':>8}"
    )

    print("-" * 58)

    for model_key in MODELS:

        results = load_results(
            model_key,
            prompt_label
        )

        if results is None:

            print(
                f"{MODELS[model_key]['name']:<20} "
                f"{'(no data)'}"
            )
            continue

        metrics = compute_metrics(results)

        if metrics is None:

            print(
                f"{MODELS[model_key]['name']:<20} "
                f"{'(no successful runs)'}"
            )
            continue

        print(
            f"{MODELS[model_key]['name']:<20} "
            f"{metrics['avg_hallucination_resistance']:>7.2f} "
            f"{metrics['avg_honesty']:>7.2f} "
            f"{metrics['composite_score']:>9.2f} "
            f"{metrics['avg_latency']:>7.2f}s"
        )


# ============================================================
# FIND BEST COMBINATION
# ============================================================

def find_best_combination():

    prompt_labels = [
        "v1_basic",
        "v2_improved",
        "v3_strong",
        "v4_final",
    ]

    best_score = -1
    best_model = ""
    best_prompt = ""

    for model_key in MODELS:

        for prompt_label in prompt_labels:

            results = load_results(
                model_key,
                prompt_label
            )

            if results is None:
                continue

            metrics = compute_metrics(results)

            if metrics is None:
                continue

            if metrics["composite_score"] > best_score:
                best_score = metrics[
                    "composite_score"
                ]
                best_model = model_key
                best_prompt = prompt_label

    if best_score >= 0:

        print(f"\n{'='*60}")
        print("BEST COMBINATION")
        print(f"{'='*60}")
        print(
            f"Model    : "
            f"{MODELS[best_model]['name']}"
        )
        print(f"Prompt   : {best_prompt}")
        print(f"Score    : {best_score:.2f} / 5")

    else:

        print(
            "\nNo results found. "
            "Run evaluation first."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PROMPT COMPARISON REPORT")
    print("=" * 60)

    # Compare prompts per model
    for model_key in MODELS:
        compare_prompts_for_model(model_key)

    # Compare models per prompt
    prompt_labels = [
        "v1_basic",
        "v2_improved",
        "v3_strong",
        "v4_final",
    ]

    for prompt_label in prompt_labels:
        compare_models_for_prompt(prompt_label)

    # Best combination
    find_best_combination()


if __name__ == "__main__":
    main()
