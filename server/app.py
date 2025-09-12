from fastapi import FastAPI
from src.routes import base_router
from contextlib import asynccontextmanager

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    print("Starting up fastapi...")
    yield
    # --- shutdown ---
    print("Shutting down fastapi...")



app.include_router(base_router)



