import requests
import json


class OllamaClient:
    """
    Hardened Ollama client.

    Guarantees:
    - Never returns invalid JSON
    - Fails loudly and clearly
    - No silent corruption of downstream logic
    """

    def __init__(
        self,
        model: str = "phi3:mini",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str) -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        raw = response.json()

        # Ollama returns generated text under "response"
        text = raw.get("response", "")

        if not isinstance(text, str) or not text.strip():
            raise ValueError("LLM returned empty response")

        text = text.strip()

        # Strict JSON parse
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON:\n{text}"
            ) from e

        if not isinstance(parsed, dict):
            raise ValueError(
                f"LLM JSON root must be an object, got {type(parsed)}"
            )

        return parsed
