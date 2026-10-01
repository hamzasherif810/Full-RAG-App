from helpers.config import get_settings

# The BaseModel initialize the client, database, and create Settings model(remember the Settings model fields are filled during runtime using pydantic mechanism)
class BaseDataModel():
    def __init__(self, client: object):
        self.app_settings = get_settings()
        self.client = client
        self.database = client[self.app_settings.MONGODB_DATABASE]