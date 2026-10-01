from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from bson.objectid import ObjectId
import pymongo

class Project(BaseModel):

    # In Pydantic, arbitrary_types_allowed=True tells Pydantic to skip its standard data validation for custom Python classes it doesn't recognize,
    # instead of crashing with an error.By default, Pydantic only knows how to validate standard Python data types (like str, int, dict, list) and
    # standard library objects (like datetime or UUID). If you give it a complex object from a third-party library, Pydantic doesn't know how to verify its structure, so it throws a PydanticSchemaGenerationError.
    # You use it specifically to stop Pydantic from crashing when it encounters the ObjectId data type.

    id: Optional[ObjectId] = Field(default= None, alias="_id")
    # When you pull a document back from MongoDB (which naturally has a _id key), you can do Project(**doc) and it will populate id via the alias automatically.
    # When sending back to MongoDB, use p.model_dump(by_alias=True) so it comes out as _id again.

    project_id: str = Field(..., min_length=1)

    @field_validator('project_id')
    @classmethod
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError('project_id must be alphanumeric')

        return value

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    # This is the function that will be used in the ProjectModel to create the indexes needed.
    # Here you are just defining what properties will be used as indexes but the actual indexing creation happens in the ProjectModel using .create_index
    @classmethod
    def get_indexes(cls):

        return [
            {
                "keys": [
                    ("project_id", pymongo.ASCENDING)
                ],
                "name": "project_id_index_1",
                "unique": True
            }
        ]
