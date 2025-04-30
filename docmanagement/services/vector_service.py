
from core.config import settings
from services.azure_openai_service import AzureOpenAIService
from services.azure_ai_search_service import AzureAISearchService
from azure.search.documents.models import (
    VectorFilterMode,
    VectorizedQuery,
    VectorQuery
)

class VectorEmbeddingService:

    def __init__(self, embedding_platform = 'AzureOpenAI'):
        self.embedding_platform = embedding_platform
        if self.embedding_platform == 'AzureOpenAI':
            self.embedding_service = AzureOpenAIService()

    def generate_embeddings(self, text):
        # Ingest documents from the vector store service
        # e.g.: If the vector store is Azure AI Search, AzureAISearchService will be called.
        embeddings = self.embedding_service.generate_embeddings(text)

        return embeddings
        
class VectorStoreService:

    def __init__(self, vector_store = 'AzureAISearch'):
        self.vector_store = vector_store
        if self.vector_store == 'AzureAISearch':
            self.vector_store_service = AzureAISearchService()

    def ingest_documents(self, documents):
        # Ingest documents from the vector store service
        # e.g.: If the vector store is Azure AI Search, AzureAISearchService will be called.
        self.status = self.vector_store_service.ingest_documents(documents)

    def delete_documents(self, space_id, doc_id):
        # Delete documents from the vector store service
        self.vector_store_service.delete_documents(space_id, doc_id)

        




