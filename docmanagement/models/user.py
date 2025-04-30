from pydantic import BaseModel
from typing import List

class User(BaseModel):
    id: str 
    userId : str # partition key
    name : str
    email : str
    roles: List[str]
    groups: List[str]
    