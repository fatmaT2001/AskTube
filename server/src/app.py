from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


from .routes import base_router
from .routes import chat_router

from .utils.settings import get_settings
from .models.db_scheme import SQLAlchemyBase


from .stores import VectorDBFactory, GenerationFactory


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
        db_client=sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        app.state.db_client = db_client
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
    try:
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLAlchemyBase.metadata.create_all)
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise e
    

    # setup vector db
    try:
        vector_db_factory = VectorDBFactory()
        vector_db = vector_db_factory.create_vectordb(get_settings().VECTOR_DB_PROVIDER)
        await vector_db.connect()
        app.state.vector_db = vector_db
    except Exception as e:
        print(f"Error setting up vector database: {e}")
        raise e
    
    # setup generation model
    try:
        generation_factory = GenerationFactory()
        generation_model = generation_factory.create_provider(get_settings().GENERATION_MODEL_PROVIDER)
        generation_model.connect()
        app.state.generation_model = generation_model
    except Exception as e:
        print(f"Error setting up generation model: {e}")
        raise e
    
    print("Starting up fastapi...")
    yield
    # --- shutdown ---
    await db_engine.dispose()
    await app.state.vector_db.disconnect()
    app.state.generation_model.disconnect()
    print("Shutting down fastapi...")



app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(base_router)
app.include_router(chat_router)



