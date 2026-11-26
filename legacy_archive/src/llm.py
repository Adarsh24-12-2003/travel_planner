from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """Return an LLM client. Default: Ollama (free, local).

    NOTE: We keep LLM usage minimal in this refactor day.
    Tools produce structured data; LLM only formats or critiques.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        # Prefer the newer package (avoids deprecation warnings)
        try:
            from langchain_ollama import ChatOllama  # type: ignore
        except Exception:  # fallback for older environments
            from langchain_community.chat_models import ChatOllama  # type: ignore
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.1")
        return ChatOllama(base_url=base_url, model=model, temperature=0.2)

    # Optional: OpenAI (commented by default in .env.example)
    if provider == "openai":
        from langchain_openai import ChatOpenAI  # requires extra install if you enable
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model, temperature=0.2)

    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
