from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PreviewKioskRenderRequest(BaseModel):
    business_id: UUID
    draft: dict[str, Any] = Field(default_factory=dict)
