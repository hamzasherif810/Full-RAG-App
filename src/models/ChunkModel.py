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
            indexes = DataChunk.get_indexes() # list of dictionaries
            for index in indexes:
                await self.collection.create_index(
                    keys=index["keys"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_chunk(self, chunk: DataChunk):
        result = await self.collection.insert_one(chunk.model_dump(by_alias=True, exclude_none=True))
        chunk.id = result.inserted_id
        return chunk

    async def get_chunk(self, _id: str):
        document = await self.collection.find_one({
            "_id": ObjectId(_id)
        })

        if document is None:
            return None

        chunk = DataChunk(**document)
        return chunk

    # This function aims to decrease number of calls for insertions. Instead of making n calls to insert n chunks. Divide them in m chunks and make M calls
    async def insert_many_chunks(self, chunks: list[DataChunk], batch_size: int = 100):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i: i+batch_size]

            operations = [InsertOne(document=chunk.model_dump(by_alias=True, exclude_none=True))
                          for chunk in batch]

            await self.collection.bulk_write(operations)

        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        result = await self.collection.delete_many({
            "chunk_project_id": project_id
        })

        return result.deleted_count

    # since we dont have how many chunks we will get, use pagination for safety
    async def get_project_chunks(self, project_id: ObjectId, page_no: int=1, page_size: int=50):

        records = await self.collection.find({
            "chunk_project_id": project_id
        }).skip(
            ((page_no - 1) * page_size)
        ).limit(
            page_size
        ).to_list(
            length = None
        )

        return [
            DataChunk(**record)
            for record in records 
        ]