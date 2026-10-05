# Results Directory

Evaluation results are saved here as JSON files.

Each file follows the naming convention:

```
<model_key>_<prompt_version>.json
```

For example:
- `qwen2.5_v1_basic.json`
- `deepseek-r1_v4_final.json`
- `llama3.2_v3_strong.json`

Run `scripts/run_evaluation.py` to generate results.
Run `scripts/compare_prompts.py` to compare them.
