from pydantic import BaseModel
from typing import Optional

class Attributes(BaseModel):
    numPages: Optional[int] = 0
    numTables: Optional[int] = 0
    numImages: Optional[int] = 0
    numParagraphs: Optional[int] = 0
    numTokens: Optional[int] = 0