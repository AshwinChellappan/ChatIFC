from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    id: Optional[str] = '' 
    userId : Optional[str] = '' # partition key
    name : str
    email : str
    roles: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    userType: Optional[str] = 'viewer'
    isContact: Optional[bool] = False