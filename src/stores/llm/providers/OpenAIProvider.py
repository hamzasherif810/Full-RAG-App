from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI
import logging

class OpenAIProvider(LLMInterface):

    def __init__(self,
                 api_key: str,
                 base_url: str = None,
                 default_input_max_tokens: int = 1000,
                 default_generation_max_output_tokens: int = 1000,
                 default_generation_temperature: float = 0.1
                 ):

        self.api_key = api_key
        self.base_url = base_url

        self.default_input_max_tokens = default_input_max_tokens
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str): # this function is for internal use, which means that it will not be exposed for external use. So, it will not be put in the interface.
        return text[:self.default_input_max_tokens].strip()

#================================================== Generate text ====================================================================================

    def generate_text(self,
                      prompt: str,
                      chat_history: list = [],
                      max_output_tokens: int = None,
                      temperature: float = None):

        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model for OpenAI was not set")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature is not None else self.default_generation_temperature


        chat_history.append(
            self.construct_prompt(prompt=self.process_text(prompt), role=OpenAIEnums.USER.value)
        )

        response = self.client.chat.completions.create(
            model=self.generation_model_id,
            messages=chat_history,
            max_completion_tokens=max_output_tokens,
            temperature=temperature
        )

        if not response or not response.choices or not response.choices[0].message:
            self.logger.error("Error while generating text with OpenAI")
            return None

        return response.choices[0].message.content

        
#================================================== Embed text ====================================================================================

    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("OpenAI cient was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for OpenAI was not set")
            return None

        response = self.client.embeddings.create(
            model=self.embedding_model_id,
            input=text, #  The input must not exceed the max input tokens for the model (8192 tokens for all embedding models).
            encoding_format="float",
            dimensions=self.embedding_size # The number of dimensions the resulting output embeddings should have. Only supported in text-embedding-3 and later models
        )

        # response.data[0].embedding
        if not response or not response.data or not response.data[0].embedding:
            self.logger.error("Error wile embedding text with OpenAI")
            return None

        return response.data[0].embedding
    

    def construct_prompt(self,
                         prompt: str,
                         role: str):

        return {
            "role": role,
            "content": prompt
        }
