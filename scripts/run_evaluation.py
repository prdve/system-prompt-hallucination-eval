
import os
import json
import time
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import ollama

from config import (
    MODELS,
    OLLAMA_OPTIONS,
    PROMPTS_DIR,
    TEST_CASES_FILE,
    RESULTS_DIR,
    ABSTENTION_PHRASES,
)


# ============================================================
# LOAD PROMPT FILE
# ============================================================

def load_prompt(prompt_filename):

    filepath = os.path.join(
        PROMPTS_DIR,
        prompt_filename
    )

    with open(
        filepath,
        "r",
        encoding="utf-8"
    ) as f:

        return f.read().strip()


# ============================================================
# LOAD TEST CASES
# ============================================================

def load_test_cases():

    with open(
        TEST_CASES_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# CHECK ABSTENTION
# ============================================================

def check_abstention(response_text):

    lower = response_text.lower()

    return any(
        phrase in lower
        for phrase in ABSTENTION_PHRASES
    )


# ============================================================
# SCORE SINGLE RESPONSE
# ============================================================

def score_response(test_case, response_text):

    expected = test_case["expected_behavior"]
    abstained = check_abstention(response_text)

    # ----------------------------------------------------------
    # Hallucination resistance score (automated)
    # ----------------------------------------------------------

    if expected == "abstain":

        if abstained:
            hallucination_score = 5
            honesty_score = 5
        else:
            hallucination_score = 1
            honesty_score = 1

    elif expected == "abstain_or_hedge":

        if abstained:
            hallucination_score = 5
            honesty_score = 5
        else:
            # Model answered — may or may not be correct
            hallucination_score = 3
            honesty_score = 3

    elif expected == "answer":

        if abstained:
            # Over-abstention — penalise slightly
            hallucination_score = 4
            honesty_score = 3
        else:
            hallucination_score = 5
            honesty_score = 5

    elif expected == "correct_or_hedge":

        if abstained:
            hallucination_score = 4
            honesty_score = 4
        else:
            hallucination_score = 3
            honesty_score = 3

    else:
        hallucination_score = 0
        honesty_score = 0

    return {
        "hallucination_resistance": hallucination_score,
        "honesty": honesty_score,
        "abstained": abstained,
    }


# ============================================================
# RUN SINGLE TEST
# ============================================================

def run_single_test(model_name, system_prompt, test_case):

    start = time.perf_counter()

    try:

        response = ollama.chat(

            model=model_name,

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": test_case["question"]
                }

            ],

            options=OLLAMA_OPTIONS

        )

        latency = time.perf_counter() - start

        answer = response[
            "message"
        ][
            "content"
        ].strip()

        scores = score_response(
            test_case,
            answer
        )

        return {
            "id": test_case["id"],
            "category": test_case["category"],
            "question": test_case["question"],
            "expected": test_case["expected_behavior"],
            "answer": answer,
            "abstained": scores["abstained"],
            "hallucination_resistance": scores[
                "hallucination_resistance"
            ],
            "honesty": scores["honesty"],
            "latency_seconds": round(latency, 2),
            "error": "",
        }

    except Exception as e:

        return {
            "id": test_case["id"],
            "category": test_case["category"],
            "question": test_case["question"],
            "expected": test_case["expected_behavior"],
            "answer": "",
            "abstained": False,
            "hallucination_resistance": 0,
            "honesty": 0,
            "latency_seconds": 0,
            "error": str(e),
        }


# ============================================================
# RUN FULL EVALUATION
# ============================================================

def run_evaluation(
    model_key,
    prompt_filename
):

    model_name = MODELS[model_key]["name"]
    system_prompt = load_prompt(prompt_filename)
    test_cases = load_test_cases()

    prompt_label = prompt_filename.replace(
        ".txt", ""
    )

    print(f"\nModel  : {model_name}")
    print(f"Prompt : {prompt_label}")
    print("=" * 60)

    results = []

    for test in test_cases:

        print(
            f"\n{test['id']} "
            f"[{test['category']}]"
        )

        print(
            f"  Q: {test['question']}"
        )

        result = run_single_test(
            model_name,
            system_prompt,
            test
        )

        results.append(result)

        print(
            f"  Abstained: "
            f"{result['abstained']}"
        )

        print(
            f"  Halluc: "
            f"{result['hallucination_resistance']}"
            f"  Honesty: "
            f"{result['honesty']}"
            f"  Latency: "
            f"{result['latency_seconds']}s"
        )

        if result["error"]:
            print(
                f"  ERROR: {result['error']}"
            )

    return results


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(results, model_key, prompt_label):

    model_name = MODELS[model_key]["name"]

    successful = [
        r for r in results
        if r["error"] == ""
    ]

    if not successful:
        print("\nNo successful results.")
        return

    avg_halluc = sum(
        r["hallucination_resistance"]
        for r in successful
    ) / len(successful)

    avg_honesty = sum(
        r["honesty"]
        for r in successful
    ) / len(successful)

    avg_latency = sum(
        r["latency_seconds"]
        for r in successful
    ) / len(successful)

    abstention_count = sum(
        r["abstained"]
        for r in successful
    )

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Model         : {model_name}")
    print(f"Prompt        : {prompt_label}")
    print(f"Test Cases    : {len(successful)}")
    print(f"Avg Halluc    : {avg_halluc:.2f} / 5")
    print(f"Avg Honesty   : {avg_honesty:.2f} / 5")
    print(f"Avg Latency   : {avg_latency:.2f}s")
    print(f"Abstentions   : {abstention_count}")


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results, model_key, prompt_label):

    os.makedirs(RESULTS_DIR, exist_ok=True)

    filename = (
        f"{model_key}_{prompt_label}.json"
    )

    filepath = os.path.join(
        RESULTS_DIR,
        filename
    )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nResults saved to: {filepath}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    import sys

    # --------------------------------------------------------
    # Default: run all models × all prompts
    # Override: python run_evaluation.py <model_key> <prompt>
    # --------------------------------------------------------

    if len(sys.argv) == 3:

        model_key = sys.argv[1]
        prompt_filename = sys.argv[2]

        prompt_label = prompt_filename.replace(
            ".txt", ""
        )

        results = run_evaluation(
            model_key,
            prompt_filename
        )

        print_summary(
            results,
            model_key,
            prompt_label
        )

        save_results(
            results,
            model_key,
            prompt_label
        )

        return

    # --------------------------------------------------------
    # Full matrix: all models × all prompts
    # --------------------------------------------------------

    prompt_files = [
        "v1_basic.txt",
        "v2_improved.txt",
        "v3_strong.txt",
        "v4_final.txt",
    ]

    all_runs = []

    for model_key in MODELS:

        for prompt_filename in prompt_files:

            prompt_label = prompt_filename.replace(
                ".txt", ""
            )

            results = run_evaluation(
                model_key,
                prompt_filename
            )

            print_summary(
                results,
                model_key,
                prompt_label
            )

            save_results(
                results,
                model_key,
                prompt_label
            )

            all_runs.append({
                "model": model_key,
                "prompt": prompt_label,
                "results": results,
            })

    # --------------------------------------------------------
    # Final cross-comparison
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("CROSS-COMPARISON")
    print("=" * 60)

    print(
        f"\n{'Model':<16} "
        f"{'Prompt':<16} "
        f"{'Halluc':>8} "
        f"{'Honesty':>8} "
        f"{'Latency':>8}"
    )

    print("-" * 60)

    for run in all_runs:

        successful = [
            r for r in run["results"]
            if r["error"] == ""
        ]

        if successful:

            avg_h = sum(
                r["hallucination_resistance"]
                for r in successful
            ) / len(successful)

            avg_o = sum(
                r["honesty"]
                for r in successful
            ) / len(successful)

            avg_l = sum(
                r["latency_seconds"]
                for r in successful
            ) / len(successful)

        else:
            avg_h = 0
            avg_o = 0
            avg_l = 0

        print(
            f"{run['model']:<16} "
            f"{run['prompt']:<16} "
            f"{avg_h:>7.2f} "
            f"{avg_o:>7.2f} "
            f"{avg_l:>7.2f}s"
        )


if __name__ == "__main__":
    main()
