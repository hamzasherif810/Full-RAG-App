from .BaseDataModel import BaseDataModel
from .db_schemas.asset import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from typing import Self

# This class is responsible for handling operations performed on the assets collection.
class AssetsModel(BaseDataModel):

    def __init__(self, client: object):
        super().__init__(client)
        self.collection = self.database[DataBaseEnum.COLLECTION_ASSET_NAME.value]

    @classmethod
    async def create_instance(cls, client: object) -> Self:
        instance = cls(client=client)
        await instance.init_collection()
        return instance
    
    async def init_collection(self) -> None:
        all_collections = await self.database.list_collection_names()
        if self.collection.name not in all_collections:
            
            indexes = Asset.get_indexes()# get_indexes is a class method so we didn't need to creaet object from Asset.
            for index in indexes:
                await self.collection.create_index(
                    keys=index["keys"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def insert_asset(self, asset: Asset) -> Asset:
        result = await self.collection.insert_one(asset.model_dump(by_alias=True, exclude_none=True))
        asset.id = result.inserted_id
        return asset

    async def get_project_assets(self, asset_project_id: str, asset_type: str) -> list[Asset]:
        documents = await self.collection.find(
            {
                "asset_project_id":ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
                "asset_type": asset_type
             }).to_list(length=None)

        # .find() returns a cursor
        # .find().to_list() returns a list of asset documents under the given project_id
        return [
            Asset(**document)
            for document in documents
        ]
        #now the function return list of Asset objects

    # this function takes the asset_name which is the file name (str) and return the actual Asset Object
    async def get_asset_record(self, asset_project_id: str, asset_name: str) -> Asset:
        document = await self.collection.find_one({
            "asset_project_id":ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
            "asset_name": asset_name
        })

        if document:
            return Asset(**document)
        return None