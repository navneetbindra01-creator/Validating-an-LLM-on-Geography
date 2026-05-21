from openai import OpenAI
import cache
import config

_CLIENT: OpenAI | None = None


def _client() -> OpenAI:
    global _CLIENT
    if _CLIENT is None:
        if not config.XAI_API_KEY:
            raise EnvironmentError("XAI_API_KEY is not set. Copy .env.example → .env and add your key.")
        _CLIENT = OpenAI(api_key=config.XAI_API_KEY, base_url=config.XAI_BASE_URL)
    return _CLIENT


def ask_grok(question: str, system_prompt: str = "", use_cache: bool = True) -> str:
    """Return Grok's response, served from disk cache when available."""
    cache_key = question + ("|" + system_prompt if system_prompt else "")

    if use_cache:
        cached = cache.get_response(config.GROK_MODEL, cache_key)
        if cached is not None:
            return cached

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})

    response = _client().chat.completions.create(
        model=config.GROK_MODEL,
        messages=messages,
        temperature=0,
    )
    text = response.choices[0].message.content.strip()

    if use_cache:
        cache.set_response(config.GROK_MODEL, cache_key, text)

    return text
