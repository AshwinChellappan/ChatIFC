
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

from core.config import settings
from util.constants import AI_SEARCH
from util.logger import logger

class AzureAISearchService:

    def __init__(self):
        # service endpoint
        self.service_endpoint = settings.AZURE_AISEARCH_ENDPOINT
        # Key
        self.key = settings.AZURE_AISEARCH_KEY
        # Index name
        self.index_name = AI_SEARCH.INDEX_NAME
        # define clients
        self.index_client = SearchIndexClient(self.service_endpoint, AzureKeyCredential(self.key))
        # define search client
        self.search_client = SearchClient(self.service_endpoint, index_name = self.index_name, credential = AzureKeyCredential(self.key))

    def ingest_documents(self, documents):
        message = None
        try:
            self.search_client.upload_documents(documents=documents)
            message = 'Document ingestion successful.'
        except Exception as error:
            message = 'Document ingestion unsucessful.'
            logger.log(f'Document Ingestion unsuccessful: {error}')

        return message

    def delete_documents(self, space_id, doc_id):
        # Filter query on space id and doc id
        filter_query = "spaceId eq '{}' and docId eq '{}'".format(space_id, doc_id)
        # Search results on filter
        results = self.search_client.search(search_text="*", filter=filter_query)
        # Get delete keys
        delete_keys = [{'id' : result['id']} for result in results]
        #
        if delete_keys:
            deletion_result = self.search_client.delete_documents(documents=delete_keys)
            if deletion_result:
                print('Successful deletion of records.')
            else:
                print('Deletion of records unsuccessful.')
        else:
            print('No chunks and vectors exist for the space and document combination.')


