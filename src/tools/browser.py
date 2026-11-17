from collections.abc import Callable
from urllib.parse import urlparse

from openai.types.responses import FunctionToolParam

MAX_CHARS = 20_000
TIMEOUT_MS = 30_000


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Допустимы только http/https ссылки: {url}")
    return url


def fetch_page(url: str, selector: str | None = None) -> str:
    """Открывает страницу в headless-браузере (Chromium) и возвращает видимый текст.

    Если передан selector (CSS), возвращается текст только первого подходящего элемента.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return (
            "Playwright не установлен. Выполните: uv add playwright "
            "и затем: uv run playwright install chromium"
        )

    url = _validate_url(url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=TIMEOUT_MS)
            except Exception:
                pass  # страница может постоянно что-то подгружать — берём что есть

            title = page.title()
            if selector:
                element = page.query_selector(selector)
                if element is None:
                    return f"Элемент не найден по селектору '{selector}' на {url}"
                text = element.inner_text()
            else:
                text = page.inner_text("body")
        finally:
            browser.close()

    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n...[обрезано]"
    return f"Заголовок: {title}\nURL: {url}\n\n{text}"


BROWSER_TOOLS: list[FunctionToolParam] = [
    {
        "type": "function",
        "name": "fetch_page",
        "description": (
            "Открыть веб-страницу в браузере (с выполнением JavaScript) и получить её текстовое содержимое. "
            "Используй, когда нужна информация по ссылке."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Полный адрес страницы, начинающийся с http:// или https://",
                },
                "selector": {
                    "type": ["string", "null"],
                    "description": "Необязательный CSS-селектор, чтобы получить текст только одного элемента. null — вся страница.",
                },
            },
            "required": ["url", "selector"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

BROWSER_FUNCTIONS: dict[str, Callable[..., str]] = {
    "fetch_page": fetch_page,
}
