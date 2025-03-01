from pydantic import BaseModel


class Create(BaseModel):
    title: str
    owner_id: int
