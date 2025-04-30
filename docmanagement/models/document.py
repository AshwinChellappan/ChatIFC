from pydantic import BaseModel
from models.attributes import Attributes
from typing import Optional


class Document(BaseModel):
    id: Optional[str] = None
    docId : Optional[str] = None
    docName : str
    spaceId : str
    docTypeId : Optional[str] = None
    instanceId : Optional[str] = None
    referencePath : Optional[str] = None
    blobName : Optional[str] = None
    size : Optional[float] = None
    docType : Optional[str] = None
    numOfChunks: Optional[int] = None
    ingested: Optional[bool] = False
    selectedForRAG: Optional[bool] = False
    isResponseTemplate: Optional[bool] = False
    isInstanceDoc: Optional[bool] = False
    isResponseDoc: Optional[bool] = False
    attributes: Optional[Attributes] = None
    responseTemplateDescription: Optional[str] = None
    ingestionInProgress : Optional[bool] = False
    isDefaultResponseTemplate : Optional[bool] = False
    uploadStatus : Optional[bool] = False
    uploadErrorMsg : Optional[str] = None