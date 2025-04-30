
from core.config import settings
from services.azure_openai_service import AzureOpenAIService

class VectorEmbeddingService:

    def __init__(self, embedding_platform = 'AzureOpenAI'):
        self.embedding_platform = embedding_platform
        if self.embedding_platform == 'AzureOpenAI':
            self.vector_embedding_service = AzureOpenAIService()

    def generate_embeddings(self, text):
        # Ingest documents from the vector store service
        # e.g.: If the vector store is Azure AI Search, AzureAISearchService will be called.
        embeddings = self.vector_embedding_service.generate_embeddings(text)

        return embeddings
        



