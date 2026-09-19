from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import os
import aiofiles
from models import ResponseSignal
import logging
from .schemas.data import ProcessRequest


logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix=("/api/v1/data"),
    tags=["api_v1", "data"]
)

# For every upload, I need to put file in tenents, to store them in structural way and avoid storing all things together and helps us when we evovle the project to add features on files.

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile, app_settings: Settings = Depends(get_settings)):
    # First we need to validate the file type uploaded and it max size. We will put these standards in .env(must be reflected also in .env.example and config file)
    # Since the validation is logic, then we will create in a separate logic file (under controller)
    data_controller = DataController()

    is_valid, return_signal, type = data_controller.validate_uploaded_file(file=file)

    # Now I need to save the uploaded file in the folder of the project_id given. So I need the logic that checks whether the folder of the project_id does already exist or not, and if not create it.
    # And to do this, I need to get the path of files folder to search under it for the project_id specific folder.
    # Since this is a logic, it will be created in the controllers.


    if not is_valid:
        return JSONResponse(
            status_code = 400,
            content = {
                "signal" : return_signal
            }
        )

    proj_dir_path = ProjectController().get_project_path(project_id=project_id)
    # What if there is two files with the same name but differ in content are put under the same project directory.
    # So, there must be a way of creating a unique name of each file uploaded
    # We will do this by striping the name of eachfile uploaded and then concatinating it with the project-id and a unique string of length 12 chars.
    # And this is definitely a logic so it will be implemented inside the controllers.
    file_path, file_id = data_controller.generate_unique_filepath(orig_file_name=file.filename, project_id=project_id)


    # Write the file content into the file path in binary format chunk by chunk
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code = 400,
            content = {
                "signal" : ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )
    
    return JSONResponse(
        content = {
            "signal" : ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id" : file_id
        }
    )

@data_router.post("/process/{project_id}")
async def process_endpoint(project_id: str, process_request: ProcessRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    processcontroller = ProcessController(project_id=project_id)
    file_content = processcontroller.get_file_content(file_id=file_id)

    file_chunks = processcontroller.process_file_content(
        file_id=file_id,
        file_content=file_content,
        chunk_size=chunk_size,
        overlap_size=overlap_size
        )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code = 400,
            content = {
                'signal': ResponseSignal.FILE_PROCESSING_FAILED.value
            }
        )

    return file_chunks