import httpx

from app.config import get_settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(RuntimeError):
    pass


async def chat_completion(messages: list[dict], *, temperature: float = 0.2) -> str:
    """Отправляет запрос в OpenRouter. Если модель указана с суффиксом ':online',
    OpenRouter перед ответом сам выполняет веб-поиск (плагин на базе Exa) и
    подмешивает найденные страницы в контекст модели — это и есть "ИИ гуглит".
    """
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise OpenRouterError("OPENROUTER_API_KEY не задан")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.app_url,
        "X-Title": settings.app_name,
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)

    if resp.status_code != 200:
        raise OpenRouterError(f"OpenRouter вернул {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError(f"Неожиданный формат ответа OpenRouter: {data}") from exc
