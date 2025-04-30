from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LLMConfig(BaseModel):
    temperature: Optional[float] = 0.1
    topProbabilities : Optional[float] = 0.1
    maxResponseLength : Optional[int] = 1500
    similarityTopK : Optional[int] = 3
    llmModel:Optional[str] = 'gpt-35-turbo-16k'