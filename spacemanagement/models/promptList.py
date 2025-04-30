from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from models.prompt import Prompt
from models.llm_config import LLMConfig

class PromptList(BaseModel):
    id: Optional[str] = '' # unique prompt ID
    promptListId: Optional[str] = '' # unique prompt ID
    promptListName: str # string
    description : Optional[str] = ''
    spaceId: str
    docId: Optional[str] = None
    prompts : Optional[List[Prompt]] = []
    llmConfig : Optional[LLMConfig] = None
    createdBy: Optional[str] = None
    createdOn: Optional[datetime] = None
    lastUpdatedBy: Optional[str] = None
    lastUpdatedOn: Optional[datetime] = None
    optimumFlag: Optional[bool] = False

    