from datetime import datetime, timedelta
import asyncio
from sqlalchemy import select, update
from database import engine
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from models import DashboardSubscriptionModel, UserModel
from send_email import send_email


async def get_schedules_from_db():
    async with engine.connect() as conn:
        schedules = await conn.execute(
            select(DashboardSubscriptionModel).order_by(
                DashboardSubscriptionModel.schedule_time
            )
        )

    return schedules.fetchall()


async def update_schedule_in_db(schedule, duration_time):
    async with engine.connect() as conn:
        await conn.execute(
            update(DashboardSubscriptionModel)
            .where(DashboardSubscriptionModel.id == schedule.id)
            .values(schedule_time=datetime.now() + duration_time)
        )
        await conn.commit()


async def schedule_run(schedule: DashboardSubscriptionModel):
    async with engine.connect() as conn:
        user = await conn.execute(
            select(UserModel).where(UserModel.id == schedule.user_id)
        )
    user = user.fetchone()
    print(f"Отправка письма для расписания: {schedule.id} на почту {user.email}")
    send_email(user.email)


async def start_scheduler():
    scheduler = AsyncIOScheduler()

    async def check_and_send_emails():
        schedules: list[DashboardSubscriptionModel] = await get_schedules_from_db()

        for schedule in schedules:
            if schedule.schedule_time <= datetime.now():
                await schedule_run(schedule)

                if schedule.schedule_type == "daily":
                    duration_time = timedelta(days=1)
                elif schedule.schedule_type == "weekly":
                    duration_time = timedelta(weeks=1)
                elif schedule.schedule_type == "monthly":
                    duration_time = timedelta(days=30)

                await update_schedule_in_db(schedule, duration_time)

    # Добавляем параметры для контроля параллельного выполнения
    scheduler.add_job(
        check_and_send_emails,
        "interval",
        seconds=5,
        max_instances=1,  # Максимум 1 параллельное выполнение
        coalesce=True,  # Объединять пропущенные запуски в один
        misfire_grace_time=None,  # Выполнять пропущенные задачи без ограничения по времени
    )

    scheduler.start()

    try:
        await asyncio.get_event_loop().create_future()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(start_scheduler())
