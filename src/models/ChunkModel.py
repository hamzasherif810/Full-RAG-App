from .BaseDataModel import BaseDataModel
from .db_schemas.data_chunk import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne

# This ChunkModel class is for the operations that will be performed in the chunks collection.


class ChunkModel(BaseDataModel):

    def __init__(self, client: object):
        super().__init__(client=client)
        self.collection = self.database[DataBaseEnum.COLLECTION_CHUNK_NAME.value]

    @classmethod
    async def create_instance(cls, client: object):
        instance = cls(client=client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.database.list_collection_names()
        if self.collection.name not in all_collections:
            indexes = DataChunk.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    keys=index["keys"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_chunk(self, chunk: DataChunk):
        result = await self.collection.insert_one(chunk.model_dump())
        chunk._id = result.inserted_id
        return chunk

    async def get_chunk(self, _id: str):
        document = await self.collection.find_one({
            "_id": ObjectId(_id)
        })

        if document is None:
            return None

        chunk = DataChunk(**document)
        chunk._id = document["_id"]
        return chunk

    async def insert_many_chunks(self, chunks: list[DataChunk], batch_size: int = 100):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i: i+batch_size]

            operations = [InsertOne(document=chunk.model_dump())
                          for chunk in batch]

            await self.collection.bulk_write(operations)

        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        result = await self.collection.delete_many({
            "chunk_project_id": project_id
        })

        return result.deleted_count
