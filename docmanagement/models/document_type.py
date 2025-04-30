from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from models.chunking_config import ChunkingConfig

class DocumentType(BaseModel):
    id: Optional[str] = ""
    docTypeId : Optional[str] = None
    docTypeLevel: Optional[int] = 2
    typeName : str= ""
    description : Optional[str] = ""
    spaceId : str = ""
    chunkingConfig: Optional[ChunkingConfig] = ChunkingConfig()
    chunkingConfigSave: Optional[bool] = False
    linkedAssistants: Optional[List[str]] = [] # List of space ids linked if docTypeLevel = 0
    createdOn :  Optional[datetime] = None
    createdBy : Optional[str] = ""
    lastUpdatedOn : Optional[datetime] = None
    lastUpdatedBy : Optional[str] = ""
    ingestionTriggeredBy : Optional[str] = ""
    numDocsToBeIngested : Optional[int] = 0
    ingestionTriggeredOn : Optional[datetime] = None
    ingestionFailedDocs : Optional[List[str]] = []
    uploadStatus : Optional[bool] = False
    uploadFailure : Optional[int] = None
    uploadStatusPublished : Optional[bool] = True