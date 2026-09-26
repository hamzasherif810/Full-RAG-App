from fastapi import APIRouter, Depends, UploadFile, status, Request, HTTPException
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import os
import aiofiles
from models import ResponseSignal
import logging
from .schemas.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.db_schemas.data_chunk import DataChunk
from datetime import datetime
from bson.objectid import ObjectId

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix=("/api/v1/data"),
    tags=["api_v1", "data"]
)

# For every upload, I need to put file in tenents, to store them in structural way and avoid storing all things together and helps us when we evovle the project to add features on files.


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile, app_settings: Settings = Depends(get_settings)):
    # First we need to validate the file type uploaded and it max size. We will put these standards in .env(must be reflected also in .env.example and config file)
    # Since the validation is logic, then we will create in a separate logic file (under controller)

    data_controller = DataController()

    # database
    project_model = await ProjectModel.create_instance(client=request.state.client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    is_valid, return_signal, type = data_controller.validate_uploaded_file(
        file=file)

    # Now I need to save the uploaded file in the folder of the project_id given. So I need the logic that checks whether the folder of the project_id does already exist or not, and if not create it.
    # And to do this, I need to get the path of files folder to search under it for the project_id specific folder.
    # Since this is a logic, it will be created in the controllers.

    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={
                "Signal": return_signal,
                "Uploaded file type": type,
                "Allowed file types": app_settings.FILE_ALLOWED_TYPES
            }
        )


    # What if there is two files with the same name but differ in content are put under the same project directory.
    # So, there must be a way of creating a unique name of each file uploaded
    # We will do this by striping the name of eachfile uploaded and then concatinating it with the project-id and a unique string of length 12 chars.
    # And this is definitely a logic so it will be implemented inside the controllers.
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename, project_id=project_id)

    # Write the file content into the file path in binary format chunk by chunk
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=400,
            content={
                "Signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )

    return JSONResponse(
        content={
            "Signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id,
            "_id project": str(project._id)
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: str, process_request: ProcessRequest):
    # Since we want to process a specific file in a specific project, then we need the project_id which was passed in the URL
    # and we also need the file_id which is a part of the ProcessRequest object passed as a parameter
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    no_deleted_chunks = 0 # initial value

    # 1) Find the file, load the content, and process it
    processcontroller = ProcessController(project_id=project_id)
    try:
        file_content = processcontroller.get_file_content(file_id=file_id)
    # 1.1) In case the file doesn't exist 
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    file_chunks = processcontroller.process_file_content(
        file_content=file_content,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )

    # 2) Create a ProjectModel object to start doing operations on the projects collection
    project_model = await ProjectModel.create_instance(client=request.state.client)
    # 3) Get OR Create & Get the project document from the projects collection
    project = await project_model.get_project_or_create_one(project_id=project_id)


    # 4) If the returned chunks are empty, then the processing is failed
    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=400,
            content={
                'signal': ResponseSignal.FILE_PROCESSING_FAILED.value
            }
        )

    # 5)
    # Now we have file_chunks which is a List[Document], each document object has two properties, the page_content(splitted text or chunk) and metadata of this page_content
    # We need to convert file_chunks to a list[DataChunk] to pass it to insert_many_chunks(self, chunks: list[DataChunk], batch_size:int) to insert them
    file_chunks_records = [
        DataChunk(chunk_text=chunk.page_content,
                  chunk_metdata=chunk.metadata,
                  chunk_order=i,
                  chunk_project_id=project._id,
                  chunk_insertion_date=str(datetime.now())
                  )
        for i, chunk in enumerate(file_chunks, start=1)]

    # 6) Create ChunkModel object to start doing operations on the chunks collection
    chunk_model = await ChunkModel.create_instance(client=request.state.client)
    # 7) Check first before inserting the new chunks if the do_reset is true, because if it is ture, then we have to delete the old chunks first and then insert the new ones
    # 7.1) We will use project._id here because this is how chunks and projects are connected.
    if do_reset == 1:
        no_deleted_chunks = await chunk_model.delete_chunks_by_project_id(project_id=project._id)
    # 8) Insert the new chunks in the chunks collection
    no_inserted_chunks = await chunk_model.insert_many_chunks(chunks=file_chunks_records)

    return JSONResponse(
        content={
            'Signal': ResponseSignal.FILE_PROCESSING_SUCCESS.value,
            'Deleted_chunks': no_deleted_chunks,
            'Inserted_chunks': no_inserted_chunks
        }
    )
