from .BaseDataModel import BaseDataModel
from .db_schemas.project import Project
from .enums.DataBaseEnum import DataBaseEnum
from typing import Self

# This ProjectModel class is for the operations that will be performed in the projects collection.


class ProjectModel(BaseDataModel):

    def __init__(self, client: object):
        super().__init__(client=client)
        self.collection = self.database[DataBaseEnum.COLLECTION_PROJECT_NAME.value]

    # We have created this class method because init_collection is an asynchronous function which can't be used in the __init__ because it needs an async scope and the constructor can't be asynchronous.
    # This class method creates a ProjectModel object. And now after the instance created, we can use the init_collection safely because we are inside an async scope.
    @classmethod
    async def create_instance(cls, client: object) -> Self:
        instance = cls(client=client)
        await instance.init_collection()
        return instance

    # This function checks on the collection if its already created or not.
    # And if it is not, then build the collection but with the indexes thay we need. If it exists, do nothing.
    # Remember that we said before that any collection created, an index for _id property gets created automatically, here we did the samethin but with our custom property.
    async def init_collection(self) -> None:
        all_collections = await self.database.list_collection_names()
        if self.collection.name not in all_collections:
            indexes = Project.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    keys=index["keys"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_project(self, project: Project) -> Project:

        result = await self.collection.insert_one(project.model_dump(by_alias=True, exclude_none=True))
        # The validation step is not made here, it should be already handled during the creation of the object.
        # But now, you are just passing the project as a dictionary(.dic()) to the collection to save it.
        # The mongodb driver is responsible for creating the _id if it doesn't exist in the project dic, and if it does exist it also checks its uniqueness.
        # insert_one() operation returns an instance of InsertOneResult which has two properties: inserted_id and acknowledged
        project.id = result.inserted_id

        return project

    async def get_project_or_create_one(self, project_id: str) -> Project:

        document = await self.collection.find_one({
            "project_id": project_id
        })

        if document is None:
            project = Project(project_id=project_id)
            project = await self.create_project(project=project)
            return project

        return Project(**document)
        # The return is Project object that got created by unpacking the document.

    async def get_all_projects(self, page: int = 1, page_size: int = 10) -> tuple[list[Project], int]:

        total_documents = await self.collection.count_documents({})
        # Empty filter to count all documents in the collection
        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1

        cursor = self.collection.find({}).skip((page-1) * page_size).limit(page_size)
        # So if you for example wants the documents in page 4, and each page is of size 10. Then you will skip the first 3 pages which represent (3*10 documents)
        # and you will limit to only this page by setting limit to size page

        projects = []
        async for document in cursor:
            projects.append(
                Project(**document)
            )

        return projects, total_pages
