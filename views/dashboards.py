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
import views.utils as util_views


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

    query = select(UserModel).where(UserModel.id == new_dashboard.owner_id)
    owner = (await db.execute(query)).scalar()

    query = select(DashboardSubscriptionModel).where(
        DashboardSubscriptionModel.dashboard_id == new_dashboard.id
    )
    subscribers = (await db.execute(query)).scalars().all()

    return {
        "id": new_dashboard.id,
        "title": new_dashboard.title,
        "owner": dashboard.owner_id,
        "properties": dashboard.properties,
        "metrics": [
            {
                "id": 0,
                **util_views.herfindahl_hirschman_rate(
                    dashboard.owner_id, "2022-01-01", "2025-01-01", db
                ),
            },
            {
                "id": 1,
                **util_views.metric_percentage_wins(
                    dashboard.owner_id, "2022-01-01", "2025-01-01", db
                ),
            },
            {
                "id": 2,
                **util_views.metric_avg_downgrade_cost(
                    dashboard.owner_id, "2022-01-01", "2025-01-01", db
                ),
            },
            {
                "id": 3,
                **util_views.metric_total_revenue(
                    dashboard.owner_id, "2022-01-01", "2025-01-01", db
                ),
            },
        ],
        "filters": [],
        "main_chart": util_views.revenue_trend_by_mounth(
            dashboard.owner_id, "2022-01-01", "2025-01-01", db
        ),
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

        result.append(
            {
                "id": dashboard.id,
                "title": dashboard.title,
                "owner": owner,
                "properties": properties,
                "metrics": [
                    {
                        "id": 0,
                        **util_views.herfindahl_hirschman_rate(
                            user_id, "2022-01-01", "2025-01-01", db
                        ),
                    },
                    {
                        "id": 1,
                        **util_views.metric_percentage_wins(
                            user_id, "2022-01-01", "2025-01-01", db
                        ),
                    },
                    {
                        "id": 2,
                        **util_views.metric_avg_downgrade_cost(
                            user_id, "2022-01-01", "2025-01-01", db
                        ),
                    },
                    {
                        "id": 3,
                        **util_views.metric_total_revenue(
                            user_id, "2022-01-01", "2025-01-01", db
                        ),
                    },
                ],
                "subscribers": subscribers,
                "main_chart": util_views.revenue_trend_by_mounth(
                    user_id, "2022-01-01", "2025-01-01", db
                ),
            }
        )

    return result
