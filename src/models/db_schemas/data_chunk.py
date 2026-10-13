from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson.objectid import ObjectId
import pymongo


class DataChunk(BaseModel):

    id: Optional[ObjectId] = Field(default= None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    # The Field function adds extra validation rules and metadata to the property.
    # The ellipses (...) means that the field is strictly required, it can't be skipped.
    chunk_metdata: dict
    chunk_order: int = Field(..., gt=0)
    # Must be greater than 0
    chunk_insertion_date: str
    chunk_project_id: ObjectId
    chunk_asset_id: ObjectId
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True # lets you fill a field using either its alias or its real Python name. Without it, once a field has an alias, only the alias works for input.
    )

    @classmethod
    def get_indexes(cls):
        return [
            {
                "keys": [
                    ("chunk_project_id", pymongo.ASCENDING)
                ],
                "name": "chunk_project_id_index_ASCENDING",
                "unique": False # Because multiple chunks can belong to the same project_id
            }
        ]
    # get_indexes returns a list of dictionaries, each dictionary represents an index. Index can be multiproperty index.


class RetrievedDocument(BaseModel):
    text: str
    score: float