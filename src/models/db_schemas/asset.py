from pydantic import BaseModel, field_validator, Field, ConfigDict
from bson import ObjectId
from typing import Optional
from datetime import datetime
import pymongo


class Asset(BaseModel):

    id: Optional[ObjectId] = Field(default= None, alias="_id")
    # Required value but without any added or extra validation metadata
    asset_project_id: ObjectId
    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    # default value means that this field is not required
    asset_size: int = Field(ge=0, default=None)
    asset_config: dict = Field(default=None)
    asset_pushed_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    @classmethod
    def get_indexes(cls):
        return [
            {
                "keys": [
                    ("asset_project_id", pymongo.ASCENDING)
                ],
                "name": "asset_project_id_index_1",
                "unique": False
            },
            {
                "keys": [("asset_project_id", pymongo.ASCENDING),
                         ("asset_name", pymongo.ASCENDING)],
                "name": "asset_project_id_asset_name",
                "unique": True
            }
        ]
