from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Example(BaseModel):
    id: str
    question: str
    response: str