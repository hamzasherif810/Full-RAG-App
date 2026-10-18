from pydantic import BaseModel

class ProcessRequest(BaseModel):
    file_id : str|None = None
    chunk_size : int = 100
    overlap_size: int = 20
    do_reset: bool = False
    
