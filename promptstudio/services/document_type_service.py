from services.azure_cosmosdb_service import CosmosService
import uuid
from datetime import datetime

class DocumentTypeService:
    
    def __init__(self):
        self.cosmosdb_service = None
        self.container_name = 'documentType'
        
    def establish_cosmosdb_connection(self):
        self.cosmosdb_service = CosmosService(container_name=self.container_name)
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)

    def get_chunking_flag_for_docs(self, all_doc_types, documents):
        doc_chunking_flag_map = {}
        # Get chunking flag map
        chunking_flag_map = {doc_type['docTypeId']: doc_type['chunkingConfig']['isChunkingRequired'] for doc_type in all_doc_types}
        # Transfer chunking flag at document level
        doc_chunking_flag_map = {doc['docId']: chunking_flag_map[doc['docTypeId']] for doc in documents}
        
        return doc_chunking_flag_map

    def get_persistent_doc_types(self, space_id):
        self.establish_cosmosdb_connection()
        persistent_doc_types = self.cosmosdb_service.get_persistent_doc_types(space_id = space_id)

        return persistent_doc_types
    
    def get_all_document_type(self, space_id = '', only_studio_doc_types = False):
        self.establish_cosmosdb_connection()
        if only_studio_doc_types:
            all_doc_type = self.cosmosdb_service.get_studio_doc_types()
        else:
            all_doc_type = self.cosmosdb_service.get_doc_types_for_space(space_id = space_id)
        return all_doc_type
