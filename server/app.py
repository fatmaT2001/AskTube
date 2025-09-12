from fastapi import FastAPI
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


from src.routes import base_router
from src.utils.settings import get_settings
from src.models.db_scheme import SQLAlchemyBase



async def create_tables(engine: AsyncEngine, Base):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    # setup database
    postgres_conn = f"postgresql+asyncpg://{get_settings().USER}:{get_settings().PASSWORD}@{get_settings().HOST}:{get_settings().PORT}/{get_settings().DBNAME}"

    try:
        db_engine = create_async_engine(postgres_conn)
        db_clint=sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        app.state.db_clint = db_clint
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise e

    
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Connection to supabase successful!")
    except Exception as e:
        print(f"Connection failed: {e}")


    # create tables
    # try:
    #     async with db_engine.begin() as conn:
    #         print(SQLAlchemyBase.metadata.tables)
    #         await conn.run_sync(SQLAlchemyBase.metadata.create_all)
    # except Exception as e:
    #     print(f"Error creating tables: {e}")
    #     raise e
    
    
    print("Starting up fastapi...")
    yield
    # --- shutdown ---
    await db_engine.dispose()
    print("Shutting down fastapi...")



app = FastAPI(lifespan=lifespan)

app.include_router(base_router)



