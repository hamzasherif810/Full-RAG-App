from .BaseController import BaseController
from models.db_schemas import Project, DataChunk
from stores.vectordb.providers import QdrantDBProvider
from stores.llm.providers import CohereProvider, OpenAIProvider
from stores.llm.LLMEnums import DocumentTypeEnum
from stores.llm.templates import TemplateParser
import json
import logging


logger = logging.getLogger(__file__)

class NLPController(BaseController):
    def __init__(self,
                 vectordb_client: QdrantDBProvider,
                 embedding_client: CohereProvider,
                 generation_client: OpenAIProvider,
                 template_parser: TemplateParser):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()

    def reset_vectordb_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vectordb_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info =  self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.loads(
                json.dumps(collection_info, default=lambda x: x.__dict__)
        )

    # تسكين الشنكس جوة الفكتور دي بي
    # index_into_vector_db -> store embedded datachunks into the vectordb
    def embed_and_store_data_in_vectordb(self, project: Project, chunks: list[DataChunk], do_reset: bool = False):

        # 1) get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # 2) Remember that in order to insert many items in qdrant vdb, you need metadatas and texts (which are the components of the payload) and the vectors 
        texts = [ chunk.chunk_text for chunk in chunks]
        metadata = [ chunk.chunk_metdata for chunk in chunks]

        vectors = [
            self.embedding_client.embed_text(text=chunk.chunk_text, document_type=DocumentTypeEnum.DOCUMENT.value)
            for chunk in chunks
        ]

        # 3) create collection if it doesn't exist
        self.vectordb_client.create_collection(collection_name=collection_name, embedding_size=self.embedding_client.embedding_size, do_reset=do_reset)
        #3) Insert in the vdb collection
        self.vectordb_client.add_many_records(collection_name=collection_name, vectors=vectors, texts=texts, metadata=metadata)

        return True

    def search_in_vector_db(self, project_id: str, query: str, limit: int = None):
        # Get collection name
        collection_name = self.create_collection_name(project_id=project_id)

        # Embed user query with the same dimension used in the target search collection
        query_vector = self.embedding_client.embed_text(text=query, document_type=DocumentTypeEnum.QUERY.value)
        if not query_vector: # due to embedding failure
            return False
        # Do semantic search operation 
        related_documents = self.vectordb_client.search_by_vector(collection_name=collection_name, vector=query_vector, limit=limit)
        
        return related_documents


    def answer_rag_question(self, project_id: str, query: str, limit: int = None):

        answer, full_prompt, chat_history = None, None, None

        # 1) Retrieve related documents
        related_documents = self.search_in_vector_db(project_id=project_id, query=query, limit=limit)

        if not related_documents:
            return answer, full_prompt, chat_history

        # 2) construct LLM prompt (prompt engineering)
        system_prompt = self.template_parser.get("rag", "system_prompt")

        documents_prompt = [
            self.template_parser.get("rag", "document_prompt", {
                "doc_num": i+1,
                "chunk_text":document.text 
            })
            for i, document in enumerate(related_documents)
        ]
        footer_prompt = self.template_parser.get("rag", "footer_prompt", {"query": query})

        # 3) construct system prompt
        chat_history = [
            self.generation_client.construct_system_prompt(
                prompt=system_prompt
            )
        ]

        # 4) construct full user prompt

        full_user_prompt = "\n\n".join( [str(documents_prompt),  footer_prompt])

        # step4: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_user_prompt,
            chat_history=chat_history
        )

        return answer, full_user_prompt, chat_history



