from src.agents.openai_client import run
from src.settings import get_settings

if __name__ == '__main__':
    settings = get_settings()

    while True:
        prompt = input("You > ")

        if prompt.lower() in ("exit", "quit"):
            break

        print("Agent > ", end="", flush=True)
        run(settings, prompt)
