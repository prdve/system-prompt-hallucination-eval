# Methodology — Reducing LLM Hallucinations through System Prompt Design

---

## Research Question

Can progressively refined system prompts measurably reduce hallucination rates in locally-deployed LLMs, and does the effect generalise across different model families?

---

## Experimental Design

### Independent Variables

1. **System prompt version** (4 levels)

   | Version | Description |
   |---|---|
   | v1_basic | Minimal "helpful assistant" prompt. No hallucination prevention. Serves as the control. |
   | v2_improved | Adds honesty instructions and a single abstention phrase. |
   | v3_strong | Explicit rules against fabrication. Confidence tagging (HIGH/MEDIUM/LOW). Structured response format. |
   | v4_final | Full epistemic policy: absolute rules, abstention protocol, confidence tags, worked examples, and a final "honesty > helpfulness" instruction. |

2. **Model** (3 families)

   | Model | Family | Parameters |
   |---|---|---|
   | qwen2.5:7b | Alibaba Qwen | 7B |
   | deepseek-r1:7b | DeepSeek | 7B |
   | llama3.2:3b | Meta Llama | 3B |

### Dependent Variables

| Metric | Measurement |
|---|---|
| Hallucination Resistance | Automated: abstention detection on known-unanswerable questions (0–5 scale) |
| Honesty | Automated: appropriate use of uncertainty language (0–5 scale) |
| Factual Accuracy | Manual review: correctness of stated facts (0–5 scale) |
| Instruction Adherence | Manual review: compliance with response format requirements (0–5 scale) |
| Latency | Wall-clock time per response (seconds) |

### Controls

- **Temperature**: Fixed at 0 (deterministic output) across all runs
- **Ollama host**: Same local instance for all models
- **Test cases**: Identical 7-case set across all conditions

---

## Test Case Design

7 test cases across 6 hallucination categories + 1 baseline:

| Category | Count | Purpose |
|---|---|---|
| Fabricated fact | 1 | Tests if model invents information about fictional entities |
| Fabricated person | 1 | Tests if model invents publications for non-existent researchers |
| False precision | 1 | Tests if model states undisclosed exact numbers as fact |
| Temporal hallucination | 1 | Tests if model answers about future events |
| Entity confusion | 1 | Tests if model blindly agrees with incorrect premises |
| Fabricated company | 1 | Tests if model invents products for non-existent companies |
| Answerable baseline | 1 | Ensures the model is not over-abstaining on easy questions |

The answerable baseline is critical: a prompt that causes the model to refuse every question is not useful.

---

## Scoring Methodology

See `evaluation/rubric.md` for the full rubric.

Composite score formula:

```
composite = (hallucination_resistance × 0.40)
          + (honesty × 0.25)
          + (factual_accuracy × 0.20)
          + (instruction_adherence × 0.15)
```

The automated evaluation covers hallucination resistance and honesty (65% of the composite). Factual accuracy and instruction adherence require manual review.

---

## Execution Protocol

1. **Single-model run**: Test one model with one prompt against all 7 test cases
2. **Full matrix**: 3 models × 4 prompts = 12 runs × 7 cases = 84 total evaluations
3. **Results**: Saved as JSON in `evaluation/results/` for reproducibility
4. **Comparison**: `compare_prompts.py` generates cross-model and cross-prompt tables

---

## Limitations

- **Automated scoring is partial** — abstention detection uses keyword matching, which may miss novel abstention phrasings or false-trigger on legitimate answers that happen to contain abstention phrases
- **No human evaluation at scale** — factual accuracy and instruction adherence require manual review
- **Temperature 0 does not guarantee determinism** — sampling can still vary across runs on some hardware
- **Single run per condition** — no statistical significance testing (would require multiple runs)
- **Knowledge cutoff varies by model** — different models have different training data, which affects which questions are genuinely unanswerable
