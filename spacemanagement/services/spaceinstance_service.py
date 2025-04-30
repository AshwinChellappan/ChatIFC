from core.config import settings
from models.space_instance import SpaceInstance
from services.space_service import SpaceService
from services.azure_cosmosdb_service import CosmosService
from datetime import datetime, timedelta, date
import uuid
from util.constants import TIME
from util.logger import Logger

logger = Logger()

class SpaceinstanceService():

    def __init__(self):
        self.cosmosdb_service = None
        self.container_name = 'spaceInstance'

    def establish_cosmosdb_connection(self, container_name = 'spaceInstance'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService()
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container_space_instance(container_name = container_name)

    def establish_cosmosdb_prompt_connection(self, container_name = 'prompt'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService()
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container_space_instance_prompt(container_name = container_name)


    def get_space_instance(self, space_id, user):
        # Hit cosmos db and get space
        self.establish_cosmosdb_connection()
        space = self.cosmosdb_service.get_item_instance(user, container_name = self.container_name, partition_key = space_id)
        #
        return space
    
    def get_space_by_instance_id(self, instance_id, user):
        # Hit cosmos db and get space
        self.establish_cosmosdb_connection()
        space = self.cosmosdb_service.get_item_by_instance_id(user, container_name = self.container_name, partition_key = instance_id)
        if not space:
            return None
        return space
    
    def get_instance_expiry_by_instance_id(self, instance_id, user):
        # Hit cosmos db and get space
        self.establish_cosmosdb_connection()
        space = self.cosmosdb_service.get_item_by_instance_id(user, container_name = self.container_name, partition_key = instance_id)
        current_date = date.today()  # Get today's date
        if not space:
            return None
        instanceExpiry=(datetime.fromisoformat(space['instanceExpiry']).date()-current_date).days
        return instanceExpiry
    
    def create_space_instance(self,space_instance, user):
        # convert pydantic object to a dictionary
        space_instance = dict(space_instance)
        # Create unique space ID
        space_instance_id = str(uuid.uuid4())
        # Update space ids
        space_instance['id'] = space_instance_id
        space_instance['instanceId'] = space_instance_id
        space_instance['assignedUsers'] = [user.email]
        space_instance['assignedUserDetails'] = [
            {
                'name': user.name,
                'email': user.email,
                'userType': 'admin' 
            }
        ]
        current_date = date.today()  # Get today's date
        space_instance['instanceExpiry'] = (current_date + timedelta(days=TIME.INSTANCE_EXPIRY)).isoformat()  # Add 15 days
        # #Getting prompt list
        # promptList=self.get_space_prompt_list(space_instance['spaceId'])
        # space_instance['promptList'] = promptList
        #
        self.update_space_instance_history(space_instance, user)

        self.establish_cosmosdb_connection(container_name = 'spaceInstance')
        check_duplicate = self.cosmosdb_service.check_duplicate_spaceinstance(space_instance['instanceName'],space_instance['spaceId'],user)

        if not check_duplicate:
            self.cosmosdb_container.upsert_item(space_instance)
            # Establish cosmosDB connection
            self.establish_cosmosdb_connection()
            # Upsert new space item
            self.cosmosdb_container.upsert_item(space_instance)
            # Create prompt list 
            self.create_instance_prompt_list(space_instance['spaceId'], space_instance_id)
            # Create variable set
            self.create_instance_variable_set(space_instance['spaceId'],space_instance_id,user)

        
        return space_instance,check_duplicate

    def update_space_instance_history(self, space_instance, user, clone=False):

        space_instance['lastUpdatedBy'] = user.email
        space_instance['lastUpdatedOn'] = datetime.now().isoformat()
        space_instance['responseGeneratedOn'] = datetime.now().isoformat()
        # update created by, on
        if space_instance['createdBy'] == "" or space_instance['createdOn'] is None or clone:
            space_instance['createdOn'] = datetime.now().isoformat()
            space_instance['createdBy'] = user.email
        elif not isinstance(space_instance['createdOn'], str):
            space_instance['createdOn'] = space_instance['createdOn'].isoformat() 

        return space_instance
    
    def update_space_instance(self, space_id, new_space, user):
        # Update user details
        user_details = [dict(user_detail) for user_detail in new_space.assignedUserDetails]
        new_space.assignedUserDetails = user_details
        # convert pydantic object to a dictionary
        new_space = dict(new_space)
        # Update history
        updated_space=[]
        self.establish_cosmosdb_connection(container_name = 'spaceInstance')
        check_duplicate = self.cosmosdb_service.check_update_duplicate_spaceinstance(new_space['instanceName'],new_space['instanceId'],user)
        if not check_duplicate:
            new_space = self.update_space_history(new_space, user)
            # Establish cosmosDB connection
            self.establish_cosmosdb_connection()
            # Update space
            updated_space = self.cosmosdb_service.update_item_instance(space_id, new_space)

        return updated_space,check_duplicate

    def update_space_history(self, space, user, clone=False):

        space['lastUpdatedBy'] = user.email
        space['lastUpdatedOn'] = datetime.now().isoformat()
        space['assignedUsers'] = [user.email]
        space['assignedUserDetails'] = [
            {
                'name': user.name,
                'email': user.email,
                'userType': 'admin' 
            }
        ]
        del space['ingestionProgress']
        del space['responseProgress']
        space = self.remove_empty_fields(space)
        return space
    
    def remove_empty_fields(self,details):
    # Create a new dictionary with only the non-empty fields, but always include 'description'
        return {key: value for key, value in details.items() if value not in ("", [], None) or key == "description"}

    def delete_space_instance(self, space_id):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Delete space
        delete_space = self.cosmosdb_service.delete_item_instance(space_id, partition_key = space_id)
        return delete_space

    def get_space_prompt_list(self, space_id):
        self.establish_cosmosdb_prompt_connection()
        prompt_list = self.cosmosdb_service.get_space_prompt_list(space_id)
        return prompt_list
    
    def get_space_variable_set(self, space_id):
        self.establish_cosmosdb_prompt_connection(container_name = 'variableSet')
        variable_set = self.cosmosdb_service.get_variable_set_by_space_id('variableSet', space_id)
        return variable_set
    
    def get_all_spaces_instance(self, user):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Get the space item
        space_list = self.cosmosdb_service.get_all_items(user)
        return space_list

    def get_spaceinstance_status_count(self, user):
        # Hit cosmos db and get space
        # Establish connection to Cosmos DB
        self.establish_cosmosdb_connection() 
        # Fetch published spaces
        space_service_instance = SpaceService()
        getPublishedSpaces = space_service_instance.get_published_spaces()
        # Dictionary to aggregate instance statuses
        space_instance_counts = {}
        if getPublishedSpaces:
            for publishedSpace in getPublishedSpaces:
                current_space_id = publishedSpace['spaceId']
                # Fetch the instance data for each published space
                space_data = self.cosmosdb_service.get_item_instance(user, container_name=self.container_name, partition_key=current_space_id)
                instance_statuses = self.get_instance_status(space_data, current_space_id)
                
                # Update the dictionary with aggregated results
                if instance_statuses:
                    result = instance_statuses[0]  # Get the first item (since it's a list with one dictionary)
                    space_instance_counts[current_space_id] = result
        
        # Convert the dictionary values to a list
        response = list(space_instance_counts.values())
        return response

    
    def get_instance_status(self,instance,space_id):
    # Return an empty list if instance is None or not a list
        if not instance or not isinstance(instance, list):
            return []
        current_date = datetime.now()
        num_active_instances = 0
        num_expired_instances = 0
        for item in instance:
            # Check if 'instanceExpiry' key exists
            if 'instanceExpiry' in item:
                try:
                    expiry_date = datetime.strptime(item["instanceExpiry"], "%Y-%m-%d")
                    # Determine if instance is active or expired
                    if expiry_date >= current_date:
                        num_active_instances += 1
                    else:
                        num_expired_instances += 1
                except ValueError:
                    # Handle incorrect date format
                    logger.log(f"Warning: Date format issue for instance with spaceId {space_id}")
            else:
                # Handle missing 'instanceExpiry' key
                logger.log(f"Warning: 'instanceExpiry' key missing for instance with spaceId {space_id}")
        
        # Return the aggregated result in the expected format
        return [{
            "spaceId": space_id,
            "numActiveInstances": num_active_instances,
            "numExpiredInstances": num_expired_instances
        }]

    def create_instance_prompt_list(self, space_id, instance_id):
        # Get optimal prompt list from db
        # # Establish cosmos db connection
        self.establish_cosmosdb_connection(container_name = 'prompt')
        prompt_list = self.get_space_prompt_list(space_id)
        # Change ids and flags in prompt list
        new_prompt_list_id = str(uuid.uuid4())
        # Update values in the prompt list object
        prompt_list['id'] = new_prompt_list_id
        prompt_list['promptListId'] = new_prompt_list_id
        # Update prompt ids in every prompt
        for prompt in prompt_list['prompts']:
            new_prompt_id = str(uuid.uuid4())
            prompt['id'] = new_prompt_list_id
            prompt['response'] = ''
            prompt['responsePrefix'] = ''
        # Update instance variables
        prompt_list['optimumFlag'] = False
        prompt_list['isInstanceList'] = True
        prompt_list['instanceId'] = instance_id
        # upsert new prompt list
        self.cosmosdb_container.upsert_item(prompt_list)

    def create_instance_variable_set(self, space_id, instance_id,user):
        # # Establish cosmos db connection
        self.establish_cosmosdb_connection(container_name = 'variableSet')
        new_variable_set = self.get_space_variable_set(space_id)
        if new_variable_set:
            new_variable_set_id = str(uuid.uuid4())
            new_variable_set['id'] = new_variable_set_id
            new_variable_set['variableSetId'] = new_variable_set_id
            new_variable_set['isInstanceVariableSet'] = True
            new_variable_set['instanceId'] = instance_id
            new_variable_set['createdBy'] = user.email
            new_variable_set['variables'] = list(map(lambda var: {**var, 'value': ''}, new_variable_set['variables']))
            # upsert new prompt list
            self.cosmosdb_container.upsert_item(new_variable_set)


