from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from models.user import User
from models.user_group import User_group

class Space(BaseModel):
    id: Optional[str] = ""
    spaceId : Optional[str] = None
    spaceName : str= ""
    spaceLabel : Optional[str] = ""
    description : Optional[str] = ""
    assignedUsers : Optional[List[str]] = []
    assignedUserDetails : Optional[List[User]] = []
    assignedGroups : Optional[List[str]] = []
    assignedGroupDetails : Optional[List[User_group]] = []
    published: Optional[bool] = False
    createdOn :  Optional[datetime] = None
    lastUpdatedOn : Optional[datetime] = None
    createdBy : Optional[str] = ""
    lastUpdatedBy : Optional[str] = ""
    efficiencyGained : Optional[int] = 1

    