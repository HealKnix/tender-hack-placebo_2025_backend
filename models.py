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
    full_name = Column(String, unique=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

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
    owner = relationship("UserModel", back_populates="dashboards")
    # one-to-many relationship with Reports
    reports = relationship(
        "ReportModel", back_populates="dashboard", cascade="all, delete-orphan"
    )
    # one-to-many relationship with Widgets
    widgets = relationship("WidgetModel", back_populates="dashboard")


class WidgetModel(Base):
    __tablename__ = "widgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, unique=True)
    description = Column(Text)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # relationship with Dashboard
    dashboard = relationship("DashboardModel", back_populates="widgets")


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
    dashboard = relationship("DashboardModel", back_populates="reports")


# ##############################################################


class Kpgz(Base):
    __tablename__ = "kpgz"
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    code_kpgz = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)

    # Связь с таблицей cte
    ctes = relationship("Cte", back_populates="kpgz")


class Ks(Base):
    __tablename__ = "ks"
    id_ks = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    link = Column(String(255), nullable=False)
    start_ks = Column(DateTime, nullable=False)
    end_ks = Column(DateTime, nullable=False)
    start_price = Column(Numeric(18, 2), nullable=False)
    end_price = Column(Numeric(18, 2), nullable=False)
    oferta_price = Column(Numeric(18, 2), nullable=False)
    oferta_start = Column(DateTime, nullable=False)
    oferta_end = Column(DateTime, nullable=False)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Связи с таблицами customer и suppliers
    customer = relationship("Customer", back_populates="ks")
    winner = relationship("Supplier", back_populates="ks_won")
    participants = relationship("Participant", back_populates="ks")
    orders = relationship("Order", back_populates="ks")


class Customer(Base):
    __tablename__ = "customer"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    inn = Column(String(255), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)

    # Связь с регионом и тендерами (ks)
    region = relationship("Region", back_populates="customers")
    ks = relationship("Ks", back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    inn = Column(String(255), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)

    # Связь с регионом, выигранными тендерами и участием в торгах
    region = relationship("Region", back_populates="suppliers")
    ks_won = relationship("Ks", back_populates="winner")
    participants = relationship("Participant", back_populates="supplier")


class Cte(Base):
    __tablename__ = "cte"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    link = Column(String(255), nullable=False)
    price = Column(Numeric(18, 2), nullable=False)
    kpgz_id = Column(Integer, ForeignKey("kpgz.id"), nullable=False)

    # Связь с kpgz и заказами
    kpgz = relationship("Kpgz", back_populates="ctes")
    orders = relationship("Order", back_populates="cte")


class Participant(Base):
    __tablename__ = "participants"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    id_ks = Column(Integer, ForeignKey("ks.id_ks"), nullable=False)
    id_participant = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Связь с тендером (Ks) и поставщиком
    ks = relationship("Ks", back_populates="participants")
    supplier = relationship("Supplier", back_populates="participants")


class Region(Base):
    __tablename__ = "regions"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)

    # Связь с клиентами и поставщиками
    customers = relationship("Customer", back_populates="region")
    suppliers = relationship("Supplier", back_populates="region")


class Order(Base):
    __tablename__ = "order"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    id_cte = Column(Integer, ForeignKey("cte.id"), nullable=False)
    id_ks = Column(Integer, ForeignKey("ks.id_ks"), nullable=False)
    count = Column(Integer, nullable=False)

    # Связь с cte и тендером (Ks)
    cte = relationship("Cte", back_populates="orders")
    ks = relationship("Ks", back_populates="orders")
