from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
from core.config import settings
from models.user import User
from util.constants import AUTH, DB_QUERY
from fastapi import  status, HTTPException

COSMOSDB_CONTAINER = 'space'

class CosmosService():

    def __init__(self):
        # Define CosmosDB client
        self.cosmosdb_client = CosmosClient(settings.COSMOSDB_URI,credential = settings.COSMOSDB_KEY)
        # Define container name
        self.container_name = COSMOSDB_CONTAINER

    def get_container(self, container_name = 'space'):
        '''
        This method creates the instance of a CosmosDB container and returns it.
        
        Inputs
            container_name (str): Name of the container.

        Output
            container (object): returns a Azure CosmosDB container object.
            
        '''
        # Define Database
        self.cosmosdb_database = self.cosmosdb_client.get_database_client(settings.COSMOSDB_DATABASE)
        # Change container name
        self.container_name = container_name
        # Get container 
        self.container = self.cosmosdb_database.get_container_client(self.container_name)

        return self.container
    

    def get_item(self, user:User, id, partition_key=None):
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
            get_spaces_query = DB_QUERY.GET_SPACE_BY_SPACE_ID.format(
                container_name = COSMOSDB_CONTAINER,
                space_id_field = 'spaceId',
                space_id = partition_key)
            # if AUTH.SUPER_ADMIN_ROLE in user.roles:
            #     get_spaces_query = DB_QUERY.GET_SPACE_BY_SPACE_ID.format(
            #     container_name = COSMOSDB_CONTAINER,
            #     space_id_field = 'spaceId',
            #     space_id = partition_key)
            # else:
            #     # Prepare DB query
            #     users_and_groups = [user.email] + user.groups
            #     get_spaces_query = DB_QUERY.SPACE_FOR_USER_QUERY.format(
            #         container_name = COSMOSDB_CONTAINER,
            #         assigned_users_field = 'assignedUsers',
            #         # users_and_groups = users_and_groups,
            #         users_and_groups = user.email,
            #         space_id_field = 'spaceId',
            #         space_id = partition_key
            #     )
            # # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))
            # For the combination of space ID and User we get a single space
            item = items[0]
            
        except CosmosResourceNotFoundError:
            raise ValueError('Space item not found.')

        return item
    
    def check_duplicate_spaceinstance(self, space_instance_name,spaceId,user):
        try:
            # Prepare DB query
            get_spaces_query = DB_QUERY.CHECK_DUPLICATE_INSTANCE_QUERY.format(
                container_name = COSMOSDB_CONTAINER,
                assigned_users_field = 'assignedUsers',
                users_and_groups = user.email,
                space_instance_name_field = 'instanceName',
                space_instance_name = space_instance_name,
                space_id_field = 'spaceId',
                space_id = spaceId
            )
            # Get the space by hitting CosmosDB
            items = items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))


        except CosmosHttpResponseError as error:
            raise RuntimeError('Failed to fetch duplicate spaceInstance: {}'.format(error))
        
        return items
    
    def check_update_duplicate_spaceinstance(self, space_instance_name,space_instance_id,user):
        try:
            # Prepare DB query
            get_spaces_query = DB_QUERY.CHECK_UPDATE_DUPLICATE_INSTANCE_QUERY.format(
                container_name = COSMOSDB_CONTAINER,
                assigned_users_field = 'assignedUsers',
                users_and_groups = user.email,
                space_instance_name_field = 'instanceName',
                space_instance_name = space_instance_name,
                space_instance_id_field = 'instanceId',
                instance_id = space_instance_id
            )
            # Get the space by hitting CosmosDB
            items = items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))


        except CosmosHttpResponseError as error:
            raise RuntimeError('Failed to fetch duplicate spaceInstance: {}'.format(error))
        
        return items

    

    def check_duplicate_space(self, space_name):
        try:
            # Prepare DB query
            get_spaces_query = DB_QUERY.CHECK_DUPLICATE_SPACE_QUERY.format(
                container_name = COSMOSDB_CONTAINER,
                space_name_field = 'spaceName',
                space_name = space_name
            )
            # Get the space by hitting CosmosDB
            items = items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))


        except CosmosHttpResponseError as error:
            raise RuntimeError('Failed to fetch check duplicate space: {}'.format(error))
        
        return items


    def check_duplicate_space_update(self,space_id, space_name):
        try:
            # Prepare DB query
            get_spaces_query = DB_QUERY.CHECK_DUPLICATE_SPACE_UPDATE_QUERY.format(
                container_name = COSMOSDB_CONTAINER,
                space_name_field = 'spaceName',
                space_name = space_name,
                space_id_field = 'spaceId',
                space_id=space_id,
            )
            # Get the space by hitting CosmosDB
            items = items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))


        except CosmosHttpResponseError as error:
            raise RuntimeError('Failed to fetch check duplicate space: {}'.format(error))
        
        return items




    def get_all_items(self, user:User, item_name = 'Space'):
        '''
        This method fetches the list of spaces in the container.
        
        Inputs
            item_name(str) : Type of container (for e.g.: space, user, doc, etc.)

        Output
            items (list(JSON)): returns the list of space JSON objects in the container.
            
        '''
        try:
            get_spaces_query = DB_QUERY.GET_ALL_SPACES.format(
                    container_name = COSMOSDB_CONTAINER
                )
            
            # # Prepare DB query
            # if AUTH.SUPER_ADMIN_ROLE in user.roles:
            #     get_spaces_query = DB_QUERY.GET_ALL_SPACES.format(
            #         container_name = COSMOSDB_CONTAINER
            #     )
            # else :
            #     # Get user and user groups
            #     users_and_groups = [user.email] + user.groups
            #     get_spaces_query = DB_QUERY.ALL_SPACES_FOR_USER_QUERY.format(
            #         container_name = COSMOSDB_CONTAINER,
            #         assigned_users_field = 'assignedUsers',
            #         # users_and_groups = users_and_groups,
            #         users_and_groups = user.email,
            #     )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            raise RuntimeError('Failed to fetch all items: {}'.format(error))

        return items

    def update_item(self, item_id, new_item:dict, item_name = 'Space'):
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
            raise ValueError('Space not found in update item.')

        return updated_item

    def delete_item(self, item_id, partition_key=None, item_name = 'Space'):
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
            # Get item
            item = self.container.read_item(item_id, partition_key = partition_key)
            # Delete item
            self.container.delete_item(item, item_id)
            # Compose success message
            message = '{} #{} deleted.'.format(item_name, item_id)
        except CosmosResourceNotFoundError:
            raise ValueError('{} space item not found.'.format(item_name))
        return message
    
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
    
    def get_item_by_id(self, id, partition_key=None, item_name = 'space'):
        try:
            self.logger.log('CosmosDB - Get item by ID')
            item = self.container.read_item(id, partition_key = partition_key)
        except CosmosResourceNotFoundError:
            error_msg = '{} Item not found.'.format(item_name)
            self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)

        return item
    
    def get_space_prompt_list(self, spaceId, partition_key=None, item_name = 'prompt'):
        try:
            prompt_list = {}
            #self.logger.log('CosmosDB - Get item by ID')
            #promptList = self.container.read_item(id, partition_key = 'spaceId')
            DB_QUERY = {
                'SPACE_FOR_USER_QUERY': """
                    SELECT VALUE c
                    FROM c 
                    WHERE c.{space_id_field} = @spaceId 
                    AND c.optimumFlag = true
                """
            }

            # Format the query string with dynamic values
            get_spaces_query = DB_QUERY['SPACE_FOR_USER_QUERY'].format(
                space_id_field='spaceId'
            )

            # Define query parameters
            parameters = [
                {"name": "@spaceId", "value": spaceId}
            ]

            # Execute the query and retrieve results
            items = list(self.container.query_items(
                query=get_spaces_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # Print the 'prompts' fields from each document
            if items:
                prompt_list = items[0]

        except CosmosResourceNotFoundError:
            error_msg = '{} prompt list not found.'.format(item_name)
            #self.logger.log(error_msg, 'ERROR')
            raise ValueError(error_msg)
        
        return prompt_list
    
    def get_item_instance(self, user:User,container_name, partition_key ):
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
            # Prepare DB query
            users_and_groups = [user.email] + user.groups
            get_spaces_query = DB_QUERY.SPACE_FOR_USER_QUERY.format(
                container_name = container_name,
                assigned_users_field = 'assignedUsers',
                users_and_groups = user.email,
                space_id_field = 'spaceId',
                space_id = partition_key
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))
            # For the combination of space ID and User we get a single space
            if not items:
            # List is empty, handle accordingly
                print(f'Space Instance not found for space id : {partition_key}')
                return []

            #item = items[0]
            item = items
            
        except CosmosResourceNotFoundError:
            raise ValueError('Space Instance not found for Sapce ID.')

        return item
    
    def get_item_by_instance_id(self, user:User,container_name, partition_key ):
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
            # Prepare DB query
            users_and_groups = [user.email] + user.groups
            get_spaces_query = DB_QUERY.SPACE_FOR_USER_QUERY.format(
                container_name = container_name,
                assigned_users_field = 'assignedUsers',
                users_and_groups = user.email,
                space_id_field = 'instanceId',
                space_id = partition_key
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))
            
            if not items:
            # List is empty, handle accordingly
                print(f'Space Instance not found for instance id : {partition_key}')
                return []

            item = items[0]
            
        except CosmosResourceNotFoundError:
            raise ValueError('Space Instance not found for Instance ID.')

        return item
    
    def get_variable_set_by_space_id(self,container_name, space_id ):
        try:
            get_spaces_query = DB_QUERY.GET_VARIABLE_SET_QUERY.format(
                container_name = container_name,
                space_id_field = 'spaceId',
                space_id = space_id,
                is_instance_variableSet_field = 'isInstanceVariableSet'
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = get_spaces_query, enable_cross_partition_query = True))
            
            if not items:
            # List is empty, handle accordingly
                print(f'Variable set not found for space id : {space_id}')
                return []

            item = items[0]
            
        except CosmosResourceNotFoundError:
            raise ValueError('Variable set not found')

        return item
    
    def update_item_instance(self, item_id, new_item:dict):
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
            try:
                # Check if `instanceExpiry` is not None before converting
                if new_item.get('instanceExpiry') is not None:
                    new_item['instanceExpiry'] = new_item['instanceExpiry'].isoformat()
                current_item = self.container.read_item(item_id, partition_key=item_id)
                # Update the item with new space data
                updated_item = {**current_item, **new_item}
                # Replace item
                self.container.replace_item(current_item, updated_item)
            except CosmosResourceNotFoundError:
                print('Space Instance not found for instanceId {item_id}')
                return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="instanceId is not valid")
        except CosmosResourceNotFoundError:
            raise ValueError('Space Instance not Updated due to exception')

        return updated_item
    
    def get_container_space_instance(self, container_name = 'spaceInstance'):
        '''
        This method creates the instance of a CosmosDB container and returns it.
        
        Inputs
            container_name (str): Name of the container.

        Output
            container (object): returns a Azure CosmosDB container object.
            
        '''
        # Define Database
        self.cosmosdb_database = self.cosmosdb_client.get_database_client(settings.COSMOSDB_DATABASE)
        # Get container 
        self.container = self.cosmosdb_database.get_container_client(container_name)

        return self.container
    
    def get_container_space_instance_prompt(self, container_name = 'prompt'):
        '''
        This method creates the instance of a CosmosDB container and returns it.
        
        Inputs
            container_name (str): Name of the container.

        Output
            container (object): returns a Azure CosmosDB container object.
            
        '''
        # Define Database
        self.cosmosdb_database = self.cosmosdb_client.get_database_client(settings.COSMOSDB_DATABASE)
        # Get container 
        self.container = self.cosmosdb_database.get_container_client(container_name)

        return self.container
    
    def delete_item_instance(self, item_id, partition_key=None, item_name = 'spaceInstance'):
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
            try:
            # Get item
                item = self.container.read_item(item_id, partition_key = partition_key)
                # Delete item
                self.container.delete_item(item, item_id)
                # Compose success message
                message = '{} #{} deleted.'.format(item_name, item_id)
            except CosmosResourceNotFoundError:
                print('instanceId not found for deletion ',item_id)
                return []
        except CosmosResourceNotFoundError:
            raise ValueError('{} delete instance item not found.'.format(item_name))
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
    
    def get_all_items_with_filter(self, space_id):
        try:
            # items = list(self.container.read_all_items())
            # Prepare DB query
            all_items_with_filter_query = DB_QUERY.ALL_ITEMS_WITH_FILTER_BY_RESPONSE_TEMPLATE.format(
                container_name = self.container_name,
                space_id_field = 'spaceId',
                space_id = space_id,
                is_response_template = 'isResponseTemplate'
            )
            # Get the space by hitting CosmosDB
            items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
        except CosmosHttpResponseError as error:
            error_msg = 'Failed to fetch the spaceId items: {}'.format(error)
            raise RuntimeError(error_msg)
            

        return items

    def get_all_default_items_with_filter(self, space_id):
            try:
                # items = list(self.container.read_all_items())
                # Prepare DB query
                all_items_with_filter_query = DB_QUERY.ALL_ITEMS_WITH_FILTER_BY_DEFAULT_TEMPLATE.format(
                    container_name = self.container_name,
                    space_id_field = 'spaceId',
                    space_id = space_id,
                    is_default_response_template = 'isDefaultResponseTemplate'
                )
                # Get the space by hitting CosmosDB
                items = list(self.container.query_items(query = all_items_with_filter_query, enable_cross_partition_query = True))
            except CosmosHttpResponseError as error:
                error_msg = 'Failed to fetch the default items items: {}'.format(error)
                raise RuntimeError(error_msg)
            return items


    