
from core.config import settings
from services.azure_ai_search_service import AzureAISearchService

class VectorStoreService:

    def __init__(self, vector_store = 'AzureAISearch'):
        self.vector_store = vector_store
        if self.vector_store == 'AzureAISearch':
            self.vector_store_service = AzureAISearchService()

    def ingest_documents(self, documents):
        # Ingest documents from the vector store service
        # e.g.: If the vector store is Azure AI Search, AzureAISearchService will be called.
        self.status = self.vector_store_service.ingest_documents(documents)
        



