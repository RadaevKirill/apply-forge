import os

from functools import lru_cache

from openai import OpenAI
from openai.types.chat import ChatCompletionToolMessageParam
from src.settings import Settings
from src.tools.files import TOOLS, execute_tool

def get_client(settings: Settings):
    if settings.llm_api_key:
        return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_url)
    raise RuntimeError("Env key LLM_API_KEY or LLM_URL is not set")


def run(settings: Settings, content):
    client = get_client(settings)
    history: list = [{"role": "user", "content": content}]

    for _ in range(settings.llm_max_steps):
        response = client.responses.create(
            model=settings.llm_model,
            input=history,
            tools=TOOLS,
            prompt_cache_key=settings.llm_cache_key,
        )

        usage = response.usage
        if usage:
            print(f"[CACHE] cached={usage.input_tokens_details.cached_tokens} input={usage.input_tokens}")

        history.extend(item.model_dump(exclude_none=True) for item in response.output)
        tool_calls = [item for item in response.output if item.type == "function_call"]

        if not tool_calls:
            return response.output_text

        for call in tool_calls:
            print(f"[TOOL] {call.name}: {call.arguments}")
            result = execute_tool(call.name, call.arguments)
            history.append({"type": "function_call_output", "call_id": call.call_id, "output": result})