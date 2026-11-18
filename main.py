from src.agents.openai_client import TokenUsage, run
from src.settings import get_settings

if __name__ == '__main__':
    settings = get_settings()
    session_usage = TokenUsage()

    while True:
        prompt = input("You > ")

        if prompt.lower() in ("exit", "quit"):
            break

        print("Agent > ", end="", flush=True)
        _, message_usage = run(settings, prompt)
        session_usage.add(message_usage)

        print(
            f"[TOKENS] на сообщение: {message_usage.total_tokens} | "
            f"всего за сессию: {session_usage.total_tokens} "
            f"(input={session_usage.input_tokens}, "
            f"cached={session_usage.cached_tokens}, "
            f"output={session_usage.output_tokens})"
        )
