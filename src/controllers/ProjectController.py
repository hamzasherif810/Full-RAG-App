from .BaseController import BaseController
import os

class ProjectController(BaseController):
    def __init__(self):
        super().__init__()

    def get_project_path(self, project_id: str):
        proj_dir_path = os.path.join(
            self.files_dir,
            project_id
        )
        is_exist = os.path.exists(proj_dir_path)
        if not is_exist:
            os.mkdir(proj_dir_path)
        return proj_dir_path   