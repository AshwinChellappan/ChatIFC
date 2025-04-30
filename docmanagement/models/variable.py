from pydantic import BaseModel
from typing import Optional

class Variable(BaseModel):
    name: Optional[str] = ""
    value: Optional[str] = ""
    description: Optional[str] = ""