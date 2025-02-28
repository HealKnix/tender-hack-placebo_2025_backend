from pydantic import BaseModel, EmailStr
from datetime import datetime
from decimal import Decimal


class UserBaseSchema(BaseModel):
    full_name: str
    email: EmailStr


class UserLoginSchema(BaseModel):
    email: str
    password: str


class UserCreateSchema(UserBaseSchema):
    password: str


class UserUpdateSchema(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class UserReadSchema(UserBaseSchema):
    id: int

    class Config:
        from_attributes = True


class DeepSeekPromtSchema(BaseModel):
    prompt: str


class DeepSeekSchema(BaseModel):
    message: str


# ################################################################


class KpgzSchema(BaseModel):
    id: int
    code_kpgz: str
    name: str

    class Config:
        from_attributes = True


class KSSchema(BaseModel):
    id_ks: int
    link: str
    start_ks: datetime
    end_ks: datetime
    start_price: Decimal
    end_price: Decimal
    oferta_price: Decimal
    oferta_start: datetime
    oferta_end: datetime
    customer_id: int
    winner_id: int

    class Config:
        from_attributes = True


class CustomerSchema(BaseModel):
    id: int
    name: str
    inn: str
    region_id: int

    class Config:
        from_attributes = True


class SupplierSchema(BaseModel):
    id: int
    name: str
    inn: str
    region_id: int

    class Config:
        from_attributes = True


class CteSchema(BaseModel):
    id: int
    name: str
    link: str
    price: Decimal
    kpgz_id: int

    class Config:
        from_attributes = True


class ParticipantSchema(BaseModel):
    id: int
    id_ks: int
    id_participant: int

    class Config:
        from_attributes = True


class RegionSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    id: int
    id_cte: int
    id_ks: int
    count: int

    class Config:
        from_attributes = True
