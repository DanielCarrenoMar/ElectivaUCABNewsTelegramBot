from typing import Optional
from pydantic import BaseModel


class CountriesDto(BaseModel):
    id: Optional[int] = None
    country: Optional[str] = None