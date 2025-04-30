from pydantic import BaseModel
from typing import List, Optional

class User_group(BaseModel):
    displayname : str
    userType : str

    