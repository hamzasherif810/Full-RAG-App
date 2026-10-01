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
from models.AssetsModel import AssetsModel
from models.db_schemas.data_chunk import DataChunk
from models.db_schemas.asset import Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
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
    # Since the validation process is something logic, then we will create it in a separate logic file (under controller)

    data_controller = DataController()

    

    is_valid, return_signal, file_type, file_size = data_controller.validate_uploaded_file(
        file=file)

    # Now I need to save the uploaded file in the folder of the project_id given. So I need the logic that checks whether the folder of the project_id does already exist or not, and if not create it.
    # And to do this, I need to get the path of files folder to search under it for the project_id specific folder.
    # Since this is a logic, it will be created in the controllers.

    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={
                "Signal": return_signal,
                "Uploaded file type": file_type,
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


    #) DATABASE
    #------------
    #------------

    # First create ProjectModel object to manage projects collection, then get or create the project document which has project_id=project_id from the projects collection.
    project_model = await ProjectModel.create_instance(client=request.state.client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    # Now lets store the uploaded file data in the assets collection
    # First we will create AssetsModel object to manage assets database, then create Asset object and insert it in the assets collection
    asset_model = await AssetsModel.create_instance(client=request.state.client)
    asset_resource = Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=file_size
    )
    asset_record = await asset_model.insert_asset(asset=asset_resource)

    return JSONResponse(
        content={
            "Signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id,
            "_id project": str(project.id),
            "asset_id": str(asset_record.id)
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: str, process_request: ProcessRequest):
    # The ProcessRequest which is the schema model defined in src/routes/schemas/data.py have an optional file_id field
    # The absence of the file_id field means I want to process the whole project_id project
    # The presence of the file_id field means I want to process this file only in the project_id project
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    no_deleted_chunks = 0  # initial value

    # First create ProjectModel object to manage projects collection, then get or create the project document which has project_id=project_id from the projects collection.
    project_model = await ProjectModel.create_instance(client=request.state.client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    # In case I have already specified a file in my request, then I mean this one only.
    # And if not, then I want all files in the given project

    asset_model = await AssetsModel.create_instance(
        client=request.state.client
    )

    # In order to process any asset file, it needs to exist as a record in the asset collection
    # So we will check this now

    project_files_ids = {}
    if file_id:
        asset_document = await asset_model.get_asset_record(asset_project_id=project.id, asset_name=file_id)
        if asset_document is None:
            return JSONResponse({
                "status_signal": 400,
                "content": ResponseSignal.FILE_ID_ERROR.value
            })
        project_files_ids = {
            asset_document.id: asset_document.asset_name}
    else:

        project_files = await asset_model.get_project_assets(
            asset_project_id=str(project.id),
            asset_type=AssetTypeEnum.FILE.value
        )

        project_files_ids = {
            document.id: document.asset_name
            for document in project_files}

        if len(project_files_ids) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "signal": ResponseSignal.NO_FILES_ERROR.value
                }
            )

    no_inserted_chunk_records = 0
    no_files = 0

    # Create ChunkModel object to manage chunks collection
    chunk_model = await ChunkModel.create_instance(client=request.state.client)
    #  Check first before inserting the new chunks if the do_reset is true, because if it is ture, then we have to delete the old chunks first and then insert the new ones
    #  We will use project.id here because this is how chunks and projects are connected.
    if do_reset == 1:
        no_deleted_chunks = await chunk_model.delete_chunks_by_project_id(project_id=project.id)

    #Find the file, load the content, and process it
    processcontroller = ProcessController(project_id=project_id)
    # Start loop to iterate over each asset in the given project and process it, creating chunks, and then store these chunks in their collection
    files_failed_to_load = []

    # asset_id represents the file ObjectId(), while the file_id is the name of the file(asset_name)
    for asset_id, file_id in project_files_ids.items():

        try:
            file_content = processcontroller.get_file_content(file_id=file_id)
        # In case the file doesn't physically exist locally
        # Here we are telling the python that if there any error will loading the file physically from its path, take the error and put in the logs, and append the failed file in the files_failed_to_load
        except Exception as e:
            logger.error(f"Failed to load file {file_id}: {e}")
            files_failed_to_load.append(file_id)
            continue

        file_chunks = processcontroller.process_file_content(
            file_content=file_content,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )

        # If the returned chunks are empty, then the processing is failed
        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    'signal': ResponseSignal.FILE_PROCESSING_FAILED.value
                }
            )

    
        # Now we have file_chunks which is a List[Document], each document object has two properties, the page_content(splitted text or chunk) and metadata of this page_content
        # We need to convert file_chunks to a list[DataChunk] to pass it to insert_many_chunks(self, chunks: list[DataChunk], batch_size:int) to insert them
        file_chunks_records = [
            DataChunk(chunk_text=chunk.page_content,
                      chunk_metdata=chunk.metadata,
                      chunk_order=i,
                      chunk_project_id=project.id, # _id of the project
                      chunk_asset_id=asset_id, # _id of the asset or the file
                      chunk_insertion_date=str(datetime.now())
                      )
            for i, chunk in enumerate(file_chunks, start=1)]

        # 8) Insert the new chunks in the chunks collection
        no_inserted_chunk_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(
        content={
            'Signal': ResponseSignal.FILE_PROCESSING_SUCCESS.value,
            'Deleted_chunks': no_deleted_chunks,
            'Inserted_chunks': no_inserted_chunk_records,
            'No of files processed': no_files,
            'No of files failed': len(files_failed_to_load),
            'files failed to load': files_failed_to_load
        }
    )
