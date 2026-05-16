from pydantic import BaseModel
from typing import Optional


class LanguageSettings(BaseModel):
    language: Optional[str]