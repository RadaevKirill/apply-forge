# apply-forge

Карьерный помощник на базе LLM. Адаптирует резюме под вакансию, пишет сопроводительное письмо и сохраняет резюме в PDF.

## Установка

Нужны Python 3.12+ и [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run playwright install chromium
```

Для PDF (WeasyPrint) нужны системные библиотеки Pango. На Debian/Ubuntu: `sudo apt install libpango-1.0-0 libpangoft2-1.0-0`.

## Настройка

Создай файл `.env` в корне проекта:

```env
LLM_API_KEY=твой_ключ
LLM_MODEL=название_модели
LLM_URL=адрес_api
LLM_MAX_STEPS=10
LLM_CACHE_KEY=apply-forge
```

`LLM_CACHE_KEY` необязательный, по умолчанию `apply-forge`.

## Запуск

```bash
uv run main.py
```

Введи запрос в строке `You >`. Для выхода напиши `exit`.

## Файлы

- `assets/instruction.txt`: системная инструкция агента. Читается при каждом сообщении, менять можно без перезапуска.
- `assets/анкета_кандидата.md`: анкета с данными о тебе. Агент берёт из неё опыт и навыки.
- `assets/`: остальные файлы в git не попадают (см. `.gitignore`).

## Инструменты агента

- `list_files`, `read_file`, `write_file`: работа с файлами в рабочей папке.
- `create_pdf`: создаёт PDF из HTML с CSS.
- `fetch_page`: открывает страницу в браузере и возвращает текст (например, вакансию по ссылке).

Все пути ограничены рабочей папкой проекта.
