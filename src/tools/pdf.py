from collections.abc import Callable

from openai.types.responses import FunctionToolParam

from src.tools.files import _resolve


def create_pdf(path: str, html: str) -> str:
    """Создаёт PDF из HTML (с CSS внутри <style>) и сохраняет его по указанному пути."""
    from weasyprint import HTML

    if not path.lower().endswith(".pdf"):
        return f"Путь должен заканчиваться на .pdf: {path}"

    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(target)
    return f"PDF создан: {path}"


PDF_TOOLS: list[FunctionToolParam] = [
    {
        "type": "function",
        "name": "create_pdf",
        "description": (
            "Создать PDF-файл из HTML-разметки с CSS (в теге <style>). "
            "Используй для финального резюме, которое нужно отдать в формате PDF."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Путь к PDF-файлу относительно рабочей папки, например assets/resume.pdf",
                },
                "html": {
                    "type": "string",
                    "description": "Полный HTML-документ (<!DOCTYPE html> ... </html>) с содержимым резюме",
                },
            },
            "required": ["path", "html"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

PDF_FUNCTIONS: dict[str, Callable[..., str]] = {
    "create_pdf": create_pdf,
}
