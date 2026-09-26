from fastapi import FastAPI
from routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from contextlib import asynccontextmanager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    client = AsyncIOMotorClient(settings.MONGODB_URL) # Just constructs the client objcet. No actual TCP connection established at this step. The actual happens when operation is launched.
    database = client[settings.MONGODB_DATABASE] # This is just a reference, no creation yet. The actual happens when operation is launched. 
    try:
        yield {"database": database,
               "client": client}
    finally:
        client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
