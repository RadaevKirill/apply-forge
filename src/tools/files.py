import json
from collections.abc import Callable
from pathlib import Path

from openai.types.responses import FunctionToolParam

BASE_DIR = Path.cwd().resolve()


def _resolve(path: str) -> Path:
    full = (BASE_DIR / path).resolve()
    if full != BASE_DIR and BASE_DIR not in full.parents:
        raise PermissionError(f"Доступ за пределами рабочей папки запрещён: {path}")
    return full


def list_files(path: str = ".") -> str:
    target = _resolve(path)
    if not target.is_dir():
        return f"Не папка: {path}"
    entries = sorted(
        f"{p.relative_to(BASE_DIR)}{'/' if p.is_dir() else ''}" for p in target.iterdir()
    )
    return "\n".join(entries) or "(пусто)"


def read_file(path: str) -> str:
    target = _resolve(path)
    if not target.is_file():
        return f"Файл не найден: {path}"
    return target.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Записано: {path}"



TOOLS: list[FunctionToolParam] = [
    {
        "type": "function",
        "name": "list_files",
        "description": "Показать файлы и папки в указанной директории.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Путь относительно рабочей папки",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Прочитать текстовый файл.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Путь к файлу относительно рабочей папки",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "write_file",
        "description": "Записать текст в файл, перезаписывая его содержимое.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Путь к файлу относительно рабочей папки",
                },
                "content": {
                    "type": "string",
                    "description": "Новое содержимое файла",
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

FUNCTIONS: dict[str, Callable[..., str]] = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}


def execute_tool(name: str, arguments: str) -> str:
    handler = FUNCTIONS.get(name)

    if handler is None:
        return f"Неизвестный инструмент: {name}"
    
    try:
        return handler(**json.loads(arguments or "{}"))
    except Exception as e:
        return f"Ошибка: {e}"
