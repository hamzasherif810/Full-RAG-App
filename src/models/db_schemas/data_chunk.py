from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson.objectid import ObjectId
import pymongo


class DataChunk(BaseModel):

    _id: Optional[ObjectId]
    # The _id property is set to Optional because you doesn't have to add it yourself, the monogdb creates it automatically if you didn't.
    chunk_text: str = Field(..., min_length=1)
    # The Field function adds extra validation rules and metadata to the property.
    # The ellipses (...) means that the field is strictly required, it can't be skipped.
    chunk_metdata: dict
    chunk_order: int = Field(..., gt=0)
    # Must be greater than 0
    chunk_insertion_date: str
    chunk_project_id: ObjectId
    model_config = ConfigDict(
        arbitrary_types_allowed=True
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
