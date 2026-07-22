from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    category: str = Field(..., min_length=2, description="Категория товара, напр. 'упаковка для готовой еды'")
    region: str = Field("", description="Город или регион, напр. 'Москва'")
    keywords: str = Field("", description="Доп. пожелания: 'опт от 50 кг', 'нужен ХАССП' и т.п.")
    limit: int = Field(6, ge=1, le=20)


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

    @field_validator("category", "region", "description", mode="before")
    @classmethod
    def _none_to_empty(cls, v: str | None) -> str:
        return v if v is not None else ""

    @field_validator("confidence", mode="before")
    @classmethod
    def _none_confidence(cls, v: float | None) -> float:
        return v if v is not None else 0.5


class SearchResponse(BaseModel):
    query: SearchRequest
    suppliers: list[Supplier]
    used_ai: bool
    cached: bool
    warning: str | None = None
