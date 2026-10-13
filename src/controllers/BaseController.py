from helpers.config import get_settings, Settings
import os
import random, string

class BaseController:

    def __init__(self):

        self.app_settings = get_settings()
        self.src_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(
            self.src_dir,
            "assets/files"
        )
        self.vectordb_dir = os.path.join(
            self.src_dir,
            "assets/vectordb"
        )

    # if I knew the path of the controllers folder, then I have also the path of the assets folder because both are under the same directory.
    # After that, if I joined the resulting path (src directory path) with the assets/files then now I have the path of the files folder.
    # I put this in the base controller because this can be used any of the childs.
    
    def generate_random_string(self, length: int = 12):
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        
        return random_string

    def get_vectordb_path(self, vectordb_name: str) -> str:

        db_path = os.path.join(
            self.vectordb_dir,
            vectordb_name
        )

        if not os.path.exists(db_path):
            os.makedirs(db_path, exist_ok=True)
        return db_path





        