from database import SessionDep
from models import DashboardModel
from sqlalchemy import select


async def get_by_id(db: SessionDep, dashboard_id: int):
    query = select(DashboardModel).where(DashboardModel.id == dashboard_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_all(db: SessionDep):
    query = select(DashboardModel)
    result = await db.execute(query)
    return result.scalars().all()


async def create(db: SessionDep, dashboard):
    new_dashboard = DashboardModel(**dashboard)

    for table, column in dashboard.properties:
        new_dashboard.properties.append(
            dashboard_id=new_dashboard.id,
            table_name=table,
            column_name=column,
        )

    db.add(new_dashboard)
    await db.commit()
    await db.refresh(new_dashboard)

    return dashboard


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
    result = await db.execute(query)
    return result.scalars().all()
