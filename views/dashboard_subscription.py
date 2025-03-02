from sqlalchemy import select
import views.users as user_views
from database import SessionDep
from models import DashboardSubscriptionModel, UserModel


async def get_subscribers_by_dashboard_id(db: SessionDep, dashboard_id: int):
    query = select(DashboardSubscriptionModel).where(
        DashboardSubscriptionModel.dashboard_id == dashboard_id
    )
    result = (await db.execute(query)).scalars().all()

    subscribers = []
    for subscription in result:
        subscriber = await db.execute(
            select(UserModel).where(UserModel.id == subscription.user_id)
        )
        subscribers.append(subscriber)

    return subscribers
