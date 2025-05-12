from http import client
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from models import like
from core.config import settings
from api.v1.like import router
from exceptions.services import DuplicateError, NotFoundKeyError


@asynccontextmanager
async def lifespan(_: FastAPI):
    client = AsyncIOMotorClient(settings.get_mongodb_connection_string())
    await init_beanie(database=client[settings.mongo_db_name], document_models=[like.Like])
    yield
    client.close()

    
app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/api/openapi.json")


app.include_router(router=router)


@app.exception_handler(DuplicateError)
async def duplicate_key_handler(_, exception: DuplicateError):
    return JSONResponse(content=str(exception), status_code=client.BAD_REQUEST)


@app.exception_handler(NotFoundKeyError)
async def duplicate_key_handler(_, exception: NotFoundKeyError):
    return JSONResponse(content=str(exception), status_code=client.NOT_FOUND)