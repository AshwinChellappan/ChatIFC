from fastapi import FastAPI
from api import document_management_api, data_ingestion_api
from core.config import settings

# FastAPI instance
app = FastAPI(
        docs_url='/docs',
        title="Document Management Service",
        description="Document Management  Service",
    )
# Include space management API router
app.include_router(document_management_api.router)
app.include_router(data_ingestion_api.router)
