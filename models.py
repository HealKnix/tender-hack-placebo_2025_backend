from sqlalchemy import (
    Boolean,
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
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    token = Column(String, unique=True)

    # Связь с таблицей suppliers
    supplier = relationship("SupplierModel", back_populates="user", uselist=False)
    # one-to-many relationship with Dashboards
    dashboards = relationship("DashboardModel", back_populates="owner", uselist=True)
    # one-to-many relationship with Dashboards
    dashboard_subscriptions = relationship(
        "DashboardSubscriptionModel", back_populates="users", uselist=True
    )


class DashboardModel(Base):
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, unique=True)
    properties = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    filters = relationship(
        "DashboardFilterModel", back_populates="dashboard", uselist=True
    )
    properties = relationship(
        "DashboardPropetryModel", back_populates="dashboard", uselist=True
    )
    metrics = relationship(
        "DashboardMetricModel", back_populates="dashboard", uselist=True
    )
    subscribers = relationship(
        "DashboardSubscriptionModel", back_populates="dashboard", uselist=True
    )
    # relationship with User
    owner = relationship(
        "UserModel", back_populates="dashboards", foreign_keys=[owner_id], uselist=False
    )
    # one-to-many relationship with Reports
    reports = relationship("ReportModel", back_populates="dashboard", uselist=True)
    # one-to-many relationship with Widgets
    widgets = relationship("WidgetModel", back_populates="dashboard", uselist=True)


class DashboardFilterModel(Base):
    __tablename__ = "dashboard_filters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    name = Column(String(255))
    value = Column(String(255))

    dashboard = relationship(
        "DashboardModel",
        back_populates="filters",
        foreign_keys=[dashboard_id],
        uselist=False,
    )


class DashboardPropetryModel(Base):
    __tablename__ = "dashboard_properties"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    table_name = Column(String(255))
    column_name = Column(String(255))
    type = Column(String(255))

    dashboard = relationship(
        "DashboardModel",
        back_populates="properties",
        foreign_keys=[dashboard_id],
        uselist=False,
    )


class DashboardMetricModel(Base):
    __tablename__ = "dashboard_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    name = Column(String(255))
    value = Column(Numeric(18, 2))
    unit = Column(String(255))

    dashboard = relationship(
        "DashboardModel",
        back_populates="metrics",
        foreign_keys=[dashboard_id],
        uselist=False,
    )


class DashboardSubscriptionModel(Base):
    __tablename__ = "dashboard_subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    schedule_day = Column(Integer)

    dashboard = relationship(
        "DashboardModel",
        back_populates="subscribers",
        foreign_keys=[dashboard_id],
        uselist=False,
    )
    users = relationship(
        "UserModel",
        back_populates="dashboard_subscriptions",
        foreign_keys=[user_id],
        uselist=True,
    )


class WidgetModel(Base):
    __tablename__ = "widgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(String(255))
    index = Column(Integer)
    data_switch = Column(Boolean)
    smooth = Column(Boolean)
    min = Column(Numeric(18, 2))
    max = Column(Numeric(18, 2))
    title = Column(String)
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


class KpgzCategory(Base):
    __tablename__ = "kpgz_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(255), nullable=False)

    # Отношение с таблицей kpgz_detailed
    details = relationship("KpgzDetailed", back_populates="category", uselist=True)


class KpgzDetailed(Base):
    __tablename__ = "kpgz_details"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    code = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("kpgz_categories.id"), nullable=False)

    # Связь с категорией
    category = relationship("KpgzCategory", back_populates="details", uselist=False)
    # Отношение с таблицей cte
    cte_list = relationship("CteModel", back_populates="kpgz_detail", uselist=True)


# Таблица "ks"
class KsModel(Base):
    __tablename__ = "ks"
    id_ks = Column(Integer, primary_key=True, nullable=False)
    link = Column(String(255), nullable=False)
    start_ks = Column(DateTime, nullable=False)
    end_ks = Column(DateTime, nullable=False)
    start_price = Column(Numeric(18, 2), nullable=False)
    end_price = Column(Numeric(18, 2), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

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
    __tablename__ = "customers"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    inn = Column(String(255), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)

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
    kpgz_id = Column(Integer, ForeignKey("kpgz_details.id"), nullable=False)

    # Связь с таблицей kpgz
    kpgz_detail = relationship("KpgzDetailed", back_populates="cte_list", uselist=False)
    # Связь с таблицей order
    orders = relationship("OrderModel", back_populates="cte", uselist=True)


# Таблица "order"
class OrderModel(Base):
    __tablename__ = "orders"
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
    __tablename__ = "suppliers"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    inn = Column(String(255), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)

    user = relationship("UserModel", back_populates="supplier", uselist=False)
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
    __tablename__ = "participants"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    id_ks = Column(Integer, ForeignKey("ks.id_ks"), nullable=False)
    id_participant = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Связи с таблицами ks и supplier
    ks = relationship("KsModel", back_populates="participants", uselist=False)
    supplier = relationship(
        "SupplierModel", back_populates="participants", uselist=False
    )


# Таблица "region"
class RegionModel(Base):
    __tablename__ = "regions"
    id = Column(
        Integer, primary_key=True, autoincrement=True, unique=True, nullable=False
    )
    name = Column(String(255), nullable=False)

    # Связи с таблицами customer и supplier
    customers = relationship("CustomerModel", back_populates="region", uselist=True)
    suppliers = relationship("SupplierModel", back_populates="region", uselist=True)
