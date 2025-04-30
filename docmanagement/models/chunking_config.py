from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChunkingConfig(BaseModel):
    chunkingStrategy : Optional[str] = 'Recursive Character Text Splitter'
    separator : Optional[str] = '\n\n'
    chunkOverlapRatio : Optional[float] = 0.1
    chunkOverlap : Optional[int] = 100
    chunkSize : Optional[int] = 1000
    lengthFunction: Optional[str] = None
    isSeparatorRegex: Optional[bool] = True
    embeddingPlatform : Optional[str] = 'AzureOpenAI'
    vectorStore : Optional[str] = 'AzureAISearch'
    isChunkingRequired: Optional[bool] = True
    lastUpdatedBy: Optional[str] = ''
    lastUpdatedOn: Optional[datetime] = None
    stride : Optional[int] = 1
    overlap : Optional[int] = 1
    threshold : Optional[int] = 95

