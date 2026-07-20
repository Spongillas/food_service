from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    category: str = Field(..., min_length=2, description="Категория товара, напр. 'упаковка для готовой еды'")
    region: str = Field("", description="Город или регион, напр. 'Москва'")
    keywords: str = Field("", description="Доп. пожелания: 'опт от 50 кг', 'нужен ХАССП' и т.п.")
    limit: int = Field(6, ge=1, le=12)


class Supplier(BaseModel):
    name: str
    category: str = ""
    region: str = ""
    description: str = ""
    website: str | None = None
    source_url: str | None = None
    phone: str | None = None
    email: str | None = None
    other_contacts: str | None = None
    min_order: str | None = None
    price_info: str | None = None
    certificates: str | None = None
    delivery_terms: str | None = None
    notes: str | None = None
    confidence: float = Field(0.5, ge=0, le=1)
    score: float = 0.0
    recommended: bool = False


class SearchResponse(BaseModel):
    query: SearchRequest
    suppliers: list[Supplier]
    used_ai: bool
    cached: bool
    warning: str | None = None
