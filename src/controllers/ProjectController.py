from .BaseController import BaseController
import os

class ProjectController(BaseController):
    def __init__(self):
        super().__init__()
        
    # This function creates the project-id specific directory if it doesn't exist and return the proj_dir_path
    def get_project_path(self, project_id: str):
        proj_dir_path = os.path.join(
            self.files_dir,
            project_id
        )
        is_exist = os.path.exists(proj_dir_path)
        if not is_exist:
            os.mkdir(proj_dir_path)
        return proj_dir_path   