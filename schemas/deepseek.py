from pydantic import BaseModel


class Promt(BaseModel):
    prompt: str


class Message(BaseModel):
    message: str
