from pydantic import BaseModel, EmailStr


class Base(BaseModel):
    full_name: str
    email: EmailStr


class Login(BaseModel):
    email: str
    password: str


class Auth(BaseModel):
    token: str


class Create(Base):
    password: str


class Update(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class Read(Base):
    id: int
    supplier_id: int

    class Config:
        from_attributes = True
