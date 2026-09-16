"""
models/groq_client.py
Thin wrapper around the Groq API so the rest of the app never talks to the SDK directly.
Exposes two methods matching the assignment's two-model split:
  - fast_completion()      -> Gemma (classification, extraction, scope detection)
  - reasoning_completion()  -> Llama 3.3 70B (analysis, impact assessment)
"""

from groq import Groq
from config import settings


class GroqClient:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self.fast_model = settings.GROQ_FAST_MODEL
        self.reasoning_model = settings.GROQ_REASONING_MODEL

    def _complete(self, model: str, prompt: str, system: str = "", temperature: float = 0.2) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content

    def fast_completion(self, prompt: str, system: str = "") -> str:
        """Use for: scope classification, keyword extraction, request-type classification, mapping."""
        return self._complete(self.fast_model, prompt, system, temperature=0.1)

    def reasoning_completion(self, prompt: str, system: str = "") -> str:
        """Use for: complex analysis, document analysis, regulatory impact assessment."""
        return self._complete(self.reasoning_model, prompt, system, temperature=0.3)


class _LazyGroqClient:
    """Delays creating the real GroqClient (and checking for the API key) until first use,
    so other modules can be imported/tested even before GROQ_API_KEY is configured."""

    def __init__(self):
        self._instance = None

    def _get(self) -> GroqClient:
        if self._instance is None:
            self._instance = GroqClient()
        return self._instance

    def fast_completion(self, prompt: str, system: str = "") -> str:
        return self._get().fast_completion(prompt, system)

    def reasoning_completion(self, prompt: str, system: str = "") -> str:
        return self._get().reasoning_completion(prompt, system)


# Import this everywhere else instead of creating new clients.
groq_client = _LazyGroqClient()
