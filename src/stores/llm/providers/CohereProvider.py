from ..LLMInterface import LLMInterface
from ..LLMEnums import CohereEnums, DocumentTypeEnum

import cohere
import logging


class CohereProvider(LLMInterface):

    def __init__(self,
                 api_key: str,
                 default_input_max_tokens: int = 1000,
                 default_generation_max_output_tokens: int = 1000,
                 default_generation_temperature: float = 0.1):

        self.api_key = api_key

        self.default_input_max_tokens = default_input_max_tokens
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.ClientV2(
            api_key=self.api_key
        )

        self.logger = logging.getLogger(__name__)
        self.enums = CohereEnums

    def set_generation_model(self,
                             model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model_and_size(self,
                            model_id: str,
                            embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_tokens].strip()

#================================================== Generate text ====================================================================================
    def generate_text(self,
                      prompt: str,
                      chat_history: list = [],
                      max_output_tokens: int = None,
                      temperature: float = None):
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for CoHere was not set")
            return None

        prompt = self.process_text(prompt)

        chat_history.append(self.construct_prompt(role=CohereEnums.USER.value, prompt=prompt))

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature is not None else self.default_generation_temperature

        response = self.client.chat(
            model=self.generation_model_id,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temperature
        )

        if not response or not response.message or not response.message.content:
            self.logger.error("Error while generating text with CoHere")
            return None
        
        return response.message.content[0].text
    
#================================================== Embed text ====================================================================================        
    def embed_text(self, text: str, document_type: str = None):

        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere was not set")
            return None

        input_type = (CohereEnums.DOCUMENT.value
                      if document_type == DocumentTypeEnum.DOCUMENT.value
                      else CohereEnums.QUERY.value
                      )

        response = self.client.embed(
            texts=[text], # array of texts, each text will be embedded to a vector with size of the output_dimension. 
            max_tokens=self.default_input_max_tokens, # max tokens of each text in the texts array
            input_type=input_type,
            model=self.embedding_model_id,
            output_dimension=self.embedding_size, # embedding size of each text
            embedding_types=["float"] # can be one or more. may be you can also add int8, uint8, ... and you will get for each text all these types of embeddings.
        )
        # Cohere only introduced the output_dimension parameter starting with their newer embed-v4 models.
        # For embed-multilingual-v3.0 (and all other v3 variants), the output dimension is permanently locked at 1,024 dimensions and cannot be dynamically altered in the API request.

        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("Error while embedding text with CoHere")
            return None

        return response.embeddings.float[0]

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": prompt
        }

    def construct_system_prompt(self, prompt: str): 
        return {
            "role": self.enums.SYSTEM.value,
            "content": prompt
        }
