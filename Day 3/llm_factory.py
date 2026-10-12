"""
LLM Factory Module for City Care Clinics Multi-Agent System
Initializes Google Gemini 3.5 Flash Lite via LangChain
with unified error handling and structured output support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel

# Load environment variables
ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ROOT_ENV)
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

T = TypeVar("T", bound=BaseModel)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

_llm_instance = None
_is_dummy_key = False

def get_llm(temperature: float = 0.2) -> Optional[ChatGoogleGenerativeAI]:
    """Returns singleton ChatGoogleGenerativeAI instance with resilient fallback for cloud startup."""
    global _llm_instance, _is_dummy_key

    current_key = os.getenv("GEMINI_API_KEY", "").strip() or GEMINI_API_KEY
    has_real_key = bool(current_key and not current_key.startswith("your-") and current_key != "dummy-bootstrapping-key-placeholder")

    if _llm_instance is not None:
        if _is_dummy_key and has_real_key:
            _llm_instance = None
        else:
            return _llm_instance

    if has_real_key:
        api_key = current_key
        _is_dummy_key = False
    else:
        api_key = "dummy-bootstrapping-key-placeholder"
        _is_dummy_key = True

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip() or GEMINI_MODEL

    try:
        _llm_instance = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature
        )
        return _llm_instance
    except Exception as e:
        print(f"[LLM Warning] Could not initialize Gemini LLM: {e}")
        return None

def get_structured_llm(schema: Type[T]) -> Any:
    """Returns LLM configured to produce validated Pydantic schema instances."""
    llm = get_llm()
    if llm is not None:
        try:
            return llm.with_structured_output(schema)
        except Exception:
            return None
    return None

if __name__ == "__main__":
    llm = get_llm()
    print(f"Connected successfully to model: {GEMINI_MODEL}")
