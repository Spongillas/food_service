import json

from pydantic import ValidationError

from app.models import SearchRequest, Supplier
from app.services.openrouter_client import OpenRouterError, chat_completion

SCHEMA_HINT = """
Верни ТОЛЬКО JSON-массив (без markdown, без пояснений) объектов со следующими полями
(если данных нет — ставь null, НЕ придумывай):
[
  {
    "name": "название компании",
    "category": "категория товара",
    "region": "город/регион работы",
    "description": "1-2 предложения, чем занимается поставщик",
    "website": "URL сайта или null",
    "source_url": "URL страницы-источника, откуда взята информация",
    "phone": "телефон или null",
    "email": "email или null",
    "other_contacts": "телеграм/whatsapp/др. или null",
    "min_order": "минимальный объём заказа или null",
    "price_info": "ориентировочная цена/диапазон или null",
    "certificates": "сертификаты/документы (ХАССП, ГОСТ и т.п.) или null",
    "delivery_terms": "условия доставки или null",
    "notes": "любые дополнительные заметки или null",
    "confidence": 0.0-1.0 (насколько ты уверен, что это реальная действующая компания и данные точны)
  }
]
"""


def _build_messages(req: SearchRequest) -> list[dict]:
    system = (
        "Ты — ассистент по поиску поставщиков продуктов питания и сопутствующих товаров "
        "(ингредиенты, готовая продукция, упаковка). Ты используешь веб-поиск, чтобы найти "
        "РЕАЛЬНЫЕ действующие компании (сайты, каталоги b2b, маркетплейсы, справочники), а не выдумывать их. "
        "Отвечай строго на русском языке и строго в формате, указанном пользователем."
    )
    user = (
        f"Найди {req.limit} поставщиков по категории: \"{req.category}\".\n"
        f"Регион/город: \"{req.region or 'любой, приоритет России'}\".\n"
        f"Дополнительные пожелания: \"{req.keywords or 'нет'}\".\n\n"
        f"{SCHEMA_HINT}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _extract_json_array(text: str) -> list[dict]:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("В ответе модели не найден JSON-массив")
    candidate = text[start : end + 1]
    return json.loads(candidate)


def _score(supplier: Supplier) -> float:
    optional_fields = [
        supplier.website,
        supplier.phone or supplier.email or supplier.other_contacts,
        supplier.min_order,
        supplier.price_info,
        supplier.certificates,
        supplier.delivery_terms,
    ]
    completeness = sum(1 for f in optional_fields if f) / len(optional_fields)
    return round(supplier.confidence * 0.4 + completeness * 0.6, 3)


def _rank(suppliers: list[Supplier]) -> list[Supplier]:
    for s in suppliers:
        s.score = _score(s)
    suppliers.sort(key=lambda s: s.score, reverse=True)
    for i, s in enumerate(suppliers):
        s.recommended = i == 0 and s.score > 0
    return suppliers


def _mock_suppliers(req: SearchRequest) -> list[Supplier]:
    region = req.region or "Россия"
    base = [
        Supplier(
            name=f"ООО «{req.category.title()} Трейд»",
            category=req.category,
            region=region,
            description=f"Демо-запись: пример поставщика категории «{req.category}». "
            "Задайте OPENROUTER_API_KEY, чтобы включить реальный ИИ-поиск.",
            website="https://example.com",
            source_url="https://example.com/about",
            phone="+7 (999) 000-00-00",
            email="sales@example.com",
            min_order="от 50 кг / 1 паллета",
            price_info="уточняется по запросу",
            certificates="ГОСТ, декларация соответствия",
            delivery_terms=f"доставка по {region} и области, от 1-2 дней",
            notes="Демо-данные, не реальная компания.",
            confidence=0.3,
        ),
        Supplier(
            name=f"ИП Поставщик «{req.category.title()} Плюс»",
            category=req.category,
            region=region,
            description="Демо-запись №2 для проверки интерфейса и сортировки.",
            website=None,
            source_url="https://example.com/catalog",
            phone=None,
            email="info@example-2.com",
            min_order=None,
            price_info="от 250 руб/кг (демо)",
            certificates=None,
            delivery_terms="самовывоз",
            notes="Демо-данные, не реальная компания.",
            confidence=0.2,
        ),
    ]
    return base[: req.limit]


async def find_suppliers(req: SearchRequest) -> tuple[list[Supplier], bool, str | None]:
    """Возвращает (список поставщиков, использовался_ли_реальный_ИИ, предупреждение)."""
    from app.config import get_settings

    settings = get_settings()
    if not settings.ai_enabled:
        return _rank(_mock_suppliers(req)), False, (
            "Демо-режим: OPENROUTER_API_KEY не задан, показаны примерные данные."
        )

    try:
        content = await chat_completion(_build_messages(req))
        raw_items = _extract_json_array(content)
        suppliers: list[Supplier] = []
        for item in raw_items:
            try:
                suppliers.append(Supplier(**item))
            except (ValidationError, TypeError):
                continue
        if not suppliers:
            raise ValueError("Модель не вернула ни одной корректной записи")
        return _rank(suppliers), True, None
    except (OpenRouterError, ValueError, json.JSONDecodeError, TypeError) as exc:
        fallback = _rank(_mock_suppliers(req))
        return fallback, False, f"Не удалось получить данные от ИИ ({exc}); показаны примерные данные."
