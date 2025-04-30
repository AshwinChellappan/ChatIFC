from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
from core.config import settings
from api import prompt_studio_api
from util.constants import DB_QUERY, MSG

COSMOSDB_CONTAINER = 'prompt'

class CosmosService():

    def __init__(self, container_name = 'prompt'):
        self.container_name = container_name
        # Define CosmosDB client
        self.cosmosdb_client = CosmosClient(settings.COSMOSDB_URI,credential = settings.COSMOSDB_KEY)
        # Logger
        self.logger = prompt_studio_api.logger
        # Log
        self.logger.log('AZURE CosmosDB connection established...')

    def get_container(self, container_name = 'prompt'):
        # Define Database
        self.cosmosdb_database = self.cosmosdb_client.get_database_client(settings.COSMOSDB_DATABASE)
        # Define container name
        self.container_name = container_name
        # Get container 
        self.container = self.cosmosdb_database.get_container_client(container_name)
        # Log status
        self.logger.log('Azure CosmosDB container instance made...')

        return self.container
    
    def get_item(self, id, partition_key=None, item_name = 'prompt'):
        try:
            self.logger.log('CosmosDB - Get item by ID')
            item = self.container.read_item(id, partition_key = partition_key)
        except CosmosResourceNotFoundError:
            error_msg = '{} not found.'.format(item_name)
            self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)

        return item
    
    def get_space_item(self, id):
        try:
            self.logger.log('CosmosDB - Get space item by spaceId')
            item = self.container.read_item(id, partition_key = id)
        except CosmosResourceNotFoundError:
            error_msg = '{} not found.'.format(id)
            self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)

        return item
    
    def get_variable_set_items(self, space_id,instance_id = None):
        try:
            all_items_with_filter_query = DB_QUERY.GET_VARIABLE_SET_ITEM.format(
                container_name = self.container_name,
                space_id_field = 'spaceId',
                space_id = space_id
            )

            if instance_id:
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

    def get_space_instance_item(self, id, partition_key='instanceId', item_name = 'spaceInstance'):
        try:
            self.logger.log('CosmosDB - Get item by instance ID')

            get_spaces_query = DB_QUERY.SPACE_FOR_USER_QUERY.format(
                container_name = 'spaceInstance',
                assigned_users_field = 'assignedUsers',
                insatnce_id_field = 'instanceId',
                instance_id = id
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))
            
            if not items:
            # List is empty, handle accordingly
                print(f'Space Instance not found for instance id : {partition_key}')
                return []

            item = items[0]


        except CosmosResourceNotFoundError:
            error_msg = '{} not found.'.format(item_name)
            self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)

        return item

    def get_all_items_with_filter(self, space_id, item_name = 'prompt'):
        try:
            # items = list(self.container.read_all_items())
            self.logger.log('CosmosDB - Get all items with filter...')
            # Prepare DB query
            all_items_with_filter_query = DB_QUERY.ALL_ITEMS_WITH_FILTER.format(
                container_name = self.container_name,
                space_id_field = 'spaceId',
                space_id = space_id,
                instance_list_field = 'isInstanceList'
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = MSG.FETCH_FAILURE
            self.logger.log(error_msg, 'ERROR')
            raise RuntimeError(error_msg)
            

        return items

    def get_items_with_filter_instance(self, instance_id, item_name = 'prompt'):
        try:
            # items = list(self.container.read_all_items())
            self.logger.log('CosmosDB - Get  items with filter instanceId...')
            # Prepare DB query
            all_items_with_filter_instance_query = DB_QUERY.ITEMS_WITH_FILTER_INSTANCE.format(
                container_name = self.container_name,
                instance_id_field = 'instanceId',
                instance_id = instance_id
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_items_with_filter_instance_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = MSG.FETCH_FAILURE
            self.logger.log(error_msg, 'ERROR')
            raise RuntimeError(error_msg)
            

        return items

    def get_all_doc_types(self, space_id):
        try:
            # items = list(self.container.read_all_items())
            # Prepare DB query
            all_items_with_filter_query = DB_QUERY.ALL_DOC_TYPES.format(
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

    def get_docs_for_types(self, doc_types):
        try:
            # items = list(self.container.read_all_items())
            # Prepare DB query
            all_items_with_filter_query = DB_QUERY.PERSISTENT_DOCS.format(
                container_name = self.container_name,
                doc_type_field = 'docTypeId',
                doc_types = doc_types,
                rag_flag_field = "selectedForRAG"
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to to fetch docs for the given types: {}'.format(error)
            raise RuntimeError(error_msg)
            
        return items

    def get_persistent_doc_types(self, space_id):
        try:
            # Prepare DB query
            persistent_doc_types_query = DB_QUERY.PERSISTENT_DOC_TYPES.format(
                container_name = self.container_name,
                space_id_field = 'spaceId',
                space_id = space_id,
                doc_type_level_field = 'docTypeLevel',
                linked_assistants_field = 'linkedAssistants',
                rag_flag_field = "selectedForRAG",

            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = persistent_doc_types_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch persistent doc types: {}'.format(error)
            raise RuntimeError(error_msg)
            
        return items

    def get_all_docs_for_rag(self, space_id, item_name = 'document'):
        try:
            # items = list(self.container.read_all_items())
            self.logger.log('CosmosDB - Get all docs for RAG...')
            # Prepare DB query
            all_docs_for_rag_query = DB_QUERY.ALL_DOCS_FOR_RAG.format(
                doc_id_field = 'docId',
                container_name = 'document',
                space_id_field = 'spaceId',
                space_id = space_id,
                rag_flag_field = "selectedForRAG",
                is_instance_doc_field = "isInstanceDoc"
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_docs_for_rag_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch all documents for RAG: {}'.format(error)
            self.logger.log(error_msg, 'ERROR')
            raise RuntimeError(error_msg)

        return items

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

    def get_response_template_doc(self, space_id, doc_id, item_name = 'document'):
        try:
            # items = list(self.container.read_all_items())
            self.logger.log('CosmosDB - getting response template docs...')
            # Prepare DB query
            response_template_doc_query = DB_QUERY.RESPONSE_TEMPLATE_DOC.format(
                container_name = 'document',
                space_id_field = 'spaceId',
                space_id = space_id,
                doc_id_field = 'docId',
                doc_id = doc_id,
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = response_template_doc_query, enable_cross_partition_query = True))
            #
            item = items[0]
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch all documents for RAG: {}'.format(error)
            self.logger.log(error_msg, 'ERROR')
            raise RuntimeError(error_msg)

        return item
    
    def get_document_type(self, doc_type_id, item_name = 'documentType'):
        try:
            # items = list(self.container.read_all_items())
            self.logger.log('CosmosDB - getting prompt document type...')
            # Prepare DB query
            get_document_type_query = DB_QUERY.GET_DOC_QUERY_FILTER.format(
                container_name = 'documentType',
                space_id_field = 'docTypeId',
                space_id = doc_type_id
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = get_document_type_query, enable_cross_partition_query = True))
            #
            item = items[0]

        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch all documentTypes: {}'.format(error)
            self.logger.log(error_msg, 'ERROR')
            raise RuntimeError(error_msg)

        return item


    def get_all_items(self, item_name = 'prompt'):
        try:
            self.logger.log('CosmosDB - Read all items')
            items = list(self.container.read_all_items())
        except CosmosHttpResponseError as error:
            error_msg = MSG.FETCH_FAILURE
            self.logger.log(error_msg, 'ERROR')
            raise RuntimeError(error_msg)

        return items

    def update_item(self, item_id, new_item:dict, item_name = 'prompt'):
        '''
        This method takes in a brand new space and space id. It updates the new space against the space id.
        
        Inputs
            item_id (str): Unique ID field for CosmosDB.
            item_name(str) : Type of container (for e.g.: space, user, doc, etc.)

        Output
            updated_item (JSON): returns the JSON object in the container.
            
        '''
        updated_item = {}
        try:
            self.logger.log('COsmosDB - Update item...')
            current_item = self.container.read_item(item_id, partition_key=item_id)
            # Update the item with new space data
            updated_item = {**current_item, **new_item}
            # Replace item
            self.container.replace_item(current_item, updated_item)
        except CosmosResourceNotFoundError:
            error_msg = '{} not found.'.format(item_name)
            self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)

        return updated_item

    def delete_item(self, item_id, partition_key=None, item_name = 'prompt'):
        '''
        This method gets the space from CosmosDB container by passing unique ID and partition key.
        Then it deletes the space from the container.
        
        Inputs
            id (str): Unique ID field for CosmosDB.
            partition_key(str) : Unique partition_key for CosmosDB
            item_name(str) : Type of container (for e.g.: space, user, doc, etc.)

        Output
            item (JSON): returns the JSON object in the container.
        '''
        try:
            self.logger.log('CosmosDB - Delete item...')
            # Get item
            item = self.container.read_item(item_id, partition_key = partition_key)
            # Delete item
            self.container.delete_item(item, item_id)
            # Compose success message
            message = '{} #{} deleted.'.format(item_name, item_id)
        except CosmosResourceNotFoundError:
            error_msg = '{} not found.'.format(item_name)
            self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)
        return message
    
    def get_items_for_optimum_flag(self, space_id):
        '''
        This method fetches the list of flagged prompt list in the container.
        
        Inputs
            space_id(str) : unique identifier for space

        Output
            items (list(JSON)): returns the list of flagged prompt list JSON objects in the container.
            
        '''
        # Build query
        query = DB_QUERY.ALL_ITEMS_FOR_OPTIMUM_FLAG.format(
            container_name = 'prompt', 
            space_id_field = 'spaceId',
            space_id = space_id,
            flag_field = 'optimumFlag'
        )
        try:            
            # Get the flagged prompt list by hitting CosmosDB
            items = list(self.container.query_items(query = query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            raise RuntimeError('Failed to fetch flagged prompt list: {}'.format(error))
        return items
    
    def get_item_by_id(self, id, partition_key=None, item_name = 'space'):
        try:
            self.logger.log('CosmosDB - Getting space item by ID')
            item = self.container.read_item(id, partition_key = partition_key)
        except CosmosResourceNotFoundError:
            error_msg = '{} Item not found.'.format(item_name)
            self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)

        return item

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
