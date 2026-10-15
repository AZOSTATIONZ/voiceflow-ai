"""Pluggable LLM backends. Each provider implements complete(system, user) -> str."""
import logging

import requests

log = logging.getLogger(__name__)


class Provider:
    name = "base"

    def __init__(self, model: str, api_key: str = "", host: str = ""):
        self.model, self.api_key, self.host = model, api_key, host

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError

    def prewarm(self, system: str) -> None:
        """Called while the user is still speaking. Local backends load the model and cache the prompt prefix."""


class OllamaProvider(Provider):
    """Local models via Ollama: llama3, mistral, gemma, deepseek-r1, etc."""
    name = "ollama"
    _resolved: dict[str, str] = {}  # configured name -> installed name

    def __init__(self, model, api_key="", host=""):
        # On Windows "localhost" tries IPv6 first and Ollama only listens on IPv4: ~2 s lost per request.
        super().__init__(model, api_key, host.rstrip("/").replace("://localhost", "://127.0.0.1"))

    def installed_models(self) -> list[str]:
        r = requests.get(f"{self.host.rstrip('/')}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]

    def _resolve_model(self) -> str:
        """Fall back to an installed model when the configured one hasn't been pulled (llama3 -> llama3.2)."""
        installed = self.installed_models()
        if not installed:
            raise RuntimeError("Ollama has no models installed. Run: ollama pull llama3.2")
        base = self.model.split(":")[0]
        match = next((m for m in installed if m.split(":")[0] == base), None) \
            or next((m for m in installed if m.startswith(base)), None) or installed[0]
        log.warning("Ollama model '%s' not installed, using '%s'", self.model, match)
        return match

    def _chat(self, model, messages, num_predict):
        return requests.post(f"{self.host.rstrip('/')}/api/chat", timeout=60, json={
            "model": model, "stream": False, "keep_alive": "60m",
            "options": {"temperature": 0.2, "num_predict": num_predict, "num_ctx": 4096},
            "messages": messages,
        })

    def _request(self, messages, num_predict):
        model = self._resolved.get(self.model, self.model)
        r = self._chat(model, messages, num_predict)
        if r.status_code == 404:
            model = self._resolved[self.model] = self._resolve_model()
            r = self._chat(model, messages, num_predict)
        r.raise_for_status()
        return r.json()["message"]["content"]

    def complete(self, system, user):
        # Cleaned text is about as long as the dictation; cap generation so a rambling model can't stall.
        limit = max(64, len(user) // 2)
        return self._request([{"role": "system", "content": system}, {"role": "user", "content": user}], limit)

    def prewarm(self, system):
        # Load-only request: brings the model into memory (several seconds when cold) without touching the KV cache.
        model = self._resolved.get(self.model, self.model)
        r = requests.post(f"{self.host}/api/generate", timeout=60, json={"model": model, "keep_alive": "60m"})
        if r.status_code == 404:
            self._resolved[self.model] = self._resolve_model()


class AnthropicProvider(Provider):
    name = "anthropic"

    def complete(self, system, user):
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key, timeout=30)
        msg = client.messages.create(model=self.model, max_tokens=2048, system=system,
                                     messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in msg.content if b.type == "text")


class OpenAIProvider(Provider):
    name = "openai"
    base_url: str | None = None

    def complete(self, system, user):
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=30)
        resp = client.chat.completions.create(model=self.model, temperature=0.2, messages=[
            {"role": "system", "content": system}, {"role": "user", "content": user}])
        return resp.choices[0].message.content or ""


class MistralProvider(OpenAIProvider):
    name = "mistral"
    base_url = "https://api.mistral.ai/v1"


class DeepSeekProvider(OpenAIProvider):
    name = "deepseek"
    base_url = "https://api.deepseek.com"


class GeminiProvider(Provider):
    name = "gemini"

    def complete(self, system, user):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        r = requests.post(url, headers={"x-goog-api-key": self.api_key}, timeout=30, json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.2},
        })
        r.raise_for_status()
        return "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])


PROVIDERS = {p.name: p for p in (OllamaProvider, AnthropicProvider, OpenAIProvider,
                                  MistralProvider, DeepSeekProvider, GeminiProvider)}


def create_provider(settings) -> Provider:
    cls = PROVIDERS[settings.provider]
    return cls(settings.model_for(settings.provider), settings.api_keys.get(settings.provider, ""),
               settings.ollama_host)
