from qdrant_client import models, QdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from typing import List
import json
from models.db_schemas import RetrievedDocument

class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_path: str):

        self.client = None
        self.db_path = db_path
        self.distance_metric = None

        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        self.client = None

    def is_collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    def delete_collection(self, collection_name: str) -> bool:
        if self.is_collection_exists(collection_name=collection_name):
            return self.client.delete_collection(collection_name=collection_name)
    # return None if the collection doesn't exist
        
    def set_distance_metric(self, distance: str):
        if distance == DistanceMethodEnums.COSINE.value:
            self.distance_metric = models.Distance.COSINE
        elif distance == DistanceMethodEnums.DOT.value:
            self.distance_metric = models.Distance.DOT
           
    def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)
        
        if not self.is_collection_exists(collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_metric
                )
            )

            return True
        
        return False

    # return False if the collection already exists and the do_reset is set to False
    
    def add_record(self, collection_name: str, vector: list[float], text: str,
                         metadata: dict = None, 
                         record_id: str = None):
        
        if not self.collection_exists(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False
        
        try:

            _ = self.client.upload_collection(
                collection_name=collection_name,
                vectors=[vector],
                payload=[{
                    "text": text,
                    "metadata": metadata
                }],
                ids=record_id # if record_id is None, qdrant will create a UUID
            )
        
        except Exception as e:
            self.logger.error(f"Error while uploading point: {e}")
            return False

        return True

    def add_many_records(
        self,
        collection_name: str,
        vectors: list[list[float]],
        texts: list[str],
        metadata: list[dict] | None = None,
        record_ids: list[str] | None = None,
        batch_size: int = 50,
        parallel: int = 1
        ) -> bool:

        if len(texts) != len(vectors):
            raise ValueError("texts and vectors must have the same length")
        
        if metadata is None:
            metadata = [{} for _ in texts]

        if len(metadata) != len(texts):
            raise ValueError("metadata must have the same length as vectors")

        if record_ids is not None and len(record_ids) != len(texts):
            raise ValueError("record_ids must have the same length as vectors")

        #  Batching allows you to minimize the overhead of creating a network connection.
        payload = [
            {"metadata": meta, "text": text}
            for meta, text in zip(metadata, texts)
        ]
        try:
            _ = self.client.upload_collection(
                collection_name=collection_name,
                vectors=vectors,
                payload=payload,
                ids=record_ids, # if None (default), then client sees no ids and generates random UUIDs itself.
                batch_size=batch_size,
                parallel=parallel
            )
        except Exception as e:
            self.logger.error(f"Error while uploading batch: {e}")
            return False

        return True
    # return true if the uploading done succefully
        
    def search_by_vector(self, collection_name: str, vector: list[float], limit: int = 5) -> list[RetrievedDocument]:

        related_documents = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
            with_payload=True
        )
        
        if not related_documents.points:
            return []

        # the neighbors.points is a set of scoredpoints that have id, vector, score, payload
        return [
            RetrievedDocument(**{
                "score": document.score,
                "text": document.payload["text"]
            })
            for document in related_documents.points
        ]

    
