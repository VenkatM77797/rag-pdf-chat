import json
import os
from collections.abc import Iterator

import requests


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434",
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3",
)


def get_ollama_error(
    response: requests.Response,
) -> str:
    """
    Extract an error message from an Ollama response.
    """
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if isinstance(payload, dict):
        error_message = payload.get("error")

        if error_message:
            return str(error_message)

    return (
        "Ollama request failed with status "
        f"{response.status_code}."
    )


def ask_llama(prompt: str) -> str:
    """
    Generate one complete response from Ollama.
    """
    clean_prompt = prompt.strip()

    if not clean_prompt:
        raise ValueError(
            "Prompt cannot be empty."
        )

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": clean_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                },
            },
            timeout=(10, 300),
        )

    except requests.ConnectionError as error:
        raise RuntimeError(
            "Could not connect to Ollama at "
            f"{OLLAMA_BASE_URL}. "
            "Start Ollama and try again."
        ) from error

    except requests.Timeout as error:
        raise RuntimeError(
            "Ollama did not respond before "
            "the timeout."
        ) from error

    except requests.RequestException as error:
        raise RuntimeError(
            f"Ollama request failed: {error}"
        ) from error

    if not response.ok:
        raise RuntimeError(
            get_ollama_error(response)
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(
            "Ollama returned invalid JSON."
        ) from error

    answer = payload.get(
        "response",
        "",
    ).strip()

    if not answer:
        raise RuntimeError(
            "Ollama returned an empty answer."
        )

    return answer


def stream_llama(
    prompt: str,
) -> Iterator[str]:
    """
    Open an Ollama streaming request and return its iterator.
    """
    clean_prompt = prompt.strip()

    if not clean_prompt:
        raise ValueError(
            "Prompt cannot be empty."
        )

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": clean_prompt,
                "stream": True,
                "options": {
                    "temperature": 0.2,
                },
            },
            stream=True,
            timeout=(10, 300),
        )

    except requests.ConnectionError as error:
        raise RuntimeError(
            "Could not connect to Ollama at "
            f"{OLLAMA_BASE_URL}. "
            "Start Ollama and try again."
        ) from error

    except requests.Timeout as error:
        raise RuntimeError(
            "Ollama did not respond before "
            "the timeout."
        ) from error

    except requests.RequestException as error:
        raise RuntimeError(
            f"Ollama request failed: {error}"
        ) from error

    if not response.ok:
        error_message = get_ollama_error(
            response
        )

        response.close()

        raise RuntimeError(
            error_message
        )

    def generate() -> Iterator[str]:
        received_text = False

        with response:
            for line in response.iter_lines(
                decode_unicode=True
            ):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                error_message = data.get(
                    "error"
                )

                if error_message:
                    raise RuntimeError(
                        str(error_message)
                    )

                chunk = data.get(
                    "response",
                    "",
                )

                if chunk:
                    received_text = True
                    yield chunk

                if data.get("done"):
                    break

        if not received_text:
            raise RuntimeError(
                "Ollama returned an empty answer."
            )

    return generate()