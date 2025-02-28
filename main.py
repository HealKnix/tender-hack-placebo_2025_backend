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
    DeepSeekSchema,
    DeepSeekPromtSchema,
)
from views import (
    create_user,
    get_user_by_email,
    get_user,
    get_users,
    update_user,
    delete_user,
)
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


@app.post("/api/register", response_model=UserReadSchema)
async def register(user: UserCreateSchema, db: SessionDep):
    db_user = await get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
    user.password = get_password_hash(user.password)
    new_user = await create_user(db, user)
    return new_user


@app.post("/api/token")
async def login(form_data: UserLoginSchema, db: SessionDep):
    user = await get_user_by_email(db, email=form_data.email)
    if not user:
        raise HTTPException(
            status_code=400, detail="Неверное имя пользователя или пароль"
        )
    if not authenticate_user(form_data.password, user.password):
        raise HTTPException(
            status_code=400, detail="Неверное имя пользователя или пароль"
        )
    access_token = create_access_token(data={"sub": user.full_name})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/users", response_model=list[UserReadSchema], tags=["Users"])
async def read_users(db: SessionDep, skip: int = 0, limit: int = 100):
    users = await get_users(db, skip=skip, limit=limit)
    return users


@app.get("/api/users/{user_id}", response_model=UserReadSchema, tags=["Users"])
async def read_user(user_id: int, db: SessionDep):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.put("/api/users/{user_id}", response_model=UserReadSchema, tags=["Users"])
async def update_user_endpoint(
    user_id: int, user_update: UserUpdateSchema, db: SessionDep
):
    user = await update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.delete("/api/users/{user_id}", response_model=UserReadSchema, tags=["Users"])
async def delete_user_endpoint(user_id: int, db: SessionDep):
    result = await delete_user(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"detail": "Пользователь удалён"}


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
async def get_table_column_data(table_name: str, column_name: str):
    async with engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)
        if table_name not in tables:
            raise HTTPException(
                status_code=404, detail=f"Таблица '{table_name}' не найдена"
            )
        elif column_name not in tables[table_name].columns:
            raise HTTPException(
                status_code=404,
                detail=f"Столбец '{column_name}' не найден в таблице '{table_name}'",
            )

        result = await conn.execute(text(f"SELECT {column_name} FROM {table_name}"))

    # Преобразуем каждую строку в словарь с именем колонки в качестве ключа
    items = [getattr(row, column_name) for row in result]

    return items
