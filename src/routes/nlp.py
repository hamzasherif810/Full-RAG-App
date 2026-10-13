from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from .schemas.nlp import PushRequest, SearchRequest
import logging
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models.enums import ResponseSignal
from stores.llm import DocumentTypeEnum

logger = logging.getLogger('uvicorn.error')


nlp_router = APIRouter(
    prefix=("/api/v1/nlp"),
    tags=["api_v1", "nlp"]
)

# This function will take the project_id and push all the chunks of this project into the vector databae


@nlp_router.post("/push/{project_id}")
async def push_chunks(request: Request, project_id: str, push_request: PushRequest):

    nlp_controller = NLPController(vectordb_client=request.state.vectordb_client,
                                   embedding_client=request.state.embedding_client,
                                   generation_client=request.state.generation_client,
                                   template_parser=request.state.template_parser)
    
    # first we need to get the chunks of the given project_id
    # so we will create first the project model to get the id (alias=_id) of the project

    project_model = await ProjectModel.create_instance(client=request.state.client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=400,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )

    # Now we have the Project model from the projects collection in the mongodatabase. We will use now the id (alias = _id) of this project to search for the chunks in chunks collection
    chunk_model = await ChunkModel.create_instance(client=request.state.client)

    has_records = True
    page_no = 1
    inserted_items_count = 0

    while has_records:
        chunks = await chunk_model.get_project_chunks(project_id=project.id, page_no=page_no)
        if len(chunks) == 0:
            break

        is_inserted = nlp_controller.embed_and_store_data_in_vectordb(
            project=project,
            chunks=chunks,
            do_reset=push_request.do_reset if page_no == 1 else False # This logic aims to reset only the first time of the do_reset set to True. 
        )

        if not is_inserted:
            return JSONResponse(
                status_code=400,
                content={
                    "signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value
                }
            )
        
        inserted_items_count += len(chunks)
        page_no += 1
        
    return JSONResponse(
        content={
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_item_count": inserted_items_count
        }
    )


@nlp_router.post("/info/{project_id}")
async def get_info(request: Request, project_id: str):

    nlp_controller = NLPController(vectordb_client=request.state.vectordb_client,
                                   embedding_client=request.state.embedding_client,
                                   generation_client=request.state.generation_client,
                                   template_parser=request.state.template_parser)
    
    # first we need to get the chunks of the given project_id
    # so we will create first the project model to get the id (alias=_id) of the project

    project_model = await ProjectModel.create_instance(client=request.state.client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    collection_info = nlp_controller.get_vectordb_collection_info(
        project=project)

    return collection_info

@nlp_router.post("/search/{project_id}")
async def search(request: Request, project_id: str, search_request: SearchRequest):


    # create an instance from the nlp_controller to use logic inside it
    nlp_controller = NLPController(vectordb_client=request.state.vectordb_client,
                                    embedding_client=request.state.embedding_client,
                                    generation_client=request.state.generation_client,
                                    template_parser=request.state.template_parser)

    
    # Now I need to:
    # # Get collection name
    # # Embed user query with the same dimension used in the target search collection
    # # Do semantic search operation in that collection
    # Since this is a logic, we will implement it in the nlp_controller and just call it

    related_documents = nlp_controller.search_in_vector_db(project_id=project_id, query=search_request.query, limit=search_request.limit)
    
    if not related_documents: # if false
        return JSONResponse(
            status_code=400,
            content=({
                "signal": ResponseSignal.VECTORDB_SEARCH_FAILED.value
            })
        )

    
    return JSONResponse(
        content=({
            "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "result": [document.model_dump() for document in related_documents]
        })
    )

@nlp_router.post("/answer/{project_id}")
async def answer(request: Request, project_id: str, search_request: SearchRequest):

    # create an instance from the nlp_controller to use logic inside it
    nlp_controller = NLPController(
        vectordb_client=request.state.vectordb_client,
        embedding_client=request.state.embedding_client,
        generation_client=request.state.generation_client,
        template_parser=request.state.template_parser
        )

    answer, full_user_prompt, chat_history = nlp_controller.answer_rag_question(
        project_id=project_id,
        query=search_request.query,
        limit = search_request.limit
        )

    if not answer:
        return JSONResponse(
                status_code=400,
                content={
                    "signal": ResponseSignal.RAG_ANSWER_ERROR.value
                }
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_user_prompt": full_user_prompt,
            "chat_history": chat_history
        }
    )
     
    



    


