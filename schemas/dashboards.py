from pydantic import BaseModel
from typing import List, Tuple


class Create(BaseModel):
    title: str
    owner_id: int
    properties: list[str]
