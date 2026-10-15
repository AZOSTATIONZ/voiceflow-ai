import logging
import re

from ai.prompts import build_system_prompt, build_user_prompt
from ai.providers import create_provider

log = logging.getLogger(__name__)

FILLERS = re.compile(r"\b(um+|uh+|erm+|hmm+|you know)\b,?\s*", re.IGNORECASE)
PREAMBLE = re.compile(r"^(here is|here's|sure|cleaned text|output)[^\n]*:\s*\n+", re.IGNORECASE)


def basic_cleanup(text: str) -> str:
    """Offline fallback used when the AI backend is unreachable."""
    text = FILLERS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    text = re.sub(r"\bi\b", "I", text)
    text = text[0].upper() + text[1:]
    text = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    if text[-1] not in ".!?":
        text += "."
    return text


def postprocess(output: str) -> str:
    out = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()  # reasoning models
    out = PREAMBLE.sub("", out)
    out = re.sub(r"</?dictation>", "", out).strip()
    if len(out) >= 2 and out[0] == out[-1] and out[0] in "\"'":
        out = out[1:-1]
    return out.strip()


REFUSAL = re.compile(r"\b(I can't|I cannot|I'm sorry|I am sorry|as an AI|I'm unable|I am unable)\b", re.IGNORECASE)


def looks_wrong(raw: str, out: str) -> bool:
    """Catch small-model failures (answering, refusing, truncating) so they are never pasted."""
    if REFUSAL.search(out) and not REFUSAL.search(raw):
        return True
    raw_words = len(FILLERS.sub("", raw).split())
    out_words = len(re.sub(r"\b(Hi|Hello|Dear|Best regards|Thanks|Regards)\b", "", out).split())
    if raw_words >= 4 and out_words < 0.5 * raw_words:
        return True
    return out[:1].islower()  # cleaned text always starts capitalized (or with code/punctuation)


class Cleaner:
    def __init__(self, settings):
        self.settings = settings

    def prewarm(self, ctx=None) -> None:
        try:
            create_provider(self.settings).prewarm(build_system_prompt(ctx))
        except Exception as e:
            log.debug("prewarm failed: %s", e)

    def clean(self, raw: str, ctx=None) -> tuple[str, bool]:
        """Returns (text, used_ai)."""
        if not raw.strip():
            return "", False
        if not self.settings.ai_cleanup:
            return basic_cleanup(raw), False
        try:
            provider = create_provider(self.settings)
            out = postprocess(provider.complete(build_system_prompt(ctx), build_user_prompt(raw, ctx)))
            if out and not looks_wrong(raw, out):
                return out, True
            log.warning("AI output rejected: %r", out)
        except Exception as e:
            log.warning("AI cleanup failed (%s): %s", self.settings.provider, e)
        return basic_cleanup(raw), False
