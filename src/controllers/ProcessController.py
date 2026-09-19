from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessingEnums

class ProcessController(BaseController):

    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.proj_path = ProjectController().get_project_path(project_id=project_id)

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self, file_id: str):
        file_path = os.path.join(
            self.proj_path,
            file_id
        )
        file_ext = self.get_file_extension(file_id=file_id)
        # os.path.splitext() method is used to split the pathname into a pair (root, ext), where root is the part of the path before the file extension and ext is the file extension itself.

        if file_ext == ProcessingEnums.PDF.value:
            return PyMuPDFLoader(file_path=file_path)

        if file_ext == ProcessingEnums.TXT.value:
            return TextLoader(file_path=file_path, encoding="utf-8")

        return None

    def get_file_content(self, file_id: str):

        file_loader = self.get_file_loader(file_id=file_id)
        return file_loader.load() # .load() always return a List[Document], regardless of loader type, even for a single file.


    def process_file_content(slef, file_content: list, file_id: str, chunk_size: int, overlap_size: int):

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len
        )

        file_content_text = [doc.page_content for doc in file_content]

        file_content_metadata = [doc.metadata for doc in file_content]

        chunks = text_splitter.create_documents(
            texts = file_content_text,
            metadatas = file_content_metadata
        )
        # now every chunk has the metadata of the source it came from, this is important because it tells from where each chunk came from.

        return chunks
