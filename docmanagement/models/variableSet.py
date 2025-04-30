from pydantic import BaseModel
from models.variable import Variable
from typing import Optional, List


class VariableSet(BaseModel):
    id: Optional[str] = None
    variableSetId : Optional[str] = None
    spaceId : str
    variables: Optional[List[Variable]] = None
    isInstanceVariableSet: Optional[bool] = False
    instanceId: Optional[str] = ""