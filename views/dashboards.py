from database import SessionDep
from models import (
    DashboardModel,
    DashboardPropertyModel,
    DashboardMetricModel,
    DashboardFilterModel,
    DashboardSubscriptionModel,
    UserModel,
)
from sqlalchemy import select
import schemas.dashboards as DashboardSchema
import views.users as user_views
import views.dashboard_subscription as dashboard_subscription_views


async def get_by_id(db: SessionDep, dashboard_id: int):
    query = select(DashboardModel).where(DashboardModel.id == dashboard_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_all(db: SessionDep):
    query = select(DashboardModel)
    result = await db.execute(query)
    return result.scalars().all()


async def create(db: SessionDep, dashboard: DashboardSchema.Create):
    new_dashboard = DashboardModel(
        title=dashboard.title,
        owner_id=dashboard.owner_id,
    )

    db.add(new_dashboard)

    await db.commit()
    await db.refresh(new_dashboard)

    for row in dashboard.properties:
        temp_str = row.split(".")
        property = DashboardPropertyModel(
            dashboard_id=new_dashboard.id,
            table_name=temp_str[0],
            column_name=temp_str[1],
        )
        db.add(property)
        await db.commit()
        await db.refresh(property)

    onwer = await user_views.get_by_id(db, dashboard.owner_id)

    return {
        "id": new_dashboard.id,
        "title": new_dashboard.title,
        "owner": onwer,
        "properties": dashboard.properties,
        "metrics": [],
        "filters": [],
    }


async def update_by_id(db: SessionDep, dashboard_id: int, dashboard):
    dashboard = await get_by_id(db, dashboard_id)
    if not dashboard:
        return None
    for field, value in dashboard.items():
        setattr(dashboard, field, value)
    await db.commit()
    await db.refresh(dashboard)
    return dashboard


async def delete_by_id(db: SessionDep, dashboard_id: int):
    dashboard = await get_by_id(db, dashboard_id)
    if not dashboard:
        return None
    await db.delete(dashboard)
    await db.commit()
    return dashboard


async def get_by_owner_id(db: SessionDep, user_id: int):
    query = select(DashboardModel).where(DashboardModel.owner_id == user_id)
    dashboards = (await db.execute(query)).scalars().all()

    result = []
    for dashboard in dashboards:
        query = select(DashboardPropertyModel).where(
            DashboardPropertyModel.dashboard_id == dashboard.id
        )
        properties = (await db.execute(query)).scalars().all()

        query = select(UserModel).where(UserModel.id == dashboard.owner_id)
        owner = (await db.execute(query)).scalar()

        query = select(DashboardSubscriptionModel).where(
            DashboardSubscriptionModel.dashboard_id == dashboard.id
        )
        subscribers = (await db.execute(query)).scalars().all()

        query = select(DashboardMetricModel).where(
            DashboardMetricModel.dashboard_id == dashboard.id
        )
        metrics = (await db.execute(query)).scalars().all()

        query = select(DashboardFilterModel).where(
            DashboardFilterModel.dashboard_id == dashboard.id
        )
        filters = (await db.execute(query)).scalars().all()

        result.append(
            {
                "id": dashboard.id,
                "title": dashboard.title,
                "owner": owner,
                "properties": properties,
                "metrics": metrics,
                "filters": filters,
                "subscribers": subscribers,
            }
        )

    return result
