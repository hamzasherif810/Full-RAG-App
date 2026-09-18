from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignal
import re # regex library used for text preprocessing.
import os

class DataController(BaseController):

    def __init__(self):
        super().__init__()
        self.size_scale = 1048576 # convert MB to bytes

    def validate_uploaded_file(self, file: UploadFile):
        
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value, file.content_type 
        
        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value, file.content_type 
        
        return True, ResponseSignal.FILE_UPLOAD_SUCCESS.value, file.content_type 

    def generate_unique_filepath(self, orig_file_name: str, project_id: str):
        # this function creates the new file name path which consists of the path of the project_id specific folder, then the new file name which is a combination of a random string of 12 chars and the cleaned filename.

        random_number = self.generate_random_string()
        # lets make sure that there is no file with that unique name under that projct folder
        # first lets clean the file name using regex text preprocessing
        proj_dir_path = ProjectController().get_project_path(project_id=project_id)

        cleaned_file_name = self.get_clean_filename(orig_file_name)

        new_file_path = os.path.join(
            proj_dir_path,
            random_number + '_' + cleaned_file_name
        )

        while os.path.exists(new_file_path):
            random_number = self.generate_random_string()
            new_file_path = os.path.join(
                        proj_dir_path,
                        random_number + '_' + cleaned_file_name
                    )

        return new_file_path, random_number + '_' + cleaned_file_name


    def get_clean_filename(self, filename: str):

        # replace all white spaces with underscores
        cleaned_file_name = filename.replace(" ", "_")

        # then removes anything except the alphanumeric characters (\w) and the . and replace it with empty ''
        # So \w is basically shorthand for [a-z A-Z 0-9 _].

        cleaned_file_name = re.sub(r'[^\w.]', '', cleaned_file_name.strip())

        return cleaned_file_name

