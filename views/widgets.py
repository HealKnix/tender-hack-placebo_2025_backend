from sqlalchemy import select

from database import SessionDep
from models import WidgetModel


async def get_all(db: SessionDep):
    query = select(WidgetModel)
    result = await db.execute(query)
    return result.scalars().all()


async def get_by_dashboard_id(db: SessionDep, dashboard_id: int):
    query = select(WidgetModel).where(WidgetModel.dashboard_id == dashboard_id)
    result = await db.execute(query)
    return result.scalars().all()


async def update_by_id(db: SessionDep, widget_id: int, widget: WidgetModel):
    pass
