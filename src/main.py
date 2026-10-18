from fastapi import FastAPI
from routes import base, data, nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from contextlib import asynccontextmanager
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates import TemplateParser

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL) # Just constructs the client objcet. No actual TCP connection established at this step. The actual happens when operation is launched.
    database = mongo_client[settings.MONGODB_DATABASE] # This is just a reference, no creation yet. The actual happens when operation is launched.

    # LLM provider factory
    llm_provider_factory = LLMProviderFactory(config=settings)

    # Generation client
    generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    # Embedding client
    embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    embedding_client.set_embedding_model_and_size(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)

    # Vector DB provider factory
    vectordb_provider_factory = VectorDBProviderFactory(config=settings)

    # vectordb client
    vectordb_client = vectordb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)
    vectordb_client.connect()
    vectordb_client.set_distance_metric(distance=settings.VECTOR_DB_DISTANCE_METRIC)

    # Template parser
    template_parser = TemplateParser(language=settings.PRIMARY_LANG, default_language=settings.DEFAULT_LANG)

    try:
        yield {"database": database,
               "client": mongo_client,
               "embedding_client": embedding_client,
               "generation_client": generation_client,
               "vectordb_client": vectordb_client,
               "template_parser": template_parser
               }
    finally:
        mongo_client.close()
        vectordb_client.disconnect()



app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
