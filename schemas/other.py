from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class Metric1(BaseModel):
    hhi_index: float


class Metric2(BaseModel):
    win_rate: float


class Metric3(BaseModel):
    avg_reduction_percent: float


class Metric4(BaseModel):
    my_revenue: float


class KpgzSchema(BaseModel):
    id: int
    code_kpgz: str
    name: str

    class Config:
        from_attributes = True


class KsSchema(BaseModel):
    id_ks: int
    link: str
    start_ks: datetime
    end_ks: datetime
    start_price: Decimal
    end_price: Decimal
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
    price: Decimal
    oferta_price: Decimal
    oferta_start: datetime
    oferta_end: datetime
    count: int

    class Config:
        from_attributes = True
