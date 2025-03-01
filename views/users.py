from sqlalchemy import select
from passlib.context import CryptContext
from database import SessionDep
from models import UserModel
from schemas import UserCreateSchema, UserUpdateSchema

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


async def create(db: SessionDep, user: UserCreateSchema):
    new_user = UserModel(
        full_name=user.full_name,
        email=user.email,
        password=user.password,
    )
    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)

    return new_user


async def get_by_token(db: SessionDep, token: str):
    result = await db.execute(select(UserModel).where(UserModel.token == token))
    return result.scalars().first()


async def get_by_email(db: SessionDep, email: str):
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalars().first()


async def get_by_id(db: SessionDep, user_id: int):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    return result.scalars().first()


async def get_all(db: SessionDep, skip: int = 0, limit: int = 100):
    result = await db.execute(select(UserModel).offset(skip).limit(limit))
    return result.scalars()


async def update_by_id(db: SessionDep, user_id: int, user_update: UserUpdateSchema):
    user = await get_by_id(db, user_id)
    if not user:
        return None

    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.password is not None:
        user.password = pwd_context.hash(user_update.password)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def delete_by_id(db: SessionDep, user_id: int):
    user = await get_by_id(db, user_id)
    if not user:
        return None

    await db.delete(user)
    await db.commit()

    return True
