from pydantic import BaseModel
from datetime import datetime
from datetime import date
from typing import List, Optional
from models.user import User
from models.promptList import PromptList

current_date = date.today()

class SpaceInstance(BaseModel):
    id : Optional[str]= ""
    instanceId : Optional[str]= ""
    instanceName : str = ""
    spaceId : str= ""
    description : Optional[str]= ""
    docTypes : Optional[List[str]] = []
    promptList : Optional[List[PromptList]] = []
    responseDocId : Optional[str]= ""
    responseTemplateDocId: Optional[str] = ""
    ingestionStatus : Optional[str]= ""
    ingestionProgress: Optional[float] = 0.0
    responseStatus : Optional[str]= ""
    responseProgress: Optional[float] = 0.0
    assignedUsers : Optional[List[str]] = []
    assignedUserDetails : Optional[List[User]] = []
    createdOn :  Optional[datetime]= None
    lastUpdatedOn : Optional[datetime]= None
    createdBy : Optional[str]= ""
    lastUpdatedBy : Optional[str]= ""
    instanceExpiry : Optional[date]= None
    responseGeneratedOn : Optional[datetime]= None