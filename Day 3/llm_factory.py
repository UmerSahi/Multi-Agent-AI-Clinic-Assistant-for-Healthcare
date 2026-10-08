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
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

T = TypeVar("T", bound=BaseModel)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

_llm_instance = None

def get_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """Returns singleton ChatGoogleGenerativeAI instance."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment or .env file.")

    _llm_instance = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=temperature
    )
    return _llm_instance

def get_structured_llm(schema: Type[T]) -> Any:
    """Returns LLM configured to produce validated Pydantic schema instances."""
    llm = get_llm()
    return llm.with_structured_output(schema)

if __name__ == "__main__":
    llm = get_llm()
    print(f"Connected successfully to model: {GEMINI_MODEL}")
