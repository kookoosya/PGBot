"""Unit tests for classified submission validation rules."""

import pytest
from unittest.mock import AsyncMock

from app.models.enums import ClassifiedCategory
from app.services.classified.schemas import ClassifiedCreateInput, ClassifiedValidationError
from app.services.classified.validation import validate_create_input


@pytest.mark.asyncio
async def test_classified_requires_agree_rules():
    db = AsyncMock()
    data = ClassifiedCreateInput(
        category=ClassifiedCategory.FIREWOOD,
        title="Дрова сухие",
        description="Продаю дрова без предоплаты, самовывоз",
        phone="+79001234567",
        author_name="Иван",
        agree_rules=False,
    )
    with pytest.raises(ClassifiedValidationError, match="честное"):
        await validate_create_input(db, data)
