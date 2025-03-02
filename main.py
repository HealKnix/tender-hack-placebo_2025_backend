from datetime import datetime
from sqlalchemy import MetaData, select, text
import uvicorn
import aiohttp

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from database import SessionDep, engine

from models import SupplierModel, DashboardSubscriptionModel
import schemas.users as UserSchema
import schemas.dashboards as DashboardSchema
import schemas.deepseek as DeepseekSchema
import schemas.other as OtherSchema

import views.users as user_views
import views.dashboards as dashboard_views
import views.widgets as widget_views
import views.utils as util_views

import views.auth as auth_views

app = FastAPI()

# CORS allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# ####################################################################


@app.post("/api/register", response_model=UserSchema.Read)
async def register(user: UserSchema.Create, db: SessionDep):
    db_user = await user_views.get_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Почта уже зарегистрирована")

    new_user = await user_views.create(db, user)
    new_user.supplier_id = new_user.id
    new_user.password = auth_views.get_password_hash(user.password)
    new_user.token = auth_views.create_access_token(data={"sub": new_user.id})

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@app.post("/api/login")
async def login(form_data: UserSchema.Login, db: SessionDep):
    user = await user_views.get_by_email(db, email=form_data.email)
    if not user:
        raise HTTPException(
            status_code=400, detail="Неверное имя пользователя или пароль"
        )
    if not auth_views.authenticate_user(form_data.password, user.password):
        raise HTTPException(
            status_code=400, detail="Неверное имя пользователя или пароль"
        )
    # access_token = create_access_token(data={"sub": user.full_name})
    return {"access_token": user.token, "token_type": "bearer"}


@app.post("/api/auth")
async def auth(form_data: UserSchema.Auth, db: SessionDep):
    user = await user_views.get_by_token(db, token=form_data.token)
    if not user:
        raise HTTPException(status_code=400, detail="У вас нет доступа к этой странице")

    return {
        "id": user.id,
        "supplier_id": user.supplier_id,
        "full_name": user.full_name,
        "email": user.email,
    }


# ####################################################################


@app.get("/api/users", response_model=list[UserSchema.Read], tags=["Users"])
async def read_users(db: SessionDep, skip: int = 0, limit: int = 100):
    users = await user_views.get_all(db, skip=skip, limit=limit)
    return users


@app.get("/api/users/{user_id}", response_model=UserSchema.Read, tags=["Users"])
async def read_user(user_id: int, db: SessionDep):
    user = await user_views.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.put("/api/users/{user_id}", response_model=UserSchema.Read, tags=["Users"])
async def update_user_endpoint(
    user_id: int, user_update: UserSchema.Update, db: SessionDep
):
    user = await user_views.update_by_id(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.delete("/api/users/{user_id}", response_model=UserSchema.Read, tags=["Users"])
async def delete_user_endpoint(user_id: int, db: SessionDep):
    result = await user_views.delete_by_id(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"detail": "Пользователь удалён"}


# ####################################################################


@app.get("/api/suppliers/{inn}", tags=["Suppliers"])
async def get_supplier_by_inn(inn: str, db: SessionDep):
    res = await db.execute(select(SupplierModel).where(SupplierModel.inn == inn))

    return res.scalar()


# ####################################################################


@app.get("/api/dashboards", tags=["Dashboard"])
async def get_dashboards(db: SessionDep):
    return await dashboard_views.get_all(db)


@app.post("/api/dashboards", tags=["Dashboard"])
async def create_dashboard(dashboard: DashboardSchema.Create, db: SessionDep):
    return await dashboard_views.create(db, dashboard)


@app.patch("/api/dashboards/{dashboard_id}", tags=["Dashboard"])
async def update_dashboards_by_id(dashboard_id: int, dashboard, db: SessionDep):
    return await dashboard_views.update_by_id(db, dashboard_id, dashboard)


@app.get("/api/dashboards/owner/{owner_id}", tags=["Dashboard"])
async def get_dashboards_by_owner_id(owner_id: int, db: SessionDep):
    return await dashboard_views.get_by_owner_id(db, owner_id)


@app.get("/api/dashboards_subsribers", tags=["Subscribers"])
async def get_subscribers(db: SessionDep):
    res = await db.execute(select(DashboardSubscriptionModel))
    return res.scalars().all()


@app.patch("/api/dashboards_subsribers", tags=["Subscribers"])
async def update_subscribers(db: SessionDep):
    schedule = DashboardSubscriptionModel(
        dashboard_id=1,
        user_id=3,
        schedule_time=datetime.now(),
        schedule_type="daily",
    )

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    return schedule


# ####################################################################


@app.get("/api/widgets", tags=["Widgets"])
async def get_widgets(db: SessionDep):
    return await widget_views.get_all(db)


@app.get("/api/widgets/dashboard/{dashboard_id}", tags=["Widgets"])
async def get_widgets_by_dashboard_id(dashboard_id: int, db: SessionDep):
    return await widget_views.get_by_dashboard_id(db, dashboard_id)


# ####################################################################


@app.get(
    "/api/utils/herfindahl_hirschman_index/{supplier_id}/{start_date}/{end_date}",
    tags=["Utils/Metrics"],
)
async def get_herfindahl_hirschman_rate(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    return await util_views.herfindahl_hirschman_rate(
        supplier_id, start_date, end_date, db
    )


@app.get(
    "/api/utils/metric_percentage_wins/{supplier_id}/{start_date}/{end_date}",
    tags=["Utils/Metrics"],
)
async def get_metric_percentage_wins(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    return await util_views.metric_percentage_wins(
        supplier_id, start_date, end_date, db
    )


@app.get(
    "/api/utils/metric_avg_downgrade_cost/{supplier_id}/{start_date}/{end_date}",
    tags=["Utils/Metrics"],
)
async def get_metric_avg_downgrade_cost(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    return await util_views.metric_avg_downgrade_cost(
        supplier_id, start_date, end_date, db
    )


@app.get(
    "/api/utils/metric_total_revenue/{supplier_id}/{start_date}/{end_date}",
    tags=["Utils/Metrics"],
)
async def get_metric_total_revenue(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    return await util_views.metric_total_revenue(supplier_id, start_date, end_date, db)


@app.get(
    "/api/utils/revenue_by_regions/{supplier_id}/{start_date}/{end_date}",
    tags=["Utils/Charts"],
)
async def get_revenue_by_regions(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    return await util_views.revenue_by_regions(supplier_id, start_date, end_date, db)


@app.get(
    "/api/utils/revenue_by_kpgz_category_by_region_id/{supplier_id}/{start_date}/{end_date}/{region_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_revenue_by_kpgz_category_by_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    return await util_views.revenue_by_kpgz_category_by_region_id(
        supplier_id, start_date, end_date, region_id, limit, db
    )


@app.get(
    "/api/utils/revenue_by_kpgz_category_by_kpgz_category_id/{supplier_id}/{start_date}/{end_date}/{kpgz_category_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_revenue_by_kpgz_category_by_kpgz_category_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    limit: int,
    db: SessionDep,
):
    return await util_views.revenue_by_kpgz_category_by_kpgz_category_id(
        supplier_id, start_date, end_date, kpgz_category_id, limit, db
    )


@app.get(
    "/api/utils/revenue_by_kpgz_category_by_kpgz_category_id_and_region_id/{supplier_id}/{start_date}/{end_date}/{kpgz_category_id}/{region_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_revenue_by_kpgz_category_by_kpgz_category_id_and_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    return await util_views.revenue_by_kpgz_category_by_kpgz_category_id_and_region_id(
        supplier_id, start_date, end_date, kpgz_category_id, region_id, limit, db
    )


@app.get(
    "/api/utils/total_revenue_by_kpgz_category/{start_date}/{end_date}/{limit}",
    tags=["Utils/Charts"],
)
async def get_total_revenue_by_kpgz_category(
    start_date: str,
    end_date: str,
    limit: int,
    db: SessionDep,
):
    return await util_views.total_revenue_by_kpgz_category(
        start_date, end_date, limit, db
    )


@app.get(
    "/api/utils/total_revenue_by_kpgz_category_by_region_id/{start_date}/{end_date}/{region_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_total_revenue_by_kpgz_category_by_region_id(
    start_date: str,
    end_date: str,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    return await util_views.total_revenue_by_kpgz_category_by_region_id(
        start_date, end_date, region_id, limit, db
    )


@app.get(
    "/api/utils/total_revenue_by_regions_by_kpgz_category_id/{start_date}/{end_date}/{kpgz_category_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_total_revenue_by_regions_by_kpgz_category_id(
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    limit: int,
    db: SessionDep,
):
    return await util_views.total_revenue_by_regions_by_kpgz_category_id(
        start_date, end_date, kpgz_category_id, limit, db
    )


@app.get(
    "/api/utils/total_revenue_by_regions_by_kpgz_category_and_region_id/{start_date}/{end_date}/{kpgz_category_id}/{region_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_total_revenue_by_regions_by_kpgz_category_and_region_id(
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    return await util_views.total_revenue_by_regions_by_kpgz_category_and_region_id(
        start_date, end_date, kpgz_category_id, region_id, limit, db
    )


@app.get(
    "/api/utils/revenue_trend_by_mounth/{supplier_id}/{start_date}/{end_date}",
    tags=["Utils/Charts"],
)
async def get_revenue_trend_by_mounth(
    supplier_id: int,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    return await util_views.revenue_trend_by_mounth(
        supplier_id, start_date, end_date, db
    )


@app.get(
    "/api/utils/revenue_trend_by_weeks/{supplier_id}/{start_date}/{end_date}",
    tags=["Utils/Charts"],
)
async def get_revenue_trend_by_weeks(
    supplier_id: int,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    return await util_views.revenue_trend_by_weeks(
        supplier_id, start_date, end_date, db
    )


@app.get(
    "/api/utils/revenue_trend_by_mounth_by_region_id/{supplier_id}/{start_date}/{end_date}/{region_id}",
    tags=["Utils/Charts"],
)
async def get_revenue_trend_by_mounth_by_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    region_id: int,
    db: SessionDep,
):
    return await util_views.revenue_trend_by_mounth_by_region_id(
        supplier_id, start_date, end_date, region_id, db
    )


@app.get(
    "/api/utils/revenue_trend_by_weeks_by_region_id/{supplier_id}/{start_date}/{end_date}/{region_id}",
    tags=["Utils/Charts"],
)
async def get_revenue_trend_by_weeks_by_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    region_id: int,
    db: SessionDep,
):
    return await util_views.revenue_trend_by_weeks_by_region_id(
        supplier_id, start_date, end_date, region_id, db
    )


@app.get(
    "/api/utils/revenue_trend_by_mounth_by_kpgz_category_id/{supplier_id}/{start_date}/{end_date}/{kpgz_category_id}",
    tags=["Utils/Charts"],
)
async def get_revenue_trend_by_mounth_by_kpgz_category_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    db: SessionDep,
):
    return await util_views.revenue_trend_by_mounth_by_kpgz_category_id(
        supplier_id, start_date, end_date, kpgz_category_id, db
    )


@app.get(
    "/api/utils/revenue_trend_by_weeks_by_kpgz_category_id/{supplier_id}/{start_date}/{end_date}/{kpgz_category_id}",
    tags=["Utils/Charts"],
)
async def get_revenue_trend_by_weeks_by_kpgz_category_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    db: SessionDep,
):
    return await util_views.revenue_trend_by_weeks_by_kpgz_category_id(
        supplier_id, start_date, end_date, kpgz_category_id, db
    )


@app.get(
    "/api/utils/revenue_trend_by_mounth_by_kpgz_category_id_and_region_id/{supplier_id}/{start_date}/{end_date}/{kpgz_category_id}/{region_id}",
    tags=["Utils/Charts"],
)
async def get_revenue_trend_by_mounth_by_kpgz_category_id_and_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id: int,
    db: SessionDep,
):
    return await util_views.revenue_trend_by_mounth_by_kpgz_category_id_and_region_id(
        supplier_id, start_date, end_date, kpgz_category_id, region_id, db
    )


@app.get(
    "/api/utils/revenue_trend_by_weeks_by_kpgz_category_id_and_region_id/{supplier_id}/{start_date}/{end_date}/{kpgz_category_id}/{region_id}",
    tags=["Utils/Charts"],
)
async def get_revenue_trend_by_weeks_by_kpgz_category_id_and_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id: int,
    db: SessionDep,
):
    return await util_views.revenue_trend_by_weeks_by_kpgz_category_id_and_region_id(
        supplier_id, start_date, end_date, kpgz_category_id, region_id, db
    )


@app.get(
    "/api/utils/revenue_by_customers/{supplier_id}/{start_date}/{end_date}/{limit}",
    tags=["Utils/Charts"],
)
async def get_revenue_by_customers(
    supplier_id: int,
    start_date: str,
    end_date: str,
    limit: int,
    db: SessionDep,
):
    return await util_views.revenue_by_customers(
        supplier_id, start_date, end_date, limit, db
    )


@app.get(
    "/api/utils/revenue_by_customers_by_region_id/{supplier_id}/{start_date}/{end_date}/{region_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_revenue_by_customers_by_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    return await util_views.revenue_by_customers_by_region_id(
        supplier_id, start_date, end_date, region_id, limit, db
    )


@app.get(
    "/api/utils/revenue_by_customers_by_kpgz_id/{supplier_id}/{start_date}/{end_date}/{kpgz_category_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_revenue_by_customers_by_kpgz_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    limit: int,
    db: SessionDep,
):
    return await util_views.revenue_by_customers_by_kpgz_id(
        supplier_id, start_date, end_date, kpgz_category_id, limit, db
    )


@app.get(
    "/api/utils/revenue_by_customers_by_region_id_and_kpgz_category_id/{supplier_id}/{start_date}/{end_date}/{kpgz_category_id}/{region_id}/{limit}",
    tags=["Utils/Charts"],
)
async def get_revenue_by_customers_by_region_id_and_kpgz_category_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id,
    limit: int,
    db: SessionDep,
):
    return await util_views.revenue_by_customers_by_region_id_and_kpgz_category_id(
        supplier_id, start_date, end_date, kpgz_category_id, region_id, limit, db
    )


# ####################################################################


@app.post("/api/deepseek", response_model=DeepseekSchema.Message, tags=["DeepSeek"])
async def deepseek(secret_key: str, deep: DeepseekSchema.Promt):
    if not auth_views.pwd_context.verify(
        secret_key,
        "$5$rounds=535000$U/n.eV30oSlzqJ7.$rRhZQqSHGhH9HQHOPGQco1peH7iQUM4Yh6t4ibN/uZ8",
    ):
        raise HTTPException(status_code=401, detail="Incorrect secret key")

    url = "http://localhost:11434/api/generate/"

    json_body = {
        "model": "deepseek-r1:32b",
        "prompt": deep.prompt,
        "stream": False,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_body) as response:
            if response.status == 200:
                data = await response.json()
                return {"message": data["response"]}
            else:
                raise HTTPException(
                    status_code=response.status, detail=await response.text()
                )


@app.get("/api/download/{file_name}", tags=["Download"])
async def download_file(file_name: str):
    return FileResponse(f"reports/{file_name}")


# ###################################################################


def get_table_names(sync_conn):
    metadata = MetaData()
    # Делаем рефлексию, чтобы получить список таблиц
    metadata.reflect(bind=sync_conn)
    return metadata.tables


@app.get("/api/properties", tags=["Database"])
async def get_properties():
    async with engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)
        return [{table: tables.get(table).columns.keys()} for table in tables.keys()][
            1:
        ]


@app.get("/api/tables", tags=["Database"], response_model=list[str])
async def get_tables():
    async with engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)
    return tables.keys()


@app.get(
    "/api/tables/{table_name}/columns", tags=["Database"], response_model=list[str]
)
async def get_table_columns(table_name: str):
    async with engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)
        if table_name not in tables:
            raise HTTPException(
                status_code=404, detail=f"Таблица '{table_name}' не найдена"
            )

    columns = tables[table_name].columns.keys()

    return columns


@app.get("/api/tables/{table_name}/columns/{column_name}/{func}", tags=["Database"])
async def get_table_column_data(
    table_name: str, column_names: str, func: str | None = None
):
    async with engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)
        if table_name not in tables:
            raise HTTPException(
                status_code=404, detail=f"Таблица '{table_name}' не найдена"
            )
        column_name_list = [x.strip() for x in column_names.split(",")]
        for column_name in column_name_list:
            if column_name not in tables[table_name].columns:
                raise HTTPException(
                    status_code=404,
                    detail=f"Столбец '{column_name}' не найден в таблице '{table_name}'",
                )

        if not func:
            result = await conn.execute(
                text(f"SELECT {column_names} FROM {table_name}")
            )
        else:
            result = await conn.execute(
                text(f"SELECT {func}({column_names}) FROM {table_name} LIMIT 1")
            )

            return result.scalar()

    # Преобразуем каждую строку в словарь с именем колонки в качестве ключа
    items = [
        {column_name_list[i]: row for i, row in enumerate(column)} for column in result
    ]

    return items
