import os
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv


@dataclass
class Settings:
    llm_api_key: str
    llm_model: str
    llm_url: str
    llm_max_steps: int
    llm_cache_key: str

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()

    return Settings(
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        llm_url=os.getenv("LLM_URL", ""),
        llm_max_steps=int(os.getenv("LLM_MAX_STEPS", "")),
        llm_cache_key=os.getenv("LLM_CACHE_KEY", "apply-forge"),
    )