
import os
import json
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
    ABSTENTION_PHRASES,
)


# ============================================================
# UTILITY: LOAD PROMPT
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
# UTILITY: CHECK ABSTENTION
# ============================================================

def check_abstention(response_text):

    lower = response_text.lower()

    return any(
        phrase in lower
        for phrase in ABSTENTION_PHRASES
    )


# ============================================================
# UTILITY: QUERY MODEL
# ============================================================

def query_model(
    model_name,
    system_prompt,
    user_message
):

    response = ollama.chat(

        model=model_name,

        messages=[

            {
                "role": "system",
                "content": system_prompt
            },

            {
                "role": "user",
                "content": user_message
            }

        ],

        options=OLLAMA_OPTIONS

    )

    return response[
        "message"
    ][
        "content"
    ].strip()


# ============================================================
# UTILITY: LIST AVAILABLE PROMPTS
# ============================================================

def list_prompts():

    prompts = []

    for filename in sorted(
        os.listdir(PROMPTS_DIR)
    ):

        if filename.endswith(".txt"):
            prompts.append(filename)

    return prompts


# ============================================================
# UTILITY: LIST AVAILABLE MODELS
# ============================================================

def list_models():

    return list(MODELS.keys())


# ============================================================
# UTILITY: VALIDATE MODEL KEY
# ============================================================

def validate_model_key(model_key):

    if model_key not in MODELS:

        print(
            f"Unknown model: {model_key}"
        )

        print(
            "Available: "
            + ", ".join(MODELS.keys())
        )

        sys.exit(1)


# ============================================================
# UTILITY: VALIDATE PROMPT FILE
# ============================================================

def validate_prompt_file(prompt_filename):

    filepath = os.path.join(
        PROMPTS_DIR,
        prompt_filename
    )

    if not os.path.exists(filepath):

        print(
            f"Prompt file not found: "
            f"{filepath}"
        )

        print(
            "Available: "
            + ", ".join(list_prompts())
        )

        sys.exit(1)
