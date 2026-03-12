"""
llm.py — LLM client wrapper using Google Gemini API (FREE tier).

Free quota: 1,500 requests/day, 1M tokens/day — no credit card needed.
Get your free API key at: https://aistudio.google.com/app/apikey

Supports fallback to any OpenAI-compatible provider via env var.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_model = None


def get_model():
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ GEMINI_API_KEY not set!\n"
                "👉 Get your FREE key at: https://aistudio.google.com/app/apikey\n"
                "   Then add to .env:  GEMINI_API_KEY=your_key_here"
            )
        genai.configure(api_key=api_key)
        model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        _model = genai.GenerativeModel(model_name)
    return _model


def chat(
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> str:
    """
    Chat with Gemini. Combines system + user into a single prompt
    (Gemini Flash uses single-turn format).
    Temperature=0 for deterministic SQL generation.
    """
    gemini_model = get_model()

    # Gemini doesn't have a separate system role — prepend it to the user message
    full_prompt = f"{system}\n\n---\n\n{user}"

    response = gemini_model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text.strip()

import google.generativeai as genai
genai.configure(api_key="AIzaSyBLN3hcXBPwvOAxIYUJ6MQsTZ6iYR_hDSM")

for m in genai.list_models():
    print(m.name)