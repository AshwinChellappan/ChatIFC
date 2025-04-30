
from azure.identity import ManagedIdentityCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import (
    VectorFilterMode,
    VectorizedQuery,
    VectorQuery
)
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
    HnswAlgorithmConfiguration

)

from azure.identity._exceptions import CredentialUnavailableError as IdentityCredentialUnavailableError
from fastapi import FastAPI, HTTPException
from azure.identity._exceptions import CredentialUnavailableError
from azure.core.exceptions import ServiceRequestError, HttpResponseError

from core.config import settings, DEBUG
from util.constants import AI_SEARCH
from util.logger import Logger

class AzureAISearchService:

    def __init__(self):
        # Initialize logger
        self.logger = Logger()
        # service endpoint
        self.service_endpoint = settings.AZURE_AISEARCH_ENDPOINT
        # Key
        self.key = settings.AZURE_AISEARCH_KEY
        # Index name
        self.index_name = AI_SEARCH.INDEX_NAME
        # Define Index client
        self.index_client = SearchIndexClient(self.service_endpoint, AzureKeyCredential(self.key))
        # Define search client
        self.search_client = SearchClient(self.service_endpoint, index_name = self.index_name, credential = AzureKeyCredential(self.key))
        # Log the initialization
        self.logger.log("Azure AI Search Service initialized using keys.")

    def perform_search(self, prompt, vector_query, doc_list, fields, top_k = 3, is_chunking_required = True):
        results = []
        # Construct query filter
        query_filter = ' or '.join([f"docId eq '{doc_id}'" for doc_id in doc_list])
        # Get results
        if is_chunking_required:
            results = self.search_client.search(
                filter = query_filter,
                search_text = prompt,
                vector_queries = [vector_query],
                select = fields,
                top = top_k
            )
        else:    
            results = self.search_client.search(
                filter = query_filter,
                select = fields
            )
        
        return results