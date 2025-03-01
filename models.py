from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Numeric,
)
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    token = Column(String, unique=True)

    # one-to-many relationship with Dashboards
    dashboards = relationship(
        "DashboardModel", back_populates="owner", cascade="all, delete-orphan"
    )


class DashboardModel(Base):
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # relationship with User
    owner = relationship("UserModel", back_populates="dashboards", uselist=False)
    # one-to-many relationship with Reports
    reports = relationship("ReportModel", back_populates="dashboard", uselist=True)
    # one-to-many relationship with Widgets
    widgets = relationship("WidgetModel", back_populates="dashboard", uselist=True)


class WidgetModel(Base):
    __tablename__ = "widgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String)
    description = Column(Text)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # relationship with Dashboard
    dashboard = relationship("DashboardModel", back_populates="widgets", uselist=False)


class ReportStatusModel(Base):
    __tablename__ = "report_statuses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # "IN_PROGRESS", "NEW", "READY", "FAILED"
    status = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    name = Column(String, index=True, unique=True)
    title = Column(String)
    description = Column(Text)
    status_id = Column(Integer, ForeignKey("report_statuses.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # relationship with Dashboard
    dashboard = relationship("DashboardModel", back_populates="reports", uselist=False)


# ##############################################################


# Таблица "kpgz"
class KpgzModel(Base):
    __tablename__ = "kpgz"
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    code_kpgz = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)

    # Один к многим: kpgz -> cte
    cte_list = relationship("CteModel", back_populates="kpgz", uselist=True)


# Таблица "ks"
class KsModel(Base):
    __tablename__ = "ks"
    id_ks = Column(Integer, primary_key=True, nullable=False)
    link = Column(String(255), nullable=False)
    start_ks = Column(DateTime, nullable=False)
    end_ks = Column(DateTime, nullable=False)
    start_price = Column(Numeric(18, 2), nullable=False)
    end_price = Column(Numeric(18, 2), nullable=False)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("supplier.id"), nullable=False)

    # Связь с таблицей customer
    customer = relationship("CustomerModel", back_populates="ks_list", uselist=False)
    # Связь с таблицей supplier (победитель)
    supplier_winner = relationship(
        "SupplierModel",
        back_populates="ks_list",
        foreign_keys=[winner_id],
        uselist=False,
    )
    # Связь с таблицей order
    orders = relationship("OrderModel", back_populates="ks", uselist=True)
    # Связь с таблицей participant
    participants = relationship("ParticipantModel", back_populates="ks", uselist=True)


# Таблица "customer"
class CustomerModel(Base):
    __tablename__ = "customer"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    inn = Column(String(255), nullable=False)
    region_id = Column(Integer, ForeignKey("region.id"), nullable=False)

    # Связь с таблицей region
    region = relationship("RegionModel", back_populates="customers", uselist=False)
    # Связь с таблицей ks
    ks_list = relationship("KsModel", back_populates="customer", uselist=True)


# Таблица "cte"
class CteModel(Base):
    __tablename__ = "cte"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    cte_name = Column(String(1024), nullable=False)
    link = Column(String(255), nullable=True)
    kpgz_id = Column(Integer, ForeignKey("kpgz.id"), nullable=False)

    # Связь с таблицей kpgz
    kpgz = relationship("KpgzModel", back_populates="cte_list", uselist=False)
    # Связь с таблицей order
    orders = relationship("OrderModel", back_populates="cte", uselist=True)


# Таблица "order"
class OrderModel(Base):
    __tablename__ = "order"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    id_cte = Column(Integer, ForeignKey("cte.id"), nullable=False)
    id_ks = Column(Integer, ForeignKey("ks.id_ks"), nullable=False)
    count = Column(Numeric(18, 2), nullable=False)
    price = Column(Numeric(18, 2), nullable=False)
    oferta_start = Column(DateTime, nullable=False)
    oferta_end = Column(DateTime, nullable=False)
    oferta_price = Column(Numeric(18, 2), nullable=False)

    # Связь с таблицами cte и ks
    cte = relationship("CteModel", back_populates="orders", uselist=False)
    ks = relationship("KsModel", back_populates="orders", uselist=False)


# Таблица "supplier"
class SupplierModel(Base):
    __tablename__ = "supplier"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    inn = Column(String(255), nullable=False)
    region_id = Column(Integer, ForeignKey("region.id"), nullable=False)

    # Связь с таблицей region
    region = relationship("RegionModel", back_populates="suppliers", uselist=False)
    # Связь с таблицей ks (как победитель торгов)
    ks_list = relationship("KsModel", back_populates="supplier_winner", uselist=True)
    # Связь с таблицей participant
    participants = relationship(
        "ParticipantModel", back_populates="supplier", uselist=True
    )


# Таблица "participant"
class ParticipantModel(Base):
    __tablename__ = "participant"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    id_ks = Column(Integer, ForeignKey("ks.id_ks"), nullable=False)
    id_participant = Column(Integer, ForeignKey("supplier.id"), nullable=False)

    # Связи с таблицами ks и supplier
    ks = relationship("KsModel", back_populates="participants", uselist=False)
    supplier = relationship(
        "SupplierModel", back_populates="participants", uselist=False
    )


# Таблица "region"
class RegionModel(Base):
    __tablename__ = "region"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)

    # Связи с таблицами customer и supplier
    customers = relationship("CustomerModel", back_populates="region", uselist=True)
    suppliers = relationship("SupplierModel", back_populates="region", uselist=True)
