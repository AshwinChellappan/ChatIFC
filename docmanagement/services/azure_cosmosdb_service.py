from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
from azure.identity import ManagedIdentityCredential
from core.config import settings
from models.user import User
from util.constants import DB_QUERY
# from api import document_management_api
from util.logger import logger

# COSMOSDB_CONTAINER = 'document'
DEBUG = False
class CosmosService():

    def __init__(self, container_name='document'):
        # Define CosmosDB client
        self.cosmosdb_client = CosmosClient(settings.COSMOSDB_URI, credential = settings.COSMOSDB_KEY)
        # Define container name
        self.container_name = container_name
        # Logger
        self.logger = logger
        # Log
        self.logger.log('AZURE CosmosDB connection established...')
        # # Define CosmosDB client
        # if DEBUG:
        #     self.cosmosdb_client = CosmosClient(settings.COSMOSDB_URI, credential=settings.COSMOSDB_KEY)
        # else:
        #     managed_id_credential = ManagedIdentityCredential(
        #         client_id=settings.AZURE_MANAGED_IDENTITY_CLIENT_ID,
        #         tenant_id=settings.AZURE_AD_TENANT_ID
        #     )
        #     self.cosmosdb_client = CosmosClient(settings.COSMOSDB_URI, credential=managed_id_credential)
        # # Define container name
        # self.container_name = container_name
        # # Logger
        # self.logger = logger
        # # Log
        # self.logger.log('AZURE CosmosDB connection established...')

    def get_container(self, container_name = 'document'):
        '''
        This method creates the instance of a CosmosDB container and returns it.
        
        Inputs
            container_name (str): Name of the container.

        Output
            container (object): returns a Azure CosmosDB container object.
            
        '''
        self.container_name = container_name
        # Define Database
        self.cosmosdb_database = self.cosmosdb_client.get_database_client(settings.COSMOSDB_DATABASE)
        # Get container 
        self.container = self.cosmosdb_database.get_container_client(self.container_name)

        return self.container

    def get_item(self, doc_id, partition_key=None):
        '''
        This method gets the space from CosmosDB container by passing unique ID and partition key.
        
        Inputs
            id (str): Unique ID field for CosmosDB.
            partition_key(str) : Unique partition_key for CosmosDB
            item_name(str) : Type of container (for e.g.: space, user, doc, etc.)

        Output
            item (JSON): returns the JSON object in the container.
            
        '''
        try:
            # Get the document by hitting CosmosDB
            item = self.container.read_item(item=doc_id, partition_key=partition_key)
                        
        except CosmosResourceNotFoundError:
            raise ValueError('Document not found.')

        return item

    def get_all_items_with_filter(self, space_id):
        try:
            # items = list(self.container.read_all_items())
            # Prepare DB query
            all_items_with_filter_query = DB_QUERY.ALL_ITEMS_WITH_FILTER.format(
                container_name = self.container_name,
                space_id_field = 'spaceId',
                space_id = space_id
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch all items: {}'.format(error)
            raise RuntimeError(error_msg)
        return items
    
    def get_variable_set_items(self, space_id,instance_id,isInstanceVariableSet):
        try:
            all_items_with_filter_query = DB_QUERY.GET_VARIABLE_SET_ITEM.format(
                container_name = self.container_name,
                space_id_field = 'spaceId',
                space_id = space_id
            )

            if bool(isInstanceVariableSet):
                all_items_with_filter_query += ' and {}.instanceId = "{}" and {}.isInstanceVariableSet = true'.format(
                self.container_name,
                instance_id,
                self.container_name,
            )
            else :
                all_items_with_filter_query += 'and {}.isInstanceVariableSet = false'.format(
                self.container_name)

            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch variable set items: {}'.format(error)
            raise RuntimeError(error_msg)
        return items


    def get_studio_doc_types(self):
        try:
            # Prepare DB query
            studio_doc_types = DB_QUERY.STUDIO_LEVEL_DOC_TYPES.format(
                container_name = self.container_name,
                doc_type_level_field = 'docTypeLevel'
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = studio_doc_types, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch studio level document types: {}'.format(error)
            raise RuntimeError(error_msg)
            
        return items
    
    def get_doc_types_for_space(self, space_id):
        try:
            # Prepare DB query
            doc_types_for_space_query = DB_QUERY.DOC_TYPES_FOR_SPACE.format(
                container_name = self.container_name,
                space_id_field = 'spaceId',
                space_id = space_id,
                doc_type_level_field = 'docTypeLevel',
                linked_assistants_field = 'linkedAssistants'
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = doc_types_for_space_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch document types for space: {}'.format(error)
            raise RuntimeError(error_msg)
            
        return items

    def get_document_by_instanceid(self, instance_Id,container_name):
        try:
            self.get_container()
            all_items_with_filter_query =DB_QUERY.ALL_ITEMS_WITH_FILTER_INSTANCEID.format(
                container_name = self.container_name,
                instance_id_field = 'instanceId',
                instance_id = instance_Id,
                is_instance_doc_field = 'isInstanceDoc'
            )
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch all document items by instanceId: {}'.format(error)
            raise RuntimeError(error_msg)
        return items
    
    def get_document_by_spaceid(self, space_id,container_name):
        try:
            self.get_container()
            all_items_with_filter_query =DB_QUERY.ALL_ITEMS_WITH_FILTER_SPACEID.format(
                container_name = self.container_name,
                space_id_field = 'spaceId',
                space_id = space_id,
                is_default_template_field = 'isDefaultResponseTemplate'
            )
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch all document items by instanceId: {}'.format(error)
            raise RuntimeError(error_msg)
        return items

    def get_space_instance_by_instance(self, item_id, partition_key = None, item_name = 'spaceInstance'):
        try:
            item = self.container.read_item(item_id, partition_key = partition_key)
        except CosmosResourceNotFoundError:
            return []
        return item
    
    def delete_item_instance(self, item_id, partition_key = None, item_name = 'spaceInstance'):
        '''
        This method gets the space Instance from CosmosDB container by passing unique ID and partition key.
        Then it deletes the space Instance from the container.
        
        Inputs
            id (str): Unique ID field for CosmosDB.
            partition_key(str) : Unique partition_key for CosmosDB
            item_name(str) : Type of container (for e.g.: space, user, doc, etc.)

        Output
            item (JSON): returns the JSON object in the container.
        '''
        try:
            item = self.container.read_item(item_id, partition_key = partition_key)
            self.container.delete_item(item, item_id)
            message = f'Cleanup for instanceId {item_id} completed successfully.'
        except CosmosResourceNotFoundError:
            return []
        return message

    def get_all_docs_for_rag(self, space_id, item_name = 'document'):
        try:
            # items = list(self.container.read_all_items())
            self.logger.log('CosmosDB - Get all items with filter...')
            # Prepare DB query
            all_docs_for_rag_query = DB_QUERY.ALL_DOCS_FOR_RAG.format(
                doc_id_field = 'docId',
                container_name = 'document',
                space_id_field = 'spaceId',
                space_id = space_id,
                is_instance_doc_field = "isInstanceDoc",
                rag_flag_field = "selectedForRAG"
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_docs_for_rag_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch all documents for RAG: {}'.format(error)
            self.logger.log(error_msg, 'ERROR')
            raise RuntimeError(error_msg)

        return items

    def update_item(self, item_id, new_item:dict):
        '''
        This method takes in a brand new space and space id. It updates the new space against the space id.
        
        Inputs
            item_id (str): Unique ID field for CosmosDB.
            item_name(str) : Type of container (for e.g.: space, user, doc, etc.)

        Output
            updated_item (JSON): returns the JSON object in the container.
            
        '''
        updated_item = {}
        # uid = str(item_id)
        # partition_key = item_id
        try:
            current_item = self.container.read_item(item_id, partition_key=item_id)
            # Update the item with new space data
            updated_item = {**current_item, **new_item}
            # Replace item
            self.container.replace_item(current_item, updated_item)
        except CosmosResourceNotFoundError:
            raise ValueError('Document not found.')

        return updated_item
    
    def reset_ingestion(self, item_id):
        # uid = str(item_id)
        # partition_key = item_id
        try:
            current_item = self.container.read_item(item_id, partition_key=item_id)
            # Update the item with new space data
            current_item['numDocsToBeIngested'] = 0
            # Replace item
            self.container.upsert_item(current_item)
        except CosmosResourceNotFoundError:
            raise ValueError('Document not found for doctype_id.')

        return current_item

    def delete_item(self, item_id, partition_key=None, item_name = 'Document'):
        '''
        This method gets the space from CosmosDB container by passing unique ID and partition key.
        Then it deletes the space from the container.
        
        Inputs
            id (str): Unique ID field for CosmosDB.
            partition_key(str) : Unique partition_key for CosmosDB
            item_name(str) : Type of container (for e.g.: , user, doc, etc.)

        Output
            item (JSON): returns the JSON object in the container.
        '''
        
        try:
            # Get item
            item = self.container.read_item(item_id, partition_key = partition_key)
            # Delete item
            self.container.delete_item(item, item_id)
            # Compose success message
            message = '{} #{} deleted.'.format(item_name, item_id)
        except CosmosResourceNotFoundError:
            raise ValueError('{} not found.'.format(item_name))
        return message
    
    def get_item_by_id(self, id, partition_key=None, item_name = 'document'):
        try:
            self.logger.log('CosmosDB - Get item by ID')
            item = self.container.read_item(id, partition_key = partition_key)
        except CosmosResourceNotFoundError:
            error_msg = '{} not found.'.format(item_name)
            self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)

        return item

    def get_items_for_query(self, query):
        '''
        This method fetches the list of spaces in the container.
        
        Inputs
            item_name(str) : Type of container (for e.g.: space, user, doc, etc.)

        Output
            items (list(JSON)): returns the list of space JSON objects in the container.
            
        '''
        try:            
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            raise RuntimeError('Failed to fetch all items: {}'.format(error))

        return items
    
    def check_doctype_in_prompt(self, docType_id,container_name):
        try:
            # Prepare DB query
            all_items_docType_with_filter_query = DB_QUERY.GET_PROMPT_FOR_DOCTYPE.format(
                container_name = container_name,
                docTypes_id_field = 'docTypes',
                doctype_id = docType_id
            )
            items = list(self.container.query_items(query = all_items_docType_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to check document type in prompt: {}'.format(error)
            raise RuntimeError(error_msg)
        return items
    
    def get_failed_docs(self, docType_id,container_name):
        try:
            # Prepare DB query
            get_all_items_failed_docs = DB_QUERY.GET_ALL_FAILED_DOCS.format(
                container_name = container_name,
                docTypes_id_field = 'docTypeId',
                doctype_id = docType_id,
                uploadStatus = 'uploadStatus'
            )
            items = list(self.container.query_items(query = get_all_items_failed_docs, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to get failed doc type in prompt: {}'.format(error)
            raise RuntimeError(error_msg)
        return items
    
    def check_link_doctype_in_prompt(self, docType_id,space_id,container_name):
        try:
            # Prepare DB query
            all_items_docType_with_filter_query = DB_QUERY.CHECK_PROMPT_FOR_DOCTYPE.format(
                container_name=container_name,
                docTypes_id_field='docTypes',  # Field for docTypes
                doctype_id=docType_id,         # UUID to match
                space_id_field='spaceId',      # Field for spaceId
                space_id=space_id              # UUID to match
                )
            items = list(self.container.query_items(query = all_items_docType_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to check document type in prompt: {}'.format(error)
            raise RuntimeError(error_msg)
        return items
    
    def get_all_items_with_space_instace(self, instance_id):
        try:
            # Prepare DB query
            all_items_with_filter_query = DB_QUERY.ALL_ITEMS_WITH_INSTANCE_FILTER.format(
                container_name = self.container_name,
                instance_field = 'instanceId',
                instance_id = instance_id,
                is_instance_doc_field = 'isInstanceDoc'
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch all documents with instance: {}'.format(error)
            raise RuntimeError(error_msg)
        return items
    
    def get_all_items_with_space(self, space_id):
        try:
            # Prepare DB query
            all_items_with_filter_query = DB_QUERY.ALL_ITEMS_WITH_SPACE_FILTER.format(
                container_name = self.container_name,
                space_field = 'spaceId',
                space_id = space_id
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch items with spaceid: {}'.format(error)
            raise RuntimeError(error_msg)
        return items
    
    def get_all_items_with_instanceid(self, instance_id):
        try:
            # Prepare DB query
            all_items_with_filter_query = DB_QUERY.ALL_ITEMS_WITH_INSTANCEID_FILTER.format(
                container_name = self.container_name,
                instance_id_field = 'instanceId',
                instance_id = instance_id
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch items with instanceid: {}'.format(error)
            raise RuntimeError(error_msg)
        return items
    
    def update_task_progress_ingestion(self,docTypeId,increment,status_message):
        try:
            self.get_container(container_name='documentType')
            doctype_item = self.container.read_item(docTypeId, partition_key=docTypeId)
            doctype_item['ingestionProgress']=increment
            doctype_item['ingestionStatus']=status_message
            self.container.replace_item(docTypeId, doctype_item)
        except Exception as e:
            raise RuntimeError(e)
        
    def get_items_filter_by_doctype_ingestion(self, container_name, doc_type_id):
        try:
            self.get_container()
            items_with_filter_query =DB_QUERY.ITEMS_WITH_INGESTION_PROGRESS.format(
                container_name = self.container_name,
                doc_type_field = 'docTypeId',
                doc_type_id = doc_type_id,
                is_instance_doc_field = 'isInstanceDoc',
                ingestion_in_progress = 'ingestionInProgress'
            )
            items = list(self.container.query_items(query = items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Error while fetch all document items by doctype ID: {}'.format(error)
            raise RuntimeError(error_msg)
        return items