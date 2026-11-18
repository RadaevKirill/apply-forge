from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI
from openai.types.responses import Response, ResponseFunctionToolCall

from src.settings import Settings
from src.tools.common import TOOLS, execute_tool

INSTRUCTIONS_PATH = Path("assets/instruction.txt")


@dataclass
class TokenUsage:
    """Счётчик токенов. Используется и для одного сообщения, и для суммы за сессию."""
    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: "TokenUsage") -> None:
        self.input_tokens += other.input_tokens
        self.cached_tokens += other.cached_tokens
        self.output_tokens += other.output_tokens
        self.total_tokens += other.total_tokens

    @classmethod
    def from_response(cls, response: Response) -> "TokenUsage":
        usage = response.usage
        if not usage:
            return cls()
        details = usage.input_tokens_details
        return cls(
            input_tokens=usage.input_tokens or 0,
            cached_tokens=(details.cached_tokens if details else 0) or 0,
            output_tokens=usage.output_tokens or 0,
            total_tokens=usage.total_tokens or 0,
        )


def create_client(settings: Settings) -> OpenAI:
    """Создаёт клиент OpenAI по настройкам. Без ключа работать не будет."""
    if not settings.llm_api_key:
        raise RuntimeError("Не задана переменная окружения LLM_API_KEY")
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_url)


def load_instructions() -> str:
    """Читает системную инструкцию агента из assets/instruction.txt."""
    return INSTRUCTIONS_PATH.read_text(encoding="utf-8")


def stream_response(client: OpenAI, settings: Settings, instructions: str, history: list[Any]) -> Response:
    """Отправляет историю в API, печатает текст по мере поступления и возвращает итоговый Response."""
    stream = client.responses.create(
        model=settings.llm_model,
        instructions=instructions,
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


def print_usage(usage: TokenUsage) -> None:
    """Выводит статистику токенов одного запроса к API."""
    print(
        f"\n[TOKENS] запрос: total={usage.total_tokens} "
        f"input={usage.input_tokens} (cached={usage.cached_tokens}) "
        f"output={usage.output_tokens}"
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


def run(settings: Settings, content: str) -> tuple[str, TokenUsage]:
    """Запускает цикл агента. Возвращает текст ответа и сумму токенов по всем запросам этого сообщения."""
    client = create_client(settings)
    instructions = load_instructions()
    history: list[Any] = [{"role": "user", "content": content}]
    message_usage = TokenUsage()

    for _ in range(settings.llm_max_steps):
        response = stream_response(client, settings, instructions, history)
        request_usage = TokenUsage.from_response(response)
        message_usage.add(request_usage)
        print_usage(request_usage)
        history.extend(item.model_dump(exclude_none=True) for item in response.output)

        tool_calls = [item for item in response.output if item.type == "function_call"]
        print()

        if not tool_calls:
            return response.output_text, message_usage

        execute_tool_calls(history, tool_calls)

    raise RuntimeError(f"Агент не завершился за {settings.llm_max_steps} шагов")
