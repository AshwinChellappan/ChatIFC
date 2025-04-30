from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from models.example import Example

class Prompt(BaseModel):
    promptId: Optional[str] = '' # unique prompt ID
    promptName: str # 
    responseSectionName: Optional[str] = ''
    promptText: Optional[str] = ''
    embeddingPlatform : str = 'AzureOpenAI'
    llmModel : Optional[str] = 'GPT-3.5Turbo'
    vectorStore : Optional[str] = 'AzureAISearch'
    docTypes : Optional[List[str]] = []
    examples: Optional[List[Example]] = []
    systemMessage : str 
    response: Optional[str] = None
    responsePrefix: Optional[str] = ''
    createdBy: Optional[str] = ''
    createdOn: Optional[datetime] = None
    lastUpdatedBy: Optional[str] = ''
    lastUpdatedOn: Optional[datetime] = None