from enum import Enum

class ResponseSignal(Enum):

    FILE_VALIDATION_SUCCESS = "file_validation_success"
    FILE_TYPE_NOT_SUPPORTED =  "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    FILE_PROCESSING_SUCCESS = "file_processing_success"
    FILE_PROCESSING_FAILED = "file_processing_failed"
    NO_FILES_ERROR = "not_files_found"
    FILE_ID_ERROR = "no_file_found_with_this_id"
    PROJECT_NOT_FOUND_ERROR = "project_not_found"
    INSERT_INTO_VECTORDB_ERROR = "insertion_in_vectordb_error"
    INSERT_INTO_VECTORDB_SUCCESS = "insertion_in_vectordb_success"
    VECTORDB_COLLECTION_RETRIEVED = "vectordb_collection_retreived"
    VECTORDB_SEARCH_SUCCESS = "vector_db_search_success"
    VECTORDB_SEARCH_FAILED = "vector_db_search_failed"
    RAG_ANSWER_ERROR = "rag_answer_error"
    RAG_ANSWER_SUCCESS = "rag_answer_success"
    