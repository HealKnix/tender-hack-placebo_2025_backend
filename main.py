from sqlalchemy import MetaData, text
import uvicorn
import aiohttp

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from database import SessionDep, engine
from schemas import (
    UserCreateSchema,
    UserReadSchema,
    UserUpdateSchema,
    UserLoginSchema,
    UserAuthSchema,
    DeepSeekSchema,
    DeepSeekPromtSchema,
)
import views.users as user_views
import views.dashboards as dashboard_views
import views.widgets as widget_views
import views.utils as util_views
from auth import (
    pwd_context,
    get_password_hash,
    authenticate_user,
    create_access_token,
)

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


@app.post("/api/register", response_model=UserReadSchema)
async def register(user: UserCreateSchema, db: SessionDep):
    db_user = await user_views.get_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Почта уже зарегистрирована")

    new_user = await user_views.create(db, user)
    new_user.password = get_password_hash(user.password)
    new_user.token = create_access_token(data={"sub": new_user.id})

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@app.post("/api/login")
async def login(form_data: UserLoginSchema, db: SessionDep):
    user = await user_views.get_by_email(db, email=form_data.email)
    if not user:
        raise HTTPException(
            status_code=400, detail="Неверное имя пользователя или пароль"
        )
    if not authenticate_user(form_data.password, user.password):
        raise HTTPException(
            status_code=400, detail="Неверное имя пользователя или пароль"
        )
    # access_token = create_access_token(data={"sub": user.full_name})
    return {"access_token": user.token, "token_type": "bearer"}


@app.post("/api/auth")
async def auth(form_data: UserAuthSchema, db: SessionDep):
    user = await user_views.get_by_token(db, token=form_data.token)
    if not user:
        raise HTTPException(status_code=400, detail="У вас нет доступа к этой странице")

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
    }


# ####################################################################


@app.get("/api/users", response_model=list[UserReadSchema], tags=["Users"])
async def read_users(db: SessionDep, skip: int = 0, limit: int = 100):
    users = await user_views.get_all(db, skip=skip, limit=limit)
    return users


@app.get("/api/users/{user_id}", response_model=UserReadSchema, tags=["Users"])
async def read_user(user_id: int, db: SessionDep):
    user = await user_views.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.put("/api/users/{user_id}", response_model=UserReadSchema, tags=["Users"])
async def update_user_endpoint(
    user_id: int, user_update: UserUpdateSchema, db: SessionDep
):
    user = await user_views.update_by_id(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.delete("/api/users/{user_id}", response_model=UserReadSchema, tags=["Users"])
async def delete_user_endpoint(user_id: int, db: SessionDep):
    result = await user_views.delete_by_id(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"detail": "Пользователь удалён"}


# ####################################################################


@app.get("/api/dashbboards", tags=["Dashboard"])
async def get_dashboards(db: SessionDep):
    return await dashboard_views.get_all(db)


@app.get("/api/dashbboards/user/{user_id}", tags=["Dashboard"])
async def get_dashboards(user_id: int, db: SessionDep):
    return await dashboard_views.get_by_user_id(db, user_id)


# ####################################################################


@app.get("/api/widgets", tags=["Widgets"])
async def get_widgets(db: SessionDep):
    return await widget_views.get_all(db)


@app.get("/api/widgets/dashboard/{dashboard_id}", tags=["Widgets"])
async def get_widgets_by_dashboard_id(dashboard_id: int, db: SessionDep):
    return await widget_views.get_by_dashboard_id(db, dashboard_id)


# ####################################################################


@app.get("/api/utils/herfindahl_hirschman_index/{supplier_id}", tags=["Utils"])
async def get_herfindahl_hirschman_rate(supplier_id: int, db: SessionDep):
    return await util_views.herfindahl_hirschman_rate(supplier_id, db)


@app.get("/api/utils/suppliers_success_rate", tags=["Utils"])
async def get_suppliers_success_rate(db: SessionDep):
    return await util_views.suppliers_success_rate(db)


@app.get("/api/utils/price_reduction_by_kpgz_categories_rate", tags=["Utils"])
async def get_price_reduction_by_kpgz_categories_rate(db: SessionDep):
    return await util_views.price_reduction_by_kpgz_categories_rate(db)


# ####################################################################


@app.post("/api/deepseek", response_model=DeepSeekSchema, tags=["DeepSeek"])
async def deepseek(secret_key: str, deep: DeepSeekPromtSchema):
    if not pwd_context.verify(
        secret_key,
        "$5$rounds=535000$U/n.eV30oSlzqJ7.$rRhZQqSHGhH9HQHOPGQco1peH7iQUM4Yh6t4ibN/uZ8",
    ):
        raise HTTPException(status_code=401, detail="Incorrect secret key")

    url = "http://localhost/api/generate/"

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


@app.get("/api/tables/{table_name}/columns/{column_name}", tags=["Database"])
async def get_table_column_data(table_name: str, column_names: str):
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

        result = await conn.execute(text(f"SELECT {column_names} FROM {table_name}"))

    # Преобразуем каждую строку в словарь с именем колонки в качестве ключа
    items = [
        {column_name_list[i]: row for i, row in enumerate(column)} for column in result
    ]

    return items
