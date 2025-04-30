from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Space(BaseModel):
    id: Optional[str] = ""
    spaceId : Optional[str] = None
    spaceName : str= ""
    spaceLabel : Optional[str] = ""
    description : Optional[str] = ""
    assignedUsers : Optional[List[str]] = []
    createdOn :  Optional[datetime] = None
    lastUpdatedOn : Optional[datetime] = None
    createdBy : Optional[str] = ""
    lastUpdatedBy : Optional[str] = ""