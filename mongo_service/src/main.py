from http import client
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from models import entity
from core.config import settings
from api.v1.like import router as like_router
from api.v1.bookmark import router as bookmark_router
from api.v1.comment import router as comment_router
from exceptions.services import DuplicateError, NotFoundKeyError


@asynccontextmanager
async def lifespan(_: FastAPI):
    client = AsyncIOMotorClient(settings.get_mongodb_connection_string())
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[entity.Like, entity.Bookmark, entity.Comment]
    )
    
    yield
    
    client.close()

    
app = FastAPI(
    lifespan=lifespan,
    docs_url="/api/v1/mongo/openapi",
    openapi_url="/api/v1/mongo/openapi.json")


app.include_router(router=like_router)
app.include_router(router=bookmark_router)
app.include_router(router=comment_router)


@app.exception_handler(DuplicateError)
async def duplicate_key_handler(_, exception: DuplicateError):
    return JSONResponse(content=str(exception), status_code=client.BAD_REQUEST)


@app.exception_handler(NotFoundKeyError)
async def not_found_key_handler(_, exception: NotFoundKeyError):
    return JSONResponse(content=str(exception), status_code=client.NOT_FOUND)
