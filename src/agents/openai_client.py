from typing import Any

from openai import OpenAI
from openai.types.responses import Response, ResponseFunctionToolCall

from src.settings import Settings
from src.tools.common import TOOLS, execute_tool


def create_client(settings: Settings) -> OpenAI:
    """Создаёт клиент OpenAI по настройкам. Без ключа работать не будет."""
    if not settings.llm_api_key:
        raise RuntimeError("Не задана переменная окружения LLM_API_KEY")
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_url)


def stream_response(client: OpenAI, settings: Settings, history: list[Any]) -> Response:
    """Отправляет историю в API, печатает текст по мере поступления и возвращает итоговый Response."""
    stream = client.responses.create(
        model=settings.llm_model,
        input=history,
        tools=TOOLS,
        prompt_cache_key=settings.llm_cache_key,
        stream=True,
    )

    final: Response | None = None
    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
        elif event.type == "response.completed":
            final = event.response

    if final is None:
        raise RuntimeError("Стрим завершился без response.completed")
    return final


def print_usage(response: Response) -> None:
    """Выводит статистику использования кэша, если API её вернул."""
    usage = response.usage
    if usage:
        print(
            f"\n[CACHE] cached={usage.input_tokens_details.cached_tokens} "
            f"input={usage.input_tokens}"
        )


def execute_tool_calls(history: list[Any], tool_calls: list[ResponseFunctionToolCall]) -> None:
    """Выполняет вызовы инструментов и добавляет их результаты в историю."""
    for call in tool_calls:
        print(f"[TOOL] {call.name}: {call.arguments}")
        result = execute_tool(call.name, call.arguments)
        history.append({
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": result,
        })


def run(settings: Settings, content: str) -> str:
    """Запускает цикл агента: запрос к модели, вызов инструментов, повтор, пока модель не ответит текстом."""
    client = create_client(settings)
    history: list[Any] = [{"role": "user", "content": content}]

    for _ in range(settings.llm_max_steps):
        response = stream_response(client, settings, history)
        print_usage(response)
        history.extend(item.model_dump(exclude_none=True) for item in response.output)

        tool_calls = [item for item in response.output if item.type == "function_call"]
        print()

        if not tool_calls:
            return response.output_text

        execute_tool_calls(history, tool_calls)

    raise RuntimeError(f"Агент не завершился за {settings.llm_max_steps} шагов")
