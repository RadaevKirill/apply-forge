import json
from collections.abc import Callable

from openai.types.responses import FunctionToolParam

from src.tools.browser import BROWSER_FUNCTIONS, BROWSER_TOOLS
from src.tools.files import FILE_FUNCTIONS, FILE_TOOLS

TOOLS: list[FunctionToolParam] = [
    *FILE_TOOLS,
    *BROWSER_TOOLS,
]

FUNCTIONS: dict[str, Callable[..., str]] = {
    **FILE_FUNCTIONS,
    **BROWSER_FUNCTIONS,
}


def execute_tool(name: str, arguments: str) -> str:
    handler = FUNCTIONS.get(name)

    if handler is None:
        return f"Неизвестный инструмент: {name}"

    try:
        return handler(**json.loads(arguments or "{}"))
    except Exception as e:
        return f"Ошибка: {e}"
