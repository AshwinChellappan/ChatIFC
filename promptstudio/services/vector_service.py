
from core.config import settings
from services.azure_openai_service import AzureOpenAIService
from services.azure_ai_search_service import AzureAISearchService
from azure.search.documents.models import (
    VectorFilterMode,
    VectorizedQuery,
    VectorQuery
)
from api import prompt_studio_api
from util.logger import Logger

class VectorEmbeddingService:

    def __init__(self, llm_config, embedding_platform = 'AzureOpenAI'):
        self.embedding_platform = embedding_platform
        if self.embedding_platform == 'AzureOpenAI':
            prompt_studio_api.logger.log('{} - embedding platform: {}'.format(self.__class__.__name__, embedding_platform))
            self.embedding_service = AzureOpenAIService(llm_config)

    def generate_embeddings(self, text):
        # Ingest documents from the vector store service
        # e.g.: If the vector store is Azure AI Search, AzureAISearchService will be called.
        embeddings = self.embedding_service.generate_embeddings(text)
        prompt_studio_api.logger.log('{} - GENERATED embeddings using {}...'.format(self.__class__.__name__, self.embedding_platform))

        return embeddings
        
class VectorStoreService:

    def __init__(self, vector_store = 'AzureAISearch'):
        # Initialize logger
        self.logger = Logger()
        # Vector store
        self.vector_store = vector_store
        if self.vector_store == 'AzureAISearch':
            prompt_studio_api.logger.log('{} - vector store: {}'.format(self.__class__.__name__, vector_store))
            self.vector_store_service = AzureAISearchService()

    def ingest_documents(self, documents):
        # Ingest documents from the vector store service
        # e.g.: If the vector store is Azure AI Search, AzureAISearchService will be called.
        self.status = self.vector_store_service.ingest_documents(documents)

    def get_context(self, prompt, prompt_embedding, doc_info_dict, knn = 3, top_k = 3):
        # Get vector query
        vector_query = VectorizedQuery(vector=prompt_embedding, k_nearest_neighbors=knn, fields="vectorEmbedding")
        # Get context
        fields = ['content', 'spaceId', 'docId']
        all_results = []
        for doc_id, is_chunking_required in doc_info_dict.items():
            results = self.vector_store_service.perform_search(prompt, vector_query, [doc_id], fields, top_k = top_k, is_chunking_required = is_chunking_required)
            # Append results to main list 
            all_results.append(results)
        # Prepare context list
        context_list_main = []
        try:
            for idx, results in enumerate(all_results):
                context_list = self.combine_results(results, fields, idx)
                context_list_main = context_list_main + context_list
        except Exception as error:
            self.logger.log(f"Error in combining results: {error}")
        return context_list_main
    
    def combine_results(self, results, fields, idx):
        context_list = []
        for result in results:
        # for idx, result in enumerate(results):
            search_result = {}
            # Prepare new dict
            for field in fields:
                search_result[field] = result[field]            
            context = search_result['content']
            context_list.append(context)
            
        return context_list
        




