import os
from typing import Any
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


def get_llm(model: str | None = None, temperature: float = 0.0, **kwargs: Any) -> Any:
    """
    Initialize and return a chat LLM instance based on available environment variables.
    Defaults to Mistral AI (using MISTRAL_API_KEY) and falls back to OpenAI (using OPENAI_API_KEY).
    """
    mistral_api_key = (os.getenv("MISTRAL_API_KEY") or "").strip()
    openai_api_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    if mistral_api_key:
        
        chosen_model = model or os.getenv("MISTRAL_MODEL", "mistral-large-latest").strip()
        return ChatMistralAI(
            model=chosen_model,
            mistral_api_key=mistral_api_key,
            temperature=temperature,
            **kwargs,
        )

    if openai_api_key:

        chosen_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        return ChatOpenAI(
            model=chosen_model,
            api_key=openai_api_key,
            temperature=temperature,
            **kwargs,
        )

    raise ValueError(
        "Neither MISTRAL_API_KEY nor OPENAI_API_KEY is configured in your environment or .env file."
    )
