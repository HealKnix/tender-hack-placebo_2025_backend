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


async def create(db: SessionDep, dashboard: DashboardModel):
    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)
    return dashboard


async def update_by_id(db: SessionDep, dashboard_id: int, dashboard: DashboardModel):
    pass


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
